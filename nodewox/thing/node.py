#coding: utf-8
from param import Param
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


class Node(object):
    "node base class"

    # default node name
    NAME = ""

    def __init__(self, key, name="", parent=None, comment="", **kwargs):
        if key!=None:
            assert key!="" and "/" not in key, key

        if name=="":
            name = self.NAME

        if parent!=None:
            assert isinstance(parent, Node), parent

        # meta
        self._key = key
        self._name = name
        self._parent = parent
        self._comment = comment
        self._params = {}
        self._children = {}
        self._id = None

        self.setup(**kwargs)


    def setup(self, **kwargs):
        pass


    @property
    def key(self): 
        return self._key


    @property
    def parent(self):
        return self._parent


    def get_id(self):
        return self._id


    def add_child(self, node):
        assert isinstance(node, Node), node
        assert node._parent==self
        assert node.key not in self._children, node.key
        self._children[node.key] = node
        return node

    @property
    def children(self):
        return self._children


    def get_attrs(self):
        return []


    #
    # NODE PARAMS RELATED
    #
    def has_param(self, key):
        return self._params.has_key(key)

    def add_param(self, key, value, name="", comment="", options=[], flag="dynamic", seq=-1):
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


    def handle_request(self, action=0, params={}, children=[]):
        "processe an incomming request"
        assert self._id > 0

        report_params = (action==1)

        # set params
        if len(params)>0:
            for k,v in params.items():
                if self.set_param(k, v):
                    report_params = True

        # resport param status
        res = {}
        if report_params and len(self._params)>0:
            params = {}
            for p in self._params.values():
                if p.flag != "STATIC":
                    params[p.key] = p.value
            if len(params)>0:
                res['params'] = params

        pubs = {"/NX/%d/r" % self.get_id(): res}

        if len(children)>0:
            # request into children
            for c in self.children:
                if c.get_id() in children:
                    r = c.handle_request(action=action)
                    if type(r)==types.DictType:
                        pubs.update(r)

        return pubs


    def loop(self):
        pass
    
