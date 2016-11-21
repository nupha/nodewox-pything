#coding: utf-8
from nodewox.thing import NX_PREFIX
from param import Param
import types
import collections
import sys
import traceback
import struct

class Node(object):
    "node base class"
    NAME = "" # default node name

    def __init__(self, key, name="", parent=None, comment="", **kwargs):
        assert isinstance(key, basestring), key
        assert key!="" and "/" not in key, key

        if name=="":
            name = self.NAME

        if parent!=None:
            assert isinstance(parent, Node), parent

        self._key = key
        self._name = name
        self._parent = parent
        self._comment = comment
        self._params = {}
        self._children = {}
        self._seq = 0
        self._id = None

        self.setup()


    @property
    def key(self): 
        return self._key

    @property
    def parent(self):
        return self._parent

    @property
    def children(self):
        return self._children

    def setup(self):
        pass

    def get_id(self):
        return self._id

    def add_child(self, node, seq=0):
        assert isinstance(node, Node), node
        assert node._parent==self
        assert node.key not in self._children, node.key
        if node._seq==0:
            node._seq = len(self._children)+1
        self._children[node.key] = node
        return node


    #
    # NODE PARAMS RELATED
    #
    def has_param(self, key):
        return self._params.has_key(key)

    def add_param(self, key, value, name="", comment="", options=[], flag="volatile", seq=-1):
        "defina a parameter with type of value"
        assert not self.has_param(key), key
        p = Param(key, value, name=name, options=options, flag=flag, comment=comment, seq=seq)
        if seq<0: p.seq = len(self._params) + 1
        self._params[key] = p
        return p

    def set_param(self, key, value):
        "set new value to a param"
        if key in self._params:
            return self._params[key].set_value(value)
        else:
            return False

    def set_params(self, vals):
        "set values of many params"
        assert type(vals)==types.DictType, vals
        cnt = 0
        for k, v in vals.items():
            if self.set_param(k, v):
                cnt += 1
        return cnt

    def get_param(self, key, default=None):
        if key not in self._params:
            return default
        else:
            return self._params[key].value

    def reset_params(self):
        "reset all params to itsinitial value"
        for p in self._params.values():
            p.reset()


    def as_data(self):
        assert isinstance(self._key, basestring) and self._key!=""
        res = {"key":self._key, "name":self._name, "seq":self._seq}

        if self._comment!="":
            res['comment'] = self.comment

        if len(self._params)>0:
            res['params'] = dict((k,v.as_data()) for k,v in self._params.items())

        return res


    def handle_request(self, action="", params={}, children=[]):
        "processe an incomming request"
        assert self._id > 0
        report_params = (action=="status")

        # set params
        for k,v in params.items():
            p = self._params.get(k)
            if p!=None:
                oval = p.value 
                if self.set_param(k, v):
                    self.on_param_changed(p, old_value=oval)
                    report_params = True

        # resport param status
        res = {}
        if report_params and len(self._params)>0:
            params = {}
            for p in self._params.values():
                if p.flag != "static":
                    params[p.key] = p.value
            if len(params)>0:
                res['params'] = params

        pubs = {"{}{}/r".format(NX_PREFIX, self.get_id()): res}
        if len(children)>0:
            # request into children
            for c in self.children.values():
                if c.get_id() in children:
                    r = c.handle_request(action=action)
                    if type(r)==types.DictType:
                        pubs.update(r)
        return pubs


    def loop(self):
        pass

    def on_param_changed(self, param, old_value):
        pass


    @classmethod
    def decode_packet(cls, packet, datatype, dim):
        assert isinstance(packet, (bytearray, basestring)), packet
        assert isinstance(datatype, basestring), datatype
        assert dim>=0, dim

        if datatype=="":
            data = bytearray(packet)
        elif len(packet)==0:
            data = []
        else:
            try:
                if datatype=="byte":
                    n = len(packet) / struct.calcsize("B")
                    data = struct.unpack("%dB" % n, packet)
                elif datatype=="int16":
                    n = len(packet) / struct.calcsize("h")
                    data = struct.unpack("!%dh" % n, packet)
                elif datatype=="int32":
                    n = len(packet) / struct.calcsize("i")
                    data = struct.unpack("!%di" % n, packet)
                elif datatype=="int64":
                    n = len(packet) / struct.calcsize("q")
                    data = struct.unpack("!%dq" % n, packet)
                elif datatype=="float":
                    n = len(packet) / struct.calcsize("f")
                    data = struct.unpack("!%df" % n, bytearray(packet))
                elif datatype=="bool":
                    n = len(packet) / struct.calcsize("B")
                    data = tuple(x!=0 for x in struct.unpack("!%dB" % n, packet))
                elif datatype=="string":
                    data = []
                    start = 0
                    while start < len(packet):
                        sz = packet[start:].find('\0')
                        assert sz>=0
                        if sz==0:
                            data.append("")
                        else:
                            data.append(struct.unpack("%ds" % sz, packet[start:start+sz]))
                        start += sz+1
                else:
                    raise NotImplementedError

                data = list(data)

            except:
                data = None
                traceback.print_exc(file=sys.stderr)

        if isinstance(data, list) and dim>0 and len(data)<dim:
            # padding list
            n = dim - len(data)
            if datatype in ("byte", "int16", "int32", "int64", "float"):
                data += [0] * n
            elif datatype=="bool":
                data += [False] * n
            elif datatype=="string":
                data += [""] * n

        return data


    @classmethod
    def encode_packet(cls, data, datatype, dim):
        if datatype == "":
            # string and bytearray converts to bytes
            # other data converts to null
            p = ""
            if data is not None and len(data)>0:
                if isinstance(data, basestring):
                    data = bytearray(data)
                    p = struct.pack("%dB" % len(data), *data)
                elif isinstance(data, bytearray):
                    p = struct.pack("%dB" % len(data), *data)

        else:
            assert isinstance(data, (list, tuple)), data

            if datatype=="byte":
                p = struct.pack("%dB" % len(data), *data)
            elif datatype=="int16":
                p = struct.pack("!%dh" % len(data), *data)
            elif datatype=="int32":
                p = struct.pack("!%di" % len(data), *data)
            elif datatype=="int64":
                p = struct.pack("!%dq" % len(data), *data)
            elif datatype=="float":
                p = struct.pack("!%df" % len(data), *data)
            elif datatype=="bool":
                p = struct.pack("!%db" % len(data), *data)
            elif datatype=="string":
                fmt = ""
                for s in data:
                    fmt += "%ds" % (len(s)+1)
                p = struct.pack(fmt, *data)
            else:
                raise NotImplementedError

        return bytearray(p)


    @classmethod
    def check_data(cls, data, datatype, dim):
        if datatype=="":
            if isinstance(data, basestring):
                data = bytearray(data)
            assert isinstance(data, bytearray), data

        else:
            if isinstance(data, bytearray):
                data = list(data)
            elif not isinstance(data, (list, tuple)):
                data = [data]
            else:
                if dim > 0 and len(data) < dim:
                    data = data[:dim] # truncate

            # fix data value
            if datatype=="byte":
                data = map(_byte, data)
            elif datatype=="int16":
                data = map(_int16, data)
            elif datatype=="int32":
                data = map(_int32, data)
            elif datatype=="int64":
                data = map(_int64, data)
            elif datatype=="float":
                data = map(_float, data)
            elif datatype=="bool":
                data = map(_bool, data)
            elif datatype=="string":
                data = map(_string, data)
            else:
                assert False, (datatype, data)

        assert isinstance(data, (list, tuple, bytearray)), data
        return data


