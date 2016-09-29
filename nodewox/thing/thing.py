#coding: utf-8
from node import Node, U8, to_int, to_float, to_bool, to_json
from mqttclient import MqttClientMixin
from channel import Channel
import json
import types
import os
import re
import pycurl
import urlparse
import StringIO
import uuid
import sys, optparse

PAT_REQ   = re.compile(r"^\/NX\/(\d+)\/q$")
PAT_EVENT = re.compile(r"^\/NX\/(\d+)$")

class Thing(Node, MqttClientMixin):
    NAME = ""
    PID = None
    CHKEYS = "*"

    def __init__(self, profile, secret=None, **kwargs):
        profile = os.path.abspath(profile)
        assert os.path.isfile(profile), profile

        self._channels = {}
        self._running = False

        self._profile = profile
        self._rest_url = ""
        self._rest_ca = ""
        self._secret = secret

        MqttClientMixin.__init__(self)

        self.load_local_profile()
        assert self._key not in (None, "")

        Node.__init__(self, self._key, name=self.NAME)


    @property
    def is_registered(self):
        return self._key!="" and self._certfile!="" and self._rest_url!=""


    def add_channel(self, ch):
        assert isinstance(ch, Channel), ch
        assert ch._parent==self
        assert ch.key not in self._channels
        self._channels[ch.key] = ch


    def as_data(self):
        res = Node.as_data(self)
        if self.PID==None:
            # user defined
            assert len(self._channels)>0
        else:
            # instantiate from product
            assert type(self.PID)==types.IntType, self.PID
            res['product'] = self.PID

        res['channels'] = dict((x.key,x.as_data()) for x in self._channels.values())
        return res


    def load_local_profile(self):
        "读取本地配置"
        assert os.path.isfile(self._profile), self._profile

        fh = open(self._profile, "r")
        data = U8(json.load(fh))
        fh.close()

        # assert pid match
        assert self.PID == data.get("pid"), (self.PID, data.get("pid"))

        self._key = data['key']
        assert self._key!=""

        self._rest_url = data['rest_url']
        assert self._rest_url.startswith("https://")

        path = os.path.dirname(self._profile)

        f = data.get("rest_ca", "")
        if f!="":
            self._rest_ca = os.path.join(path, f)

        # thing trust
        f = "/var/lib/nodewox/trust/thing_%s.pem" % os.path.basename(self._profile)
        if os.path.isfile(f):
            self._cafile = f

        # thing cert
        f = data.get("cert", "")
        if f!="":
            self._certfile = os.path.join(path, f)
            assert os.path.isfile(self._certfile), self._certfile
            self._keyfile = self._certfile

        if self._secret==None:
            self._secret = data.get("secret")

        self._username = self._key
        self._password = self._secret


    def _setup_curl(self, url, headers={}, debug=False):
        c = pycurl.Curl()
        b = StringIO.StringIO()

        # fix curl resolve dns slow problem
        c.setopt(pycurl.IPRESOLVE, pycurl.IPRESOLVE_V4)

        c.setopt(pycurl.CONNECTTIMEOUT, 30)
        c.setopt(pycurl.TIMEOUT, 60)
        c.setopt(pycurl.USERAGENT, "nodewox/thing")

        # headers
        if len(headers)>0:
            assert type(headers)==types.DictType, headers
            c.setopt(pycurl.HTTPHEADER, ["%s: %s" % (k,v) for k,v in headers.items()])

        c.setopt(pycurl.URL, url)
        c.setopt(pycurl.WRITEFUNCTION, b.write)
        c.setopt(pycurl.FOLLOWLOCATION, 1)
        c.setopt(pycurl.MAXREDIRS, 3)

        c.setopt(pycurl.SSL_VERIFYPEER, 2)
        c.setopt(pycurl.SSL_VERIFYHOST, 2)

        # setup ca
        if os.path.isfile(self._rest_ca):
            c.setopt(pycurl.CAINFO, self._rest_ca)
        elif os.path.isdir(self._rest_ca):
            c.setopt(pycurl.CAPATH, self._rest_ca)
        else:
            c.setopt(pycurl.CAINFO, "/var/lib/nodewox/trust/default.pem")

        if debug:
            c.setopt(pycurl.VERBOSE, 1)

        return (c, b)


    def load_remote_profile(self):
        "从主机获取节点配置"
        assert self.is_registered

        headers = {
            "authorization": "CERT %s" % self._secret,
            "x-requested-with": "XMLHttpRequest",
        }
        c, b = self._setup_curl(os.path.join(self._rest_url, "thing/profile"), headers=headers)

        # client cert
        c.setopt(pycurl.SSLCERT, self._certfile)
        c.setopt(pycurl.SSLKEY, self._keyfile)

        c.perform()
        status = c.getinfo(pycurl.HTTP_CODE)
        content = b.getvalue()

        if status!=200:
            # not ok
            if status in (403, 404):
                # remove register info, if remote profile not exists
                print("remove register info")
                self.clear_registry()
            else:
                print(status, content)
            return False

        try:
            d = json.loads(content)
            if d['status']<0:
                print(d['status'], d['response'])
                return False

            resp = U8(d['response'])

            # thing id
            self._id = resp['id']
            assert type(self._id)==types.IntType, self._id
            
            # mqtt config
            p = urlparse.urlsplit(resp['mqtt'])
            a = p.netloc.split(":")
            if len(a)>1:
                host = a[0]
                port = int(a[1])
            else:
                host = a[0]
                if p.scheme in ("mqtts", "ssl"):
                    port = 8883
                else:
                    port = 1883
            self._host = host
            self._port = port

            # setup channels
            for k, chinfo in resp["channels"].items():
                print(k, chinfo['id'])

                if k in self._channels:
                    ch = self._channels[k]
                    assert ch._flow==chinfo['flow']

                    ch._id = chinfo['id']
                    assert type(ch._id)==types.IntType, ch._id

                    for field in ("datatype", "exclusive", "latch"):
                        if field in chinfo:
                            setattr(ch, "_%s" % field, chinfo[field])

                    # setup params
                    params = chinfo.get("params")
                    if params!=None:
                        pvs = {}
                        for pkey, pinfo in params.items():
                            if not ch.has_param(pkey):
                                ch.add_param(pkey, **pinfo)

                            if pinfo.get("value")!=None:
                                pvs[pkey] = pinfo['value']

                        ch.reset_params()
                        if len(pvs)>0:
                            ch.set_params(pvs)

            return True

        except:
            import traceback
            print("*" * 20)
            traceback.print_exc()
            print("*" * 20)
            return False


    def register(self, user, passwd):
        "register the thing to nodewox host"
        assert self._secret != None

        # make thing meta
        info = self.as_data()
        info['secret'] = self._secret

        headers = {
                "authorization": "USERPW %s\t%s" % (user, passwd),
                "x-requested-with": "XMLHttpRequest",
                "content-type": "application/json",
        }
        c, b = self._setup_curl(os.path.join(self._rest_url, "thing/register?trust=pem&cert=pem"), headers=headers)

        c.setopt(pycurl.POST, 1)
        c.setopt(pycurl.POSTFIELDS, U8(json.dumps(info)))

        c.perform()
        status = c.getinfo(pycurl.HTTP_CODE)
        content = b.getvalue()

        if status!=200:
            print("register fail (status=%d)" % status)
            return False

        try:
            d = U8(json.loads(content))
            if d['status']<0:
                print(d['response'])
                return False
            else:
                ack = d['response']
        except:
            return False

        # update local profile
        cfg = {
                "key": self._key,
                "rest_url": self._rest_url,
                "secret": self._secret,
        }
        if self._rest_ca!="":
            cfg['rest_ca'] = self._rest_ca
        path = os.path.dirname(self._profile)

        os.umask(0o177)

        if "cert" in ack:
            # save mqtt client cert
            fname = "%s.pem" % os.path.basename(self._profile)
            cfg['cert'] = fname
            self._certfile = self._keyfile = os.path.join(path, fname)

            fh = open(self._certfile, "w")
            fh.write(ack['cert'])
            fh.close()

        if "trust" in ack:
            # save mqtt ca
            fname = os.path.join("/var/lib/nodewox/trust/", "thing_%s.pem" % os.path.basename(self._profile))
            fh = open(fname, "w")
            fh.write(ack['trust'])
            fh.close()

            # c_rehash for new ca
            # TODO...

        fh = open(self._profile, "w")
        json.dump(cfg, fh, ensure_ascii=False, indent=4)
        fh.close()

        self.load_local_profile()
        return True


    def clear_registry(self):
        if self.is_registered:
            # drop thing cert
            os.remove(self._certfile)

            # drop thing ca
            f = "/var/lib/nodewox/trust/thing_%s.pem" % os.path.base(self._profile)
            if os.path.isfile(f):
                os.remove(f)

            # reset profile
            cfg = {
                "key": self._key,
                "rest_url": self._rest_url,
                "secret": self._secret,
            }
            if self._rest_ca!="":
                cfg['rest_ca'] = self._rest_ca

            os.umask(0o177)
            fh = open(self._profile, "w")
            json.dump(cfg, fh, ensure_ascii=False, indent=4)
            fh.close()

            self._certfile = self._keyfile = ""


    def ack_req(self, client, userdata, msg):
        content = None
        from_ = -1
        if len(msg.payload)>0:
            try:
                content = json.loads(msg.payload)
                assert type(content)==types.DictType
                from_ = content.get("from", -1)
            except:
                # bad request body
                return

        _id = int(PAT_REQ.findall(msg.topic)[0])
        if _id==self._id:
            reply = self.request(content, from_)
        else:
            lst = [x for x in self._channels.values() if x._id==_id]
            if len(lst)>0:
                ch = lst[0]
                reply = ch.request(content, from_)
            else:
                reply = None

        if reply!=None:
            client.publish("/NX/%d/r" % _id, json.dumps(reply))


    def ack_event(self, client, userdata, msg):
        _id = int(PAT_EVENT.findall(msg.topic)[0])
        if _id==self._id:
            act = self
        else:
            lst = [x for x in self._channels.values() if x._id==_id]
            if len(lst)>0:
                act = lst[0]
            else:
                act = None

        if act!=None:
            if act._datatype=="int":
                val = to_int(msg.payload)
            elif act._datatype=="float":
                val = to_float(msg.payload)
            elif act._datatype=="bool":
                val = to_bool(msg.payload)
            elif act._datatype=="json":
                if len(msg.payload)==0:
                    val = None
                else:
                    val = to_json(msg.payload)
            else:
                val = msg.payload

            if val!=None:
                reply = act.process(val)
                if reply!=None:
                    client.publish("/NX/%d/r" % _id, json.dumps(reply))


    def publish(self, topic, payload="", qos=0):
        if self._client:
            self._client.publish(topic, payload=payload, qos=qos)

    def subscribe(self, topic):
        if self._client:
            if type(topic)==types.StringType:
                topic = [topic]
            else:
                assert type(topic) in (types.ListType, types.Tuple)
                assert len(topic)>0
            self._client.subscribe([(x,2) for x in set(topic)])

    def unsubscribe(self, topic):
        if self._client:
            if type(topic)==types.StringType:
                topic = [topic]
            else:
                assert type(topic) in (types.ListType, types.Tuple)
                assert len(topic)>0
            self._client.unsubscribe([(x,2) for x in set(topic)])


    def _prepare_connection(self, conn):
        ids = [self._id]
        ids += [x._id for x in self._channels.values() if x._id>0]
        args = {
            "client_id": self._key,
            "will": ("/NX/%d/r" % self._id, json.dumps({"bye":ids})),
        }
        MqttClientMixin._prepare_connection(self, conn, **args)

        # topic callbacks
        conn.message_callback_add("/NX/%d/q" % self._id, self.ack_req)
        if len(self._channels)==0 and self._flow=="I":
            conn.message_callback_add("/NX/%d" % self._id, self.ack_event)

        for ch in self._channels.values():
            conn.message_callback_add("/NX/%d/q" % ch._id, self.ack_req)
            if ch._flow=="I":
                conn.message_callback_add("/NX/%d" % ch._id, self.ack_event)

        return conn


    def connect(self):
        assert self.is_registered
        assert self._id>0
        return MqttClientMixin.connect(self)


    def on_connect(self, client, userdata, flags, rc):
        MqttClientMixin.on_connect(self, client, userdata, flags, rc)
        if rc==0:
            # listen on topics
            subs = ["/NX/%d/q" % self._id]
            for ch in self._channels.values():
                assert type(ch._id)==types.IntType and ch._id>0, (ch.key, ch._id)
                subs.append("/NX/%d/q" % ch._id)
                if ch._flow=="I":
                    subs.append("/NX/%d" % ch._id)

                # say hello from channel ch
                client.publish("/NX/%d/r" % ch._id, json.dumps({"status":ch.get_status()}))

            client.publish("/NX/%d/r" % self._id, json.dumps({"status":self.get_status()}))
            client.subscribe([(x,2) for x in set(subs)])


    def tick(self):
        # tick each channel
        for ch in self._channels.values():
            ch.tick()


    def start(self):
        assert self.is_registered
        assert not self._running
        MqttClientMixin.start(self)


    @classmethod
    def create_profile(cls, name, rest_url="https://www.nodewox.org/api", rest_ca="", key="", secret=""):
        assert name!=""
        assert rest_url.startswith("https://")
        assert len(rest_url)>8, rest_url
        if rest_url.endswith("/"):
            rest_url = rest_url[:-1]

        f = os.path.abspath(name)
        assert not os.path.exists(f)

        if key=="":
            key = str(uuid.uuid1()).replace("-", "")

        if secret=="":
            secret = str(uuid.uuid1()).replace("-", "")

        d = {"key":key, "secret":secret, "rest_url":rest_url}
        if cls.PID!=None:
            d['pid'] = cls.PID

        if rest_ca!="":
            caf = os.path.abspath(rest_ca)
            assert os.path.isfile(caf)
            p = "%s/" % os.path.dirname(f)
            if caf.startswith(p):
                caf = caf[len(p):]
            d['rest_ca'] = caf

        os.umask(0o177)
        fh = open(f, "w")
        fh.write(json.dumps(d, ensure_ascii=False, indent=4))
        fh.close()

        return f
