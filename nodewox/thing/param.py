#coding: utf-8
import json

class Param(object):

    def __init__(self, key, value, name="", options=[], writable=False, persistent=False, comment="", seq=0):
        assert key not in ("", "id"), key

        # check validity of init value
        self.datatype = None
        for t in (int, float, bool, basestring):
            if isinstance(value, t):
                self.datatype = t
                break
        if self.datatype==None:
            raise Exception("invalid init value: not acceptable type"), value

        self.key = key
        self.name = name
        self.seq = seq
        self.comment = comment
        self.value = value
        self.init_value = value
        self.persistent = persistent
        self.writable = writable
        self.disabled = False

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


    def set_value(self, val):
        if isinstance(val, self.datatype) and self.writable and self.value!=val:
            self.value = val
            return True
        else:
            return False


    def reset(self):
        self.value = self.init_value


    def as_data(self):
        res = {
            "seq": self.seq,
            "value": self.value,
            "writable": self.writable,
            "persistent": self.persistent,
        }

        if self.datatype==int:
            res['datatype'] = "int"
        elif self.datatype==float:
            res['datatype'] = "number"
        elif self.datatype==basestring:
            res['datatype'] = "string"
        elif self.datatype==bool:
            res['datatype'] = "bool"

        if self.name not in ("", self.key):
            res['name'] = self.name

        if self.comment!="":
            res['comment'] = self.comment

        if self.options!=None:
            res['options'] = json.dumps(self.options)

        return res

