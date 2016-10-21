#coding: utf-8
import json

class Param(object):

    def __init__(self, key, value, name="", flag="volatile", options=[], comment="", seq=0):
        assert key not in ("", "id"), key
        assert flag in ("volatile", "persistent", "readonly", "static"), flag

        # check validity of init value
        self.datatype = None
        if value in (True, False):
            self.datatype = bool
        else:
            for t in (int, float, basestring):
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
            assert self.datatype in (int, basestring)
            for i, x in enumerate(options):
                if isinstance(x, (list,tuple)):
                    assert isinstance(x[0], self.datatype)
                    assert isinstance(x[1], basestring)
                else:
                    assert isinstance(x, basestring)
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
        elif self.datatype==basestring:
            res['datatype'] = "string"
        elif self.datatype==bool:
            res['datatype'] = "bool"
        else:
            raise NotImplementedError

        if self.name not in ("", self.key):
            res['name'] = self.name

        if self.comment!="":
            res['comment'] = self.comment

        if len(self.options)>0:
            res['options'] = options

        return res

