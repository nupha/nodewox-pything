#coding: utf-8
from talk_pb2 import Variant, Packet, Request, Response
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

    if v.HasField("int_val"):
        return v.int_val
    elif v.HasField("real_val"):
        return v.real_val
    elif v.HasField("str_val"):
        return v.str_val
    elif v.HasField("bool_val"):
        return v.bool_val
    elif v.HasField("bin_val"):
        if len(v.bin_val)==0:
            return None
        else:
            return bytearray(v.bin_val)


Variant.from_value = classmethod(_val_to_variant)
Variant.to_value = _variant_to_val