#
# helpers
#
def _int(v):
    r = 0
    try:
        if isinstance(v, int):
            r = v
        elif isinstance(v, basestring):
            r = int(v)
        elif isinstance(v, bool):
            r = int(bool)
        elif isinstance(v, float):
            r = int(v)
    except:
        r = 0
    return r

def _byte(v):
    return _int(v) & 0xFF

def _int16(v):
    return _int(v) & 0xFFFF

def _int32(v):
    return _int(v) & 0xFFFFFFFF

def _int64(v):
    return _int(v) & 0xFFFFFFFFFFFFFFFF

def _float(v):
    r = 0
    try:
        if isinstance(v, float):
            r = v
        elif isinstance(v, int):
            r = float(v)
        elif isinstance(v, basestring):
            r = float(v)
        elif isinstance(v, bool):
            r = int(bool)
    except:
        r = 0
    return r

def _string(v):
    r = ""
    if isinstance(v, basestring):
        r = v
    elif isinstance(v, (int, float, bytearray)):
        r = str(v)
    elif isinstance(v, bool):
        r = str(bool).lower()
    return r

def _bool(v):
    r = False
    if isinstance(v, bool):
        r = v
    elif isinstance(v, (int, float)):
        r = int(v)!=0
    elif isinstance(v, basestring):
        r = v.lower() in ("true", "t", "yes", "y", "on", "1")
    return r


def U8(data):
    "convert data to utf-8"
    if isinstance(data, collections.Mapping):
        return dict((U8(key),U8(value)) for key, value in data.iteritems())
    elif isinstance(data, list):
        return [U8(x) for x in data]
    elif isinstance(data, unicode):
        return data.encode('utf-8')
    else:
        return data

