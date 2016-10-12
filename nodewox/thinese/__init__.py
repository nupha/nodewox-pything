#coding: utf-8
from talk_pb2 import Variant, Packet, Pair, Request, Response, IntArray, NumArray, BoolArray, StrArray, VariantArray, PairArray
import types

# fix Variant
def _val_to_variant(cls, val):
    tp = type(val)

    if tp==types.NoneType:
        res = Variant(bin_val=b'')
    elif tp==types.BooleanType:
        res = Variant(bool_val=val)
    elif tp==types.StringType:
        res = Variant(str_val=val)
    elif tp in (types.IntType, types.LongType):
        res = Variant(int_val=val)
    elif tp==types.FloatType:
        res = Variant(real_val=val)
    elif isinstance(val, bytearray):
        if len(val)==0:
            res = Variant(bin_val=b'')
        else:
            res = Variant(bin_val=str(val))
    else:
        assert False, (val, tp)

    assert res!=None
    return res


def _variant_to_val(v):
    assert isinstance(v, Variant), v
    ret = None
    f = v.WhichOneof("value")
    if f != "":
        ret = getattr(v, f)
        if f == "bin_val":
            if len(ret)==0:
                ret = None
            else:
                ret = bytearray(ret)
    return ret


# set value to Variant
def _put_to_variant(self, val):
    tp = type(val)

    if tp==types.NoneType:
        self.bin_val = b''
    elif tp==types.BooleanType:
        self.bool_val = val
    elif tp==types.StringType:
        self.str_val = val
    elif tp in (types.IntType, types.LongType):
        self.int_val = val
    elif tp==types.FloatType:
        self.num_val = val
    elif isinstance(val, bytearray):
        if len(val)==0:
            self.bin_val = b''
        else:
            self.bin_val = str(val)
    else:
        assert False, (val, tp)


Variant.from_value = classmethod(_val_to_variant)
Variant.to_value = _variant_to_val
Variant.put_value = _put_to_variant

