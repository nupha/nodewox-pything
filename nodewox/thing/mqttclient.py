#coding: utf-8
import paho.mqtt.client as mqtt
import time
import signal
import types
import traceback

class MqttClientMixin(object):
    "mqtt client"

    def __init__(self, host="", port=-1, unpw=None, certfile="", keyfile="", cafile="", reconnect=1000):
        self._host = host
        self._port = port
        self._certfile = certfile
        self._keyfile = keyfile
        self._cafile = cafile

        if unpw!=None:
            self._username, self._password = unpw
        else:
            self._username = self._password = ""

        self._reconnect = reconnect

        # runtime        
        self._reconnect_factor = 1
        self._reconnect_try = 0
        self._next_connect_time = time.time()
        self._connected = False
        self._client = None


    @property
    def is_connected(self):
        return self._client!=None and self._connected


    def _sched_next_connect(self):
        if self._reconnect>0:
            if self._reconnect_factor<10:
                self._reconnect_factor = 1 + self._reconnect_try // 100
            print("schedule to reconnect after %sms" % (self._reconnect*self._reconnect_factor))
            self._next_connect_time = time.time() + self._reconnect*self._reconnect_factor/1000.0


    def on_connect(self, client, userdata, flags, rc):
        if rc==0:
            print("connected")
            self._connected = True
            self._reconnect_try = 0
            self._next_connect_time = 0
        else:
            print("connect fail")
            self._connected = False
            self._sched_next_connect()


    def on_disconnect(self, client, userdata, rc):
        print("disconnected")
        self._connected = False
        if client!=None:
            self._sched_next_connect()


    def on_subscribe(self, client, userdata, mid, granted_qos):
        pass


    def on_message(self, client, userdata, msg):
        print("on_message", msg.topic, msg.payload)


    def on_log(self, client, userdata, level, buf):
        #print(level, buf)
        pass


    def publish(self, topic, data="", qos=0):
        if self.is_connected:
            self._client.publish(topic, data, qos)


    def _prepare_connection(self, conn, client_id="", will=None):
        conn.reinitialise(client_id=client_id, clean_session=True)

        # mqtt callbacks
        conn.on_connect = self.on_connect
        conn.on_disconnect = self.on_disconnect
        conn.on_subscribe = self.on_subscribe
        conn.on_message = self.on_message
        conn.on_log = self.on_log

        # user account
        if self._username!="":
            conn.username_pw_set(self._username, self._password)

        if self._certfile!="":
            conn.tls_set(self._cafile, certfile=self._certfile, keyfile=self._keyfile)
            conn.tls_insecure_set(False)

        if will!=None:
            # will
            if type(will)==types.StringType:
                will = [will]

            assert type(will) in (types.ListType, types.TupleType), will
            wt = will[0]
            wp = None
            if len(will)>1:
                wp = will[1]
            conn.will_clear()
            conn.will_set(wt, payload=wp)

        return conn


    def connect(self):
        assert self._host!=""

        # reset next_conn_time flag
        self._next_connect_time = 0

        if not self.is_connected:
            self._reconnect_try += 1

            if self._client==None:
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


    def on_sig(self, *args):
        print("SIG", args[0])
        self._running = False

    def on_start(self):
        pass

    def on_stop(self):
        pass


    def start(self):
        signal.signal(signal.SIGINT, self.on_sig)
        signal.signal(signal.SIGTERM, self.on_sig)

        self.on_start()

        # main loop
        self._running = True
        while self._running:
            if not self.is_connected and (self._next_connect_time>0 and time.time()>=self._next_connect_time):
                self.connect()
            else:
                self.tick()

            # drive mqtt socket work
            if self._client:
                self._client.loop(0.005)

        # prepare to terminate
        if self._client!=None:
            if self.is_connected:
                self.on_disconnect(None, None, 0)
                time.sleep(0.1)

            self._client = None
            # in order to emit `will' message from host, don't call client.disconnect()
            #self._client.disconnect()

        self.on_stop()


    def tick(self):
        pass
