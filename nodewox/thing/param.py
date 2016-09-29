#coding: utf-8
import json

class Param(object):

    def __init__(self, key, name="", datatype="string", value=None, options=[], writable=False, persistent=False, comment="", seq=99999):
        assert key not in ("", "id"), key
        assert datatype in ("int", "string", "float", "bool"), datatype

        self.key = key
        self.name = name
        self.seq = seq
        self.datatype = datatype
        self.comment = comment
        self.value = value
        self.default = value
        self.persistent = persistent
        self.writable = writable

        if options!=None:
            assert len(options)>0
            assert type(options) in (types.ListType, types.TupleType), options
            opts = []
            for x in options:
                if type(x) in (types.ListType, types.TupleType):
                    assert len(x)==2
                    opts.append(x)
                else:
                    opts.append((str(x), str(x)))
        else:
            opts = None
        self.options = opts


    def as_data(self):
        res = {
            "datatype": self.datatype,
            "seq": self.seq,
            "value": self.value,
            "writable": self.writable,
            "persistent": self.persistent,
        }

        if self.name not in ("", self.key):
            res['name'] = self.name

        if self.comment!="":
            res['comment'] = self.comment

        if self.options!=None:
            res['options'] = json.dumps(self.options)

        return res

