#coding: utf-8
from node import Node

class Channel(Node):

    def __init__(self, thing, key, flow, name="", datatype="", latch=False, seq=0, exclusive=True, comment="", **kwargs):
        from thing import Thing
        assert isinstance(thing, Thing), thing
        assert key!="" and "/" not in key, key
        assert flow in ("I", "O"), flow

        self._parent = thing
        self._flow = flow
        self._datatype = datatype
        self._latch = latch
        self._exclusive = exclusive
        self._seq = seq

        Node.__init__(self, key, name=name, comment=comment, **kwargs)


    def as_data(self):
        assert self._parent!=None
        res = Node.as_data(self)
        res.update({
                "flow": self._flow,
                "datatype": self._datatype,
                "latch": self._latch,
                "lang": "",
                "seq": self._seq,
        })
        if self._flow=="I":
            res['exclusive'] = self._exclusive
        else:
            res['exclusive'] = False
        return res


    def get_thing(self):
        assert self._parent!=None
        return self._parent


    def publish(self, topic, payload="", qos=0):
        self.get_thing().publish(topic, payload=payload, qos=qos)


    def subscribe(self, topic):
        self.get_thing().subscribe(topic)


    def unsubscribe(self, topic):
        self.get_thing().unsubscribe(topic)

