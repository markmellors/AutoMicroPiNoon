from bluetooth import *
from datetime import datetime
import time
import struct
import binascii
from enum import Enum

class Comms:
    '''class to establish a bluetooth comm link with host.''' 
    def __init__(self):
        self.server_sock=BluetoothSocket( RFCOMM )
        self.server_sock.bind(("",PORT_ANY))
        self.server_sock.listen(1)
        port = self.server_sock.getsockname()[1]
        self.uuid = "94f39d29-7d6d-437d-973b-fba39e49d4ee"
        self.TIME_OUT = 3
        self.init_communicated_properties()
        self.connected = False
        self.last_signal = None
        self.terminated = False
        advertise_service( self.server_sock, "SampleServer",
                           service_id = self.uuid,
                           service_classes = [ self.uuid, SERIAL_PORT_CLASS ],
                           profiles = [ SERIAL_PORT_PROFILE ], 
        #                   protocols = [ OBEX_UUID ] 
                            )
        self.connect()

    class State(Enum):
        #state enumeration
        AUTO = 0
        OFFLINE = 1
        RC = 2
        STOPPED = 3

    def init_communicated_properties(self):
        self._state = None
        self.state_colour_codes = {
            self.State.AUTO: "RED",
            self.State.OFFLINE: "BLUE",
            self.State.RC: "GREEN",
            self.State.STOPPED: "MAGENTA",
        }
        self.colour = None
        self.motor_one = None
        self.motor_two = None

    def run(self):
        while not self.terminated:
            if not self.connected:
                self.state = self.State.OFFLINE
                self.motor_one, self.motor_two = 0, 0
                print("not connected, will try to connect")
                self.connect()
            else:
                self.get_latest_data()
            if self.last_signal and self.last_signal < (time.clock() - self.TIME_OUT):
                self.connected = False

    def connect(self):
        print("trying to connect to server")
        self.server_sock.settimeout(1)
        try:
            self.client_sock, self.client_info = self.server_sock.accept()
            self.connected = True
            print("connected")
        except BluetoothError as e:
            # socket.timeout is presented as BluetoothError w/o errno
            if e.args[0] == 'timed out':
                pass

    def get_latest_data(self):
        try:
            data = self.client_sock.recv(1024)
            if len(data) == 0: 
                print ("socket data length is %d" % len(data))
                self.last_signal = time.clock()
            if len(data)>12:
                firstbyte = len(data)-12
                lastbyte = len(data)
                data = data[firstbyte:lastbyte]
                print ("data collision, trying last 12 bytes")
            if len(data) != 12:
                print ("%s: partial receive, data length is %d - skipping" % (datetime.now(), len(data)))
            s = struct.Struct('iff')
            values = s.unpack(data)
            print ("%s: received [%s]" % (datetime.now(), values))
            self.state, self.motor_one,  self.motor_two = values
        except IOError:
            self.connected = False

    @property
    def state(self):
        return self._state

    @state.setter
    def state(self, state):
        if state:
            self.__state = state
            self.colour = self.state_colour_codes.get(state, self.State.OFFLINE) 
  
    def stop(self):
        self.terminated = True
        try:
            self.client_sock.close()
        except:
            pass
        self.server_sock.close()
