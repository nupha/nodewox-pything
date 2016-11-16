from umqtt.robust import MQTTClient
import json
import ussl
import socket
import array
import ustruct
import time
import gc

NX_PREFIX = ""

def _encode(data, dtype, dim):
    if dtype=="":
        if isinstance(data, str):
            return bytes(data, "utf-8")
        elif isinstance(data, bytes):
            return data
        else:
            return None

    if len(data)==0:
        return b''

    assert isinstance(data, (list, tuple)), data

    if dtype=="byte":
        p = ustruct.pack("%dB" % len(data), *data)
    elif dtype=="int16":
        p = ustruct.pack("!%dh" % len(data), *data)
    elif dtype=="int32":
        p = ustruct.pack("!%di" % len(data), *data)
    elif dtype=="int64":
        p = ustruct.pack("!%dq" % len(data), *data)
    elif dtype=="float":
        p = ustruct.pack("!%df" % len(data), *data)
    elif dtype=="bool":
        p = ustruct.pack("!%db" % len(data), *data)
    elif dtype=="string":
        fmt = ""
        for s in data:
            fmt += "%ds" % (len(s)+1)
        p = ustruct.pack(fmt, *data)
    else:
        raise NotImplementedError

    return p


def _decode(buf, dtype, dim):
    if dtype=="":
        return buf

    if len(buf)==0:
        if dtype in ("uint8", "bool"):
            data = array.array('b', b'\0'*dim)
        elif dtype == "int16":
            data = array.array('h', [0]*dim)
        elif dtype == "int32":
            data = array.array('i', [0]*dim)
        elif dtype == "float":
            data = array.array('f', [0]*dim)
        elif dtype == "string":
            data = [""]
        return data

    if dtype=="string":
        data = []
        start = 0
        while start < len(buf):
            sz = buf[start:].find(0)
            assert sz>=0
            if sz==0:
                data.append("")
            else:
                data.append(struct.unpack("{}s".format(sz), buf[start:start+sz]))
            start += sz+1
    else:
        fmt = None
        t = ""
        if dtype=="int32":
            n = len(buf) / ustruct.calcsize("!i")
            fmt = "!{}i".format(n)
            t = "i"
        elif dtype=="int16":
            n = len(buf) / ustruct.calcsize("!h")
            fmt = "!{}h".format(dim)
            t = "h"
        elif dtype in ("uint8", "bool"):
            n = len(buf) / ustruct.calcsize("B")
            fmt = "{}B".format(dim)
            t = "B"
        elif dtype=="float":
            n = len(buf) / ustruct.calcsize("!f")
            fmt = "!{}f".format(dim)
            t = "f"
        try:
            data = array.array(t, ustruct.unpack(fmt, buf))
        except:
            data = None

    if isinstance(data, (list, array.array)) and dim>0 and len(data)<dim:
        # padding
        n = dim - len(data)
        if dtype in ("uint8", "bool"):
            v = 0
        elif dtype in ("int32", "int16"):
            v = 0
        elif dtype == "float":
            v = 0
        elif dtype == "string":
            v = ""
        for x in range(n):
            data.append(v)

    gc.collect()
    return data


class Param:
    def __init__(self, key, value, name="", flag="volatile", options=[], comment="", seq=0):
        assert key not in ("", "id"), key
        assert flag in ("volatile", "persistent", "readonly", "static"), flag

        # check validity of init value
        self.datatype = None
        if value in (True, False):
            self.datatype = bool
        else:
            for t in (int, float, str):
                if isinstance(value, t):
                    self.datatype = t
                    break
        if self.datatype==None:
            raise Exception("invalid init value: must be a value of int, float, bool or string type")

        self.key = key
        self.name = name
        self.flag = flag
        self.init_value = value
        self.value = value
        self.seq = seq
        self.comment = comment
        self.disabled = False

        if len(options)>0:
            # check options
            assert isinstance(options, (list,type)), options
            assert self.datatype in (int, str)
            for i, x in enumerate(options):
                if isinstance(x, (list,tuple)):
                    assert isinstance(x[0], self.datatype)
                    assert isinstance(x[1], str)
                else:
                    assert isinstance(x, str)
                    if self.datatype==int:
                        val = i
                    else:
                        val = str(i)
                    options[i] = (val, x)
        self.options = options

    def set_value(self, val):
        if self.flag in ("volatile", "persistent", "readonly"):
            if self.datatype==float and isinstance(val, int):
                val = float(val)
            elif self.datatype==int and isinstance(val, (float,bool)):
                val = int(val)
            elif self.datatype==bool and isinstance(val, (int,float)):
                val = val!=0

            if isinstance(val, self.datatype):
                self.value = val
                return True
        return False

    def reset(self):
        self.value = self.init_value

    def as_data(self):
        res = {
            "key": self.key,
            "value": self.value,
            "flag": self.flag,
            "seq": self.seq,
        }
        if self.datatype==int:
            res['datatype'] = "int"
        elif self.datatype==float:
            res['datatype'] = "float"
        elif self.datatype==str:
            res['datatype'] = "string"
        elif self.datatype==bool:
            res['datatype'] = "bool"
        else:
            raise NotImplementedError

        if self.name not in ("", self.key):
            res['name'] = self.name

        if len(self.options)>0:
            res['options'] = options

        return res


