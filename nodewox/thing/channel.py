#coding: utf-8
from node import Node
import nodewox.thinese as thinese

class Channel(Node):

    # channel datatype decl.
    DATA_TYPE = None  # invalidate
    DATA_DIM = 0

    def __init__(self, thing, key, flow, name="", latch=False, seq=0, exclusive=True, comment="", **kwargs):
        from thing import Thing
        assert isinstance(thing, Thing), thing
        assert key!="" and "/" not in key, key
        assert flow in ("I", "O"), flow

        datatype = self.DATA_TYPE
        datadim = self.DATA_DIM
        assert datadim>=0, datadim
        if flow=="I":
            assert datatype in (object, int, float, basestring, bool, bytearray), datatype
        else:
            assert datatype in (int, float, basestring, bool, bytearray), datatype

        self._parent = thing
        self._flow = flow
        self._datatype = datatype
        self._datadim = datadim
        self._latch = latch
        self._exclusive = exclusive
        self._seq = seq

        if name=="": name = self.NAME
        if name=="": name = chkey
        Node.__init__(self, key, parent=thing, name=name, comment=comment, **kwargs)


    def add_child(self, node):
        raise NotImplementedError


    def as_data(self):
        assert self._parent!=None
        res = Node.as_data(self)
        res.update({
                "flow": self._flow,
                "latch": self._latch,
                "lang": "",
                "seq": self._seq,
        })

        if self._datatype==int:
            res['datatype'] = ("int", self._datadim)
        elif self._datatype==float:
            res['datatype'] = ("number", self._datadim)
        elif self._datatype==basestring:
            res['datatype'] = ("string", self._datadim)
        elif self._datatype==bool:
            res['datatype'] = ("bool", self._datadim)
        elif self._datatype==bytearray:
            res['datatype'] = ("bin", self._datadim)

        if self._flow=="I":
            res['exclusive'] = self._exclusive
        else:
            res['exclusive'] = False

        return res


    def publish(self, topic, payload="", qos=0):
        self.parent.publish(topic, payload=payload, qos=qos)


    def subscribe(self, topic):
        self.parent.subscribe(topic)


    def unsubscribe(self, topic):
        self.parent.unsubscribe(topic)


    def handle_packet(self, packet):
        pass



class SourceChannel(Channel):
    DATA_TYPE = int
    def __init__(self, thing, key, **kwargs):
        Channel.__init__(self, thing, key, "O", **kwargs)



class ActuatorChannel(Channel):
    DATA_TYPE = object  # any
    def __init__(self, thing, key, **kwargs):
        Channel.__init__(self, thing, key, "I", **kwargs)

    def perform(self, src, gid, data):
        return None

    def handle_packet(self, packet):
        assert isinstance(packet, thinese.Packet), packet

        data = None
        f = packet.WhichOneof("data")
        if hasattr(packet, f):
            if self._datatype==int and f=="int_array":
                data = packet.int_array.value
            elif self._datatype==float and f=="num_array":
                data = packet.num_array.value
            elif self._datatype==basestring and f=="str_array":
                data = packet.str_array.value
            elif self._datatype==bool and f=="bool_array":
                data = packet.bool_array.value
            elif self._datatype==bytearray and f=="var_array":
                data = []
                for x in packet.var_array.value:
                    v = x.to_value()
                    if v==None or isinstance(v, bytearray):
                        data.append(v)
                    else:
                        data.append(None)

        if self._datatype!=None and data==None:
            print("invalid packet data")
            return

        return self.perform(packet.src, packet.gid, data)

