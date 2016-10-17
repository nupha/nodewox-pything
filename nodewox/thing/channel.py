#coding: utf-8
from node import Node
from Queue import Queue
import types
import time
import struct
import traceback
import sys

class Channel(Node):

    # channel datatype decl.
    DATA_TYPE = ("", 0)

    def __init__(self, thing, key, flow, name="", latch=False, seq=0, exclusive=True, comment="", **kwargs):
        from thing import Thing
        assert isinstance(thing, Thing), thing
        assert key!="" and "/" not in key, key
        assert flow in ("I", "O"), flow

        assert self.DATA_TYPE[0] in ("int16", "int32", "int64", "byte", "float", "bool", "string", ""), self.DATA_TYPE
        assert self.DATA_TYPE[1]>=0, self.DATA_TYPE

        self._parent = thing
        self._flow = flow
        self._latch = latch
        self._exclusive = exclusive
        self._seq = seq
        self._time_wakeup = 0

        if name=="": name = self.NAME
        if name=="": name = chkey
        Node.__init__(self, key, parent=thing, name=name, comment=comment, **kwargs)


    def add_child(self, node):
        raise NotImplementedError

    @property
    def is_awake(self):
        if self._time_wakeup!=0 and time.time() >= self._time_wakeup:
            self._time_wakeup = 0
        return self._time_wakeup==0


    def sleep(self, ms):
        if ms > 0:
            self._time_wakeup = max(self._time_wakeup, time.time() + ms/1000.0)


    def as_data(self):
        assert self._parent!=None
        res = Node.as_data(self)
        res.update({
                "flow": self._flow,
                "latch": self._latch,
                "lang": "",
                "seq": self._seq,
        })

        if self.DATA_TYPE[0]=="":
            res['datatype'] = ("", 0)
        else:
            res['datatype'] = self.DATA_TYPE

        if self._flow=="I":
            res['exclusive'] = self._exclusive
        else:
            res['exclusive'] = False

        return res


class SourceChannel(Channel):
    DATA_TYPE = ("", 0)
    QSIZE = 20

    def __init__(self, thing, key, **kwargs):
        Channel.__init__(self, thing, key, "O", **kwargs)
        self._dataq = Queue(self.QSIZE)

    def _encode_packet(self, data):
        if self.DATA_TYPE[1] == "":
            if len(data)>0:
                assert isinstance(data, bytearray)
                p = struct.pack("%dB" % len(data), *data)
            else:
                p = ""

        else:
            assert type(data) == types.ListType, data

            if self.DATA_TYPE[0]=="byte":
                p = struct.pack("%dB" % len(data), *data)
            elif self.DATA_TYPE[0]=="int16":
                p = struct.pack("!%dh" % len(data), *data)
            elif self.DATA_TYPE[0]=="int32":
                p = struct.pack("!%di" % len(data), *data)
            elif self.DATA_TYPE[0]=="int64":
                p = struct.pack("!%dq" % len(data), *data)
            elif self.DATA_TYPE[0]=="float":
                p = struct.pack("!%df" % len(data), *data)
            elif self.DATA_TYPE[0]=="bool":
                p = struct.pack("!%db" % len(data), *data)
            elif self.DATA_TYPE[0]=="string":
                fmt = ""
                for s in data:
                    fmt += "%ds" % (len(s)+1)
                p = struct.pack(fmt, *data)
            else:
                raise NotImplementedError

        return bytearray(p)


    def clear_data(self):
        while not self._dataq.empty():
            self._dataq.get()

    def feed_data(self, data, gid=0):
        if self.DATA_TYPE[0]=="":
            assert isinstance(data, bytearray), data

        else:
            if type(data) not in (types.ListType, types.TupleType):
                data = [data]
            else:
                data = list(data)
                if self.DATA_TYPE[1] > 0 and len(data) < self.DATA_TYPE[1]:
                    # truncate
                    data = data[self.DATA_TYPE[1]:]

            # check data value
            for i, x in enumerate(data):
                if self.DATA_TYPE[0]=="int32":
                    assert type(x)==types.IntType, x
                    assert x>=-2147483648 and x<=2147483647, x
                elif self.DATA_TYPE[0]=="int16":
                    assert type(x)==types.IntType, x
                    assert x>=-32768 and x<=32767, x
                elif self.DATA_TYPE[0]=="int64":
                    assert type(x)==types.IntType, x
                    assert x>=-9223372036854775808 and x<=9223372036854775807, x
                elif self.DATA_TYPE[0]=="bool":
                    assert x in (True, False), x
                    if x:
                        data[i] = 1
                    else:
                        data[i] = 0
                elif self.DATA_TYPE[0]=="string":
                    assert type(x)==types.StringType, x
                elif self.DATA_TYPE[0]=="float":
                    assert type(x)==types.FloatType, x
                elif self.DATA_TYPE[0]=="byte":
                    if type(x)==types.IntType:
                        assert x>=0 and x<=255, x
                    elif type(x)==types.StringType:
                        assert ord(x)>=0 and ord(x)<=255, ord(x)
                        data[i] = ord(x)
                    else:
                        assert False, x

        if self._dataq.full(): self._dataq.get()
        self._dataq.put((gid, data))


    def send_data(self):
        n = 0
        if self.get_id()>0:
            mess = self.parent.get_messenger()
            if mess.is_connected:
                topic = "/NX/%d" % self.get_id()
                while not self._dataq.empty():
                    gid, data = self._dataq.get()
                    p = self._encode_packet(data)
                    assert isinstance(p, bytearray), p
                    mess.publish(topic, p)
                    n += 1
        return n


    def loop(self):
        self.send_data()


