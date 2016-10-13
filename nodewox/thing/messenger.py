#coding: utf-8
import paho.mqtt.client as mqtt
import nodewox.thinese as thinese
import time
import signal
import types
import traceback
import re

PAT_REQ   = re.compile(r"^\/NX\/(\d+)\/q$")
PAT_RES    = re.compile(r"^\/NX\/(\d+)\/r$")
PAT_PACKET  = re.compile(r"^\/NX\/(\d+)$")

class Messenger(object):
    def __init__(self, master_node, host="", port=-1, unpw=None, certfile="", keyfile="", cafile=""):
        from node import Node
        assert isinstance(master_node, Node), master_node

        self._node = master_node
        self._host = host
        self._port = port
        self._certfile = certfile
        self._keyfile = keyfile
        self._cafile = cafile

        if unpw!=None:
            self._username, self._password = unpw
        else:
            self._username = self._password = ""

        # runtime        
        self._reconnect_factor = 1
        self._reconnect_try = 0
        self._next_connect_time = time.time()
        self._connected = False
        self._client = None


    @property
    def is_connected(self):
        return self._client!=None and self._connected


    def get_reconnect_interval(self):
        return 1000


    def _sched_next_connect(self):
        timeout = self.get_reconnect_interval()
        if timeout > 0:
            if self._reconnect_factor<10:
                self._reconnect_factor = 1 + self._reconnect_try // 100
            print("schedule to reconnect after %sms" % (timeout * self._reconnect_factor))
            self._next_connect_time = time.time() + timeout * self._reconnect_factor/1000.0


    def ack_msg_request(self, client, userdata, msg):
        try:
            req = thinese.Request.FromString(msg.payload)
        except:
            # bad request body
            return

        _id = int(PAT_REQ.findall(msg.topic)[0])
        res = {}

        if _id == self._node.get_id():
            res2 = self._node.handle_request(req)
            if res2 != None:
                res.update(res2)

            if len(req.children) > 0:
                # request to children too
                for ch in self._node.children.values():
                    if ch._id in req.children:
                        res2 = ch.handle_request(req)
                        if res2 != None:
                            res.update(res2)

        else:
            lst = [x for x in self._node.children.values() if x.get_id()==_id]
            if len(lst)>0:
                res2 = lst[0].handle_request(req)
                if res2 != None:
                    res.update(res2)

        for topic, msg in res.items():
            assert isinstance(msg, thinese.Response), msg
            client.publish(topic, bytearray(msg.SerializeToString()))


    def ack_msg_packet(self, client, userdata, msg):
        _id = int(PAT_EVENT.findall(msg.topic)[0])
        chs = [x for x in self._node.children.values() if x.get_id()==_id]
        if len(chs) > 0:
            chan = chs[0]

            if hasattr(chan, handle_packet):
                try:
                    packet = thinese.Packet.FromString(msg.payload)
                except:
                    # bad data
                    return

                f = packet.WhichOneof("data")
                if hasattr(packet, f):
                    data = getattr(packet, f).value
                else:
                    data = None
                chan.handle_packet(packet.src, packet.gid, data)


    def _on_connect(self, client, userdata, flags, rc):
        if rc==0:
            self._connected = True
            self._reconnect_try = 0
            self._next_connect_time = 0
            self._node.on_connected(userdata)
        else:
            self._connected = False
            self._node.on_connect_fail(rc, userdata)
            self._sched_next_connect()

    def _on_disconnect(self, client, userdata, rc):
        self._connected = False
        self._node.on_disconnected(rc, userdata)
        if client!=None:
            self._sched_next_connect()

    def _on_subscribe(self, client, userdata, mid, granted_qos):
        pass

    def _on_message(self, client, userdata, msg):
        self._node.on_message(msg, userdata)

    def _on_log(self, client, userdata, level, buf):
        print(level, buf)


    def publish(self, topic, data="", qos=0):
        if self.is_connected:
            self._client.publish(topic, data, qos)


    def subscribe(self, topic):
        if self._client:
            if type(topic)==types.StringType:
                topic = [topic]
            else:
                assert type(topic) in (types.ListType, types.TupleType)
                assert len(topic)>0
            self._client.subscribe([(x,2) for x in set(topic)])


    def unsubscribe(self, topic):
        if self._client:
            if type(topic)==types.StringType:
                topic = [topic]
            else:
                assert type(topic) in (types.ListType, types.Tuple)
                assert len(topic)>0
            self._client.unsubscribe([(x,2) for x in set(topic)])


    def get_client_id(self):
        return self._node._key


    def get_will(self):
        bye = bytearray(thinese.Response(acktype=thinese.Response.ACK_BYE).SerializeToString())
        return ("/NX/%d/r" % self._node.get_id(), bye)


    def _prepare_connection(self, conn):
        conn.reinitialise(client_id=self.get_client_id(), clean_session=True)

        # mqtt callbacks
        conn.on_connect = self._on_connect
        conn.on_disconnect = self._on_disconnect
        conn.on_subscribe = self._on_subscribe
        conn.on_message = self._on_message
        conn.on_log = self._on_log

        # user account
        if self._username!="":
            conn.username_pw_set(self._username, self._password)

        if self._certfile!="":
            conn.tls_set(self._cafile, certfile=self._certfile, keyfile=self._keyfile)
            conn.tls_insecure_set(False)

        will = self.get_will()
        if will != None:
            if type(will)==types.StringType:
                will = [will]

            assert type(will) in (types.ListType, types.TupleType), will
            wt = will[0]
            wp = None
            if len(will)>1:
                wp = will[1]

            if wt != "":
                conn.will_clear()
                conn.will_set(wt, payload=wp)

        conn.message_callback_add("/NX/+/q", self.ack_msg_request)
        conn.message_callback_add("/NX/+", self.ack_msg_packet)

        return conn


    def connect(self):
        assert self._host!=""
        assert self._node.get_id() > 0

        # reset next_conn_time flag
        self._next_connect_time = 0

        if not self.is_connected:
            self._reconnect_try += 1

            if self._client == None:
                self._client = self._prepare_connection(mqtt.Client())
                reconn = False
            else:
                reconn = True

            try:
                if not reconn:
                    if self._port<=0:
                        if self._certfile!="":
                            p = 8883
                        else:
                            p = 1883
                    else:
                        p = self._port
                    self._client.connect(self._host, port=p, keepalive=60)
                else:
                    self._client.reconnect()
            except:
                traceback.print_exc()
                self._sched_next_connect()

        self._client.loop(1)
        return self._client


    def loop(self):
        if not self.is_connected and (self._next_connect_time>0 and time.time()>=self._next_connect_time):
            self.connect()
        else:
            # drive mqtt socket work
            if self._client:
                self._client.loop(0.005)