class Node:
    NAME = ""
    def __init__(self, key, name="", parent=None, comment=""):
        if name=="":
            name = self.NAME

        self._id = 0
        self._key = key
        self._name = name
        self._parent = parent
        self._params = {}
        self._seq = 0

        self.setup()

    def setup(self):
        pass

    def add_param(self, key, value, name="", comment="", options=[], flag="volatile", seq=-1):
        assert not self._params.has_key(key), key
        p = Param(key, value, name=name, options=options, comment=comment, seq=seq)
        if seq<0: p.seq = len(self._params)+1
        self._params[key] = p
        return p

    def get_params_ack(self):
        res = {}
        for p in self._params.values():
            if p.flag != "static":
                res[p.key] = p.value
        if len(res)>0:
            return res

    def on_param_changed(self, key, old_value=None):
        pass

    def as_data(self):
        res = {"key":self._key, "name":self._name, "seq":self._seq}
        if len(self._params)>0:
            res['params'] = dict((k,v.as_data()) for k,v in self._params.items())
        return res

    def publish(self, topic, data=b'', qos=0):
        raise NotImplementedError

    def request(self, action="", params={}, children=[]):
        ack_params = (action=="status")

        # set params
        for k,v in params.items():
            p = self._params.get(k)
            if p!=None:
                oval = p.value 
                if self.set_param(k, v):
                    self.on_param_changed(p, old_value=oval)
                    ack_params = True

        # resport param status
        res = {}
        if ack_params and len(self._params)>0:
            params = self.get_params_ack()
            if params:
                res['params'] = params
        if len(res)>0:
            payload = json.dumps(res)
        else:
            payload = b''
        self.publish("{}{}/r".format(NX_PREFIX, self._id), payload)

    def loop(self):
        pass


class Channel(Node):
    DATA_TYPE = ("", 0)
    def __init__(self, thing, key, gender, name="", latch=False, seq=0, exclusive=True, comment="", **kwargs):
        assert isinstance(thing, Thing), thing
        assert gender in ("F", "M"), gender

        assert self.DATA_TYPE[0] in ("int16", "int32", "int64", "byte", "float", "bool", "string", ""), self.DATA_TYPE
        assert self.DATA_TYPE[1]>=0, self.DATA_TYPE

        self._parent = thing
        self._gender = gender
        self._latch = latch
        self._exclusive = exclusive
        self._seq = seq

        if name=="": name = self.NAME
        if name=="": name = key

        Node.__init__(self, key, parent=thing, name=name, comment=comment, **kwargs)

    def publish(self, topic, data=b'', qos=0):
        self._parent._pubs.append((topic, data, qos))

    def as_data(self):
        assert self._parent!=None
        res = Node.as_data(self)
        res.update({
                "gender": self._gender,
                "latch": self._latch,
                "lang": "",
                "seq": self._seq,
        })
        if self.DATA_TYPE[0]=="":
            res['datatype'] = ("", 0)
        else:
            res['datatype'] = self.DATA_TYPE

        if self._gender=="F":
            res['exclusive'] = self._exclusive
        else:
            res['exclusive'] = False

        return res


class MaleChannel(Channel):
    def __init__(self, thing, key, **kwargs):
        Channel.__init__(self, thing, key, "M", **kwargs)

    def emit(self, data, gid=0, src=0):
        if self._id > 0:
            p = _encode(data, self.DATA_TYPE[0], self.DATA_TYPE[1])
            self.publish(bytes("{}{}".format(NX_PREFIX, self._id), "utf-8"), p)


class FemaleChannel(Channel):
    def __init__(self, thing, key, **kwargs):
        Channel.__init__(self, thing, key, "F", **kwargs)

    def perform(self, data, gid=0, src=0):
        pass


