#coding: utf-8
from nodewox.thing import NX_PREFIX
from node import Node, U8
from messenger import Messenger
from channel import Channel
import signal
import json
import types
import os
import re
from M2Crypto import SSL, RSA, X509, m2, httpslib
import urlparse

PAT_REQ   = re.compile(r"^{}(\d+)\/q$".format(NX_PREFIX.replace("/", r"\/")))
PAT_EVENT = re.compile(r"^{}(\d+)$".format(NX_PREFIX.replace("/", r"\/")))

class Thing(Node):
    # thing prop decl.
    NAME = ""
    PID = None
    CHKEYS = "*"

    # messenger class decl.
    MESSENGER_CLASS = Messenger

    def __init__(self, key, secret="", reconnect=1000):
        assert isinstance(key, basestring) and key!="" and "/" not in key, key
        assert issubclass(self.MESSENGER_CLASS, Messenger), self.MESSENGER_CLASS

        self._key = key
        self._secret = secret
        self._rest_url = ""
        self._rest_ca = ""

        self._reconnect = reconnect
        
        self._cafile = None
        self._certfile = None
        self._keyfile = None

        self._username = key
        self._secret = secret

        # runtime
        self._messenger = None
        self._running = False

        Node.__init__(self, self._key, name=self.NAME)


    @property
    def is_registered(self):
        return self._certfile!="" and self._rest_url!=""

    def set_rest(self, url, ca=""):
        self._rest_url = url
        self._rest_ca = ca

    def set_user_pw(self, username, password):
        self._username = username
        self._secret = password

    def set_tls(self, cafile, certfile, keyfile):
        self._cafile = cafile
        self._certfile = certfile
        self._keyfile = keyfile

    def get_messenger(self):
        if self._messenger==None:
            assert self._host!=""
            args = {
                    "host": self._host,
                    "port": self._port,
                    "unpw": (self._username, self._secret),
                    "cafile": self._cafile,
                    "certfile": self._certfile,
                    "keyfile": self._keyfile,
                    "reconnect": self._reconnect,
            }
            self._messenger = self.MESSENGER_CLASS(self, **args)
        assert isinstance(self._messenger, Messenger), self._messenger
        return self._messenger


    def add_child(self, ch):
        assert isinstance(ch, Channel), ch
        return Node.add_child(self, ch)


    def as_data(self):
        res = Node.as_data(self)
        if self.PID==None:
            # user defined
            assert len(self.children)>0
        else:
            # instantiate from product
            assert type(self.PID)==types.IntType, self.PID
            res['product'] = self.PID

        res['children'] = dict((x.key,x.as_data()) for x in self.children.values())
        return res


    def _make_ssl_context(self):
        return SSL.Context()

    def load_remote_profile(self):
        "从主机获取节点配置"
        assert self._rest_url!=""
        assert self.is_registered

        headers = {
            "authorization": "CERT %s" % self._secret,
            "x-requested-with": "XMLHttpRequest",
        }

        sctx = self._make_ssl_context()
        if self._certfile not in (None, ""):
            cert = X509.load_cert_string(self._certfile)
            key = RSA.load_key_string(self._keyfile)
            m2.ssl_ctx_use_x509(sctx.ctx, cert.x509)
            m2.ssl_ctx_use_rsa_privkey(sctx.ctx, key.rsa)

        u = urlparse.urlparse(os.path.join(self._rest_url, "thing/profile"))
        conn = httpslib.HTTPSConnection(u.netloc, ssl_context=sctx)
        conn.request("GET", u.path, headers=headers)

        res = conn.getresponse()
        status = res.status
        content = res.read()

        if status != 200:
            return status, content

        try:
            d = U8(json.loads(content))
            if d['status'] != 0:
                return d['status'], d['response']

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

            # setup children
            for k, chinfo in resp["children"].items():
                print(k, chinfo['id'])

                if k in self.children:
                    ch = self.children[k]
                    assert ch._gender==chinfo['gender']

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

            return 0, resp

        except:
            import traceback
            print("*" * 20)
            traceback.print_exc()
            print("*" * 20)
            return -1, "ERROR"


    def register(self, user, passwd):
        "register the thing to nodewox host"
        assert self._secret not in (None, "")
        assert self._rest_url!=""

        # make thing meta
        info = self.as_data()
        info['secret'] = self._secret

        headers = {
                "authorization": "USERPW %s\t%s" % (user, passwd),
                "x-requested-with": "XMLHttpRequest",
                "content-type": "application/json",
        }
        u = urlparse.urlparse(os.path.join(self._rest_url, "thing/register?trust=pem&cert=pem"))
        conn = httpslib.HTTPSConnection(u.netloc, ssl_context=self._make_ssl_context())
        conn.request("POST", "{}?{}".format(u.path, u.query), body=U8(json.dumps(info)), headers=headers)

        res = conn.getresponse()
        status = res.status
        content = res.read()
        return status, content


    def handle_request(self, action="", params={}, children=[]):
        if action=="unregister":
            self.on_unregister()
        else:
            return super(Thing, self).handle_request(action=action, params=params, children=children)

    def on_unregister(self):
        self.stop()

    def on_connected(self, userdata):
        # listen on topics
        res = {}
        mess = self.get_messenger()

        subs = ["{}{}/q".format(NX_PREFIX, self._id)]
        for ch in self.children.values():
            assert type(ch._id)==types.IntType and ch._id>0, (ch.key, ch._id)
            subs.append("{}{}/q".format(NX_PREFIX, ch._id))
            if ch._gender=="F":
                subs.append("{}{}".format(NX_PREFIX, ch._id))

            # say hello from channel ch
            res2 = ch.handle_request(action="status")
            if res2!=None:
                res.update(res2)

        if len(self._params)>0:
            # say hello from this thing
            res2 = self.handle_request(action="status")
            if res2!=None:
                res.update(res2)

        # sub & pub
        mess.subscribe(subs)
        for topic, msg in res.items():
            assert isinstance(msg, dict), msg
            if len(msg)>0:
                payload = bytearray(json.dumps(msg))
            else:
                payload = ""
            mess.publish(topic, payload, qos=0)


    def on_connect_fail(self, code, userdata):
        pass

    def on_disconnected(self, code, userdata):
        pass

    def on_message(self, msg, userdata):
        pass

    def on_sig(self, *args):
        print("SIG", args[0])
        self._running = False


    def loop(self):
        # tick each channel
        for ch in self.children.values():
            if ch.is_awake:
                ch.loop()


    def start(self):
        assert self.is_registered
        assert not self._running

        signal.signal(signal.SIGINT, self.on_sig)
        signal.signal(signal.SIGTERM, self.on_sig)

        # main loop
        mess = self.get_messenger()
        self._running = True

        while self._running:
            self.loop() # drive thing work
            mess.loop() # drive messenger work


    def stop(self):
        self._running = False