class ActuatorChannel(Channel):
    DATA_TYPE = ("", 0)

    def __init__(self, thing, key, **kwargs):
        Channel.__init__(self, thing, key, "I", **kwargs)

    def perform(self, data, gid=0, src=0):
        raise NotImplementedError

    def handle_packet(self, packet):
        assert isinstance(packet, (bytearray, basestring)), packet
        if self.DATA_TYPE[0]=="":
            data = bytearray(packet)

        elif len(packet)==0:
            data = []

        else:
            # decode packet
            try:
                if self.DATA_TYPE[0]=="byte":
                    n = len(packet) / struct.calcsize("B")
                    data = struct.unpack("%dB" % n, packet)
                elif self.DATA_TYPE[0]=="int16":
                    n = len(packet) / struct.calcsize("h")
                    data = struct.unpack("!%dh" % n, packet)
                elif self.DATA_TYPE[0]=="int32":
                    n = len(packet) / struct.calcsize("i")
                    data = struct.unpack("!%di" % n, packet)
                elif self.DATA_TYPE[0]=="int64":
                    n = len(packet) / struct.calcsize("q")
                    data = struct.unpack("!%dq" % n, packet)
                elif self.DATA_TYPE[0]=="float":
                    n = len(packet) / struct.calcsize("f")
                    data = struct.unpack("!%df" % n, packet)
                elif self.DATA_TYPE[0]=="bool":
                    n = len(packet) / struct.calcsize("B")
                    data = tuple(x!=0 for x in struct.unpack("!%dB" % n, packet))
                elif self.DATA_TYPE[0]=="string":
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

                data = list(data)

            except:
                data = None
                traceback.print_exc(file=sys.stderr)

        if isinstance(data, list) and self.DATA_TYPE[1]>0 and len(data)<self.DATA_TYPE[1]:
            # list size padding
            n = (self.DATA_TYPE[1]-len(data))
            if self.DATA_TYPE[0] in ("byte", "int16", "int32", "int64", "float"):
                data += [0] * n
            elif self.DATA_TYPE[0]=="bool":
                data += [False] * n
            elif self.DATA_TYPE[0]=="string":
                data += [""] * n

        # perform action
        return self.perform(data)

