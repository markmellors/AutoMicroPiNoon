from bluetooth import *
from datetime import datetime
from time
import struct
import binascii
from enum import Enum

class Comms:
    '''class to establish a bluetooth comm link with host.''' 
    def __init__(self):
        self.server_sock=BluetoothSocket( RFCOMM )
        self.server_sock.bind(("",PORT_ANY))
        self.server_sock.listen(1)
        advertise_service( self.server_sock, "SampleServer",
                            service_id = uuid,
                            service_classes = [ uuid, SERIAL_PORT_CLASS ],
                            profiles = [ SERIAL_PORT_PROFILE ], 
        #                   protocols = [ OBEX_UUID ] 
                    )
        self.TIME_OUT = 3
        self.init_communciated_properties()
        self.connected = False
        self.last_signal = None
        self.terminated = False
        #call establish connection
        self.start()

    class State(Enum):
        #state enumeration
        AUTO = 0
        OFFLINE = 1
        RC = 2
        STOPPED = 3


    def init_communicated_properties(self):
        self.state = None
        self.state_colour_codes = {
            State.AUTO: "RED",
            State.OFFLINE: "BLUE",
            State.RC: "GREEN",
            State.STOPPED: "MAGENTA",
        }
        self.colour = None
        self.motor_one = None
        self.motor_two = None

    def run(self):
        while not self.terminated:
            if not self.connected
                self.state = state.OFFLINE
                self.motor_one, self.motor_two = 0, 0    
                self.connect()
            else:
                self.get_latest_data()
            if self.last_signal < (time.clock() - self.TIME_OUT):
                self.connected = False

    def connect(self):
        self.client_sock, self.client_info = self.server_sock.accept()

    def get_latest_data(self):
        try:
            data = self.client_sock.recv(1024)
            if len(data) == 0: 
                print "socket data length is %d" % len(data)
                self.last_signal = time.clock()
                continue
            if len(data)>8:
                firstbyte = len(data)-8
                lastbyte = len(data)
                data = data[firstbyte:lastbyte]
                print "data collision, trying last 8 bytes"
            if len(data) != 8:
                print "%s: partial receive, data length is %d - skipping" % (datetime.now(), len(data))
                continue
            s = struct.Struct('h2f')
            values = s.unpack(data)
            print "%s: received [%s]" % (datetime.now(), values)
            self.state = values[0]
            self.motor_one,  self.motor_two = values[1:2]
        except IOError:
            self.connected = False

    @state.setter:
    def state(self, state):
        if state:
            self.__state = state
            self.colour = self.state_colour_codes.get(state, state.OFFLINE)
   
     
    def cloe(self):
        self.termianted = True
        self.client_sock.close()
        self.server_sock.close()