class Thing(Node):
    PID = None
    CHKEYS = "*"
    def __init__(self, key):
        self._children = {}
        self._subs = {}
        self._pubs = []
        self._mqtt = None
        Node.__init__(self, key)

    def add_child(self, node, seq=0):
        if node._seq==0:
            node._seq = len(self._children)+1
        self._children[node._key] = node
        return node

    def publish(self, topic, data=b'', qos=0):
        self._pubs.append((topic, data, qos))

    def request(self, action="", params={}, children=[]):
        Node.request(self, action=action, params=params)
        if len(children)>0:
            # request into children
            for c in self._children.values():
                if c._id in children:
                    c.request(action=action)

    def as_data(self):
        data = Node.as_data(self)
        if self.PID:
            data['product'] = self.PID
        elif len(self._children)>0:
            data['children'] = dict((k,v.as_data()) for k,v in self._children.items())
        return data

    def load_meta(self, meta):
        self._id = meta['id']

        # setup children
        for k, chinfo in meta["children"].items():
            if k in self._children:
                ch = self._children[k]
                assert ch._gender==chinfo['gender']

                ch._id = chinfo['id']

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

    def loop(self):
        time.sleep_ms(10)

    def _onmessage(self, topic, msg):
        if topic in self._subs:
            op, node = self._subs[topic]
            if op=="req":
                if len(msg)==0:
                    node.request()
                else:
                    try:
                        req = json.loads(msg)
                        node.request(action=req.get("action"), \
                                params=req.get("params"), \
                                children=req.get("children",[]))
                    except:
                        pass
            elif op=="act":
                data = _decode(msg, node.DATA_TYPE[0], node.DATA_TYPE[1])
                if data!=None:
                    node.perform(data)

    def start(self, host="iot.nodewox.org", port=8883, username=None, secret=b"", keepalive=300, ssl=True):
        assert self._id > 0

        if self._mqtt:
            self._mqtt.disconnect()

        if username==None:
            username = self._key

        self._mqtt = MQTTClient(b"thing-%d" % self._id, \
                host, port=port, \
                user=username, password=secret, \
                keepalive=keepalive, ssl=ssl)

        self._mqtt.set_callback(self._onmessage)
        self._mqtt.set_last_will("{}{}/r".format(NX_PREFIX, self._id), b'{"ack":"bye"}', qos=2)
        self._mqtt.connect(clean_session=False)
        print("connected")

        s = bytes("{}{}/q".format(NX_PREFIX, self._id), "utf-8")
        self._subs[s] = ("req", self)
        self._mqtt.subscribe(s)

        p = self.get_params_ack()
        if p:
            payload = json.loads(p)
        else:
            payload = b''
        self.publish("{}{}/r".format(NX_PREFIX, self._id), payload)

        for ch in self._children.values():
            s = bytes("{}{}/q".format(NX_PREFIX, self._id), "utf-8")
            self._subs[s] = ("req", ch)
            self._mqtt.subscribe(s)

            p = ch.get_params_ack()
            if p:
                payload = json.loads(p)
            else:
                payload = b''
            self.publish("{}{}/r".format(NX_PREFIX, ch._id), payload)

            if ch._gender=="F":
                s = bytes("{}{}".format(NX_PREFIX, ch._id), "utf-8")
                self._subs[s] = ("act", ch)
                self._mqtt.subscribe(s)

        print("starting...")
        while True:
            self._mqtt.check_msg()
            
            # publish pending messages
            if len(self._pubs)>0:
                for topic, data, qos in self._pubs:
                    self._mqtt.publish(topic, data, qos=qos)
                self._pubs.clear()

            # user loop code for each cycle
            self.loop()
            for ch in self._children.values():
                ch.loop()

            gc.collect()


def register(thing, user, passwd):
    addr = socket.getaddrinfo("192.168.0.7", 6601)[0][-1]
    sock = socket.socket()
    sock.connect(addr)
    ssock = ussl.wrap_socket(sock)

    data = bytes(json.dumps(thing.as_data()), "utf-8")
    req = [
            "POST /api/thing/register HTTP/1.0",
            "Host: 192.168.0.7",
            "X-Requested-With: XMLHttpRequest",
            "Authorization: USERPW %s\t%s" % (user, passwd),
            "Content-Type: application/json",
            "Content-Length: %d" % len(data),
            "",
            ""
    ]
    ssock.write(bytes("\r\n".join(req), "utf-8"))
    ssock.write(data)

    data = bytes()
    while True:
        b = ssock.read(128)
        if b:
            data += b
            gc.collect()
        else:
            break

    sep = bytes('\r\n\r\n', 'utf-8')
    i = data.find(sep)
    if i<0:
        sep = bytes('\n\n', "utf-8")
        i = data.find(sep)

    if i>0:
        headers = str(data[:i], "utf-8").split("\n")
        if len(headers)>0:
            status = headers[0].split()[1]

        content = data[i+len(sep):]
        res = json.loads(content)
        print(status, res['response'])

    gc.collect()

