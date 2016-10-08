#coding: utf-8
from param import Param
import nodewox.thinese as thinese
import types
import collections

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

def to_int(val, default=None):
    if val==None:
        return default
    try:
        return int(val)
    except:
        return default

def to_float(val, default=None):
    if val==None:
        return default
    try:
        return float(val)
    except:
        return default

def to_bool(val, default=None):
    if type(val)==types.BooleanType:
        return val
    elif val==None:
        return default
    elif type(val) in (types.IntType, types.FloatType):
        return val not in (0, 0.0)
    elif val.lower() in ("true", "t", "yes", "y", "1"):
        return True
    elif val.lower() in ("false", "f", "no", "n", "0"):
        return False
    else:
        return default

def to_json(val, default=None):
    if val==None:
        return default
    try:
        return U8(json.loads(val))
    except:
        return default


class Node(object):
    "node base class"

    def __init__(self, key, name="", comment="", **kwargs):
        if key!=None:
            assert key!="" and "/" not in key, key

        if name=="":
            name = key

        # meta
        self._key = key
        self._name = name
        self._comment = comment
        self._params = {}
        self._id = None

        self.setup(**kwargs)


    def setup(self, **kwargs):
        pass


    @property
    def key(self): 
        return self._key


    def get_attrs(self):
        return []


    #
    # NODE PARAMS RELATED
    #
    def add_param(self, key, name="", datatype="", value=None, comment="", options=None, writable=False, seq=0):
        p = Param(key, name=name, datatype=datatype, value=value, options=options, writable=writable, seq=seq, comment=comment)
        self._params[key] = p

    def reset_params(self):
        "reset all params to initial value"
        for p in self._params.values():
            p.value = p.default

    def get_param(self, key, default=None):
        if key not in self._params:
            return default
        else:
            return self._params[key].value

    def has_param(self, key):
        return self._params.has_key(key)

    def set_param(self, key, value):
        if key in self._params and self._params[key].writable:
            '''
            dt = self._params[key].datatype
            if dt=="int":
                value = to_int(value)
            elif dt=="float":
                value = to_float(value)
            elif dt=="bool" and type(value)!=types.BooleanType:
                value = to_bool(value)
            else:
                value = U8(value)
            '''
            if self._params[key].value!=value:
                self._params[key].value = value
            return True
        else:
            return False

    def set_params(self, vals):
        assert type(vals)==types.DictType, vals
        cnt = 0
        for k, v in vals.items():
            if self.set_param(k, v):
                cnt += 1
        return cnt

    def get_status(self):
        return dict((k,v.value) for k,v in self._params.items() if v.value!=None)


    def as_data(self):
        assert self._key!=None
        res = {"key":self._key}

        if self._name not in ("", self._key):
            res['name'] = self._name

        if self._comment!="":
            res['comment'] = self.comment

        attrs = self.get_attrs()
        if len(attrs)>0:
            res['attrs'] = attrs

        if len(self._params)>0:
            res['params'] = dict((k,v.as_data()) for k,v in self._params.items())

        return res


    def request(self, msg):
        "processing incomming request"
        assert isinstance(msg, thinese.Request), msg
        res = None
        report_params = False

        if msg.action == thinese.Request.ACTION_CHECK_ALIVE:
            res = thinese.Response()

        elif msg.action == thinese.Request.ACTION_CHECK_PARAM:
            if len(self._params)>0:
                res = thinese.Response()
                report_params = True

        elif msg.action == thinese.Request.ACTION_CHECK_PARAM_ALIVE:
            res = thinese.Response()
            report_params = True

        elif msg.action == thinese.Request.ACTION_CONFIG:
            for k in msg.params:
                v = msg.params[k].to_value()
                self.set_param(k, v)
            res = thinese.Response()
            report_params = True

        if res!=None and report_params and len(self._params)>0:
            for p in self._params.values():
                va = thinese.Variant.from_value(p.value)
                f = va.WhichOneof("value")
                setattr(res.params[p.key], f, getattr(va, f))

        return res


    def tick(self):
        pass
