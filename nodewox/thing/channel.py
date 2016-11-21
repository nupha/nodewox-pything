#coding: utf-8
from nodewox.thing import NX_PREFIX
from node import Node
from Queue import Queue
import types
import time

class Channel(Node):

    # channel datatype decl.
    DATA_TYPE = ("", 0)

    def __init__(self, thing, key, gender, name="", latch=False, seq=0, exclusive=True, comment="", **kwargs):
        from thing import Thing
        assert isinstance(thing, Thing), thing
        assert gender in ("F", "M"), gender

        assert self.DATA_TYPE[0] in ("int16", "int32", "int64", "byte", "float", "bool", "string", ""), self.DATA_TYPE
        assert self.DATA_TYPE[1]>=0, self.DATA_TYPE

        self._parent = thing
        self._gender = gender
        self._latch = latch
        self._exclusive = exclusive
        self._seq = seq
        self._time_wakeup = 0

        if name=="": name = self.NAME
        if name=="": name = key

        Node.__init__(self, key, parent=thing, name=name, comment=comment, **kwargs)


    @property
    def is_awake(self):
        if self._time_wakeup!=0 and time.time() >= self._time_wakeup:
            self._time_wakeup = 0
        return self._time_wakeup==0

    def sleep(self, ms):
        if ms > 0:
            self._time_wakeup = max(self._time_wakeup, time.time() + ms/1000.0)

    def add_child(self, node):
        raise NotImplementedError

    def as_data(self):
        assert self._parent!=None
        res = Node.as_data(self)
        res.update({
                "gender": self._gender,
                "latch": self._latch,
                "lang": "",
                "seq": self._seq,
        })

        if self.DATA_TYPE[0]=="":
            res['datatype'] = ("", 0)
        else:
            res['datatype'] = self.DATA_TYPE

        if self._gender=="F":
            res['exclusive'] = self._exclusive
        else:
            res['exclusive'] = False

        return res


class MaleChannel(Channel):
    DATA_TYPE = ("", 0)
    QSIZE = 10

    def __init__(self, thing, key, **kwargs):
        Channel.__init__(self, thing, key, "M", **kwargs)
        self._dataq = Queue(self.QSIZE)

    def clear_data(self):
        while not self._dataq.empty():
            self._dataq.get()

    def feed_data(self, data, gid=0, src=0):
        data = self.check_data(data, self.DATA_TYPE[0], self.DATA_TYPE[1])
        if self._dataq.full(): 
            self._dataq.get()
        self._dataq.put((data, gid, src))

    def send_data(self):
        n = 0
        if self.get_id()>0:
            mess = self.parent.get_messenger()
            if mess.is_connected:
                topic = "{}{}".format(NX_PREFIX, self.get_id())
                while not self._dataq.empty():
                    data, gid, src = self._dataq.get()
                    p = self.encode_packet(data, self.DATA_TYPE[0], self.DATA_TYPE[1])
                    assert isinstance(p, bytearray), p
                    mess.publish(topic, p)
                    n += 1
        return n


    def loop(self):
        self.send_data()


class FemaleChannel(Channel):
    DATA_TYPE = ("", 0)

    def __init__(self, thing, key, **kwargs):
        Channel.__init__(self, thing, key, "F", **kwargs)

    def handle_packet(self, packet, src=0):
        data = self.decode_packet(packet, self.DATA_TYPE[0], self.DATA_TYPE[1])
        if data!=None:
            return self.perform(data, src=src)  # perform action

    def perform(self, data, gid=0, src=0):
        raise NotImplementedError

