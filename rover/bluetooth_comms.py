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
        self.was_connected = True
        self.last_signal = None
        self.terminated = False
        advertise_service( self.server_sock, "SampleServer",
                           service_id = self.uuid,
                           service_classes = [ self.uuid, SERIAL_PORT_CLASS ],
                           profiles = [ SERIAL_PORT_PROFILE ], 
        #                   protocols = [ OBEX_UUID ] 
                            )
        print("comm_link initialised")
        self.connect()

    def init_communicated_properties(self):
        self.state = None
        self.colour = None
        self.motor_one = None
        self.motor_two = None

    def run(self):
        while not self.terminated:
            if not self.connected:
                if self.was_connected:
                    print("not connected, will try to connect")
                    self.was_connected = False
                self.connect()
            else:
                self.get_latest_data()
            if self.last_signal and self.last_signal < (time.clock() - self.TIME_OUT):
                self.connected = False

    def connect(self):
        self.server_sock.settimeout(1)
        try:
            self.client_sock, self.client_info = self.server_sock.accept()
            self.connected = True
            self.was_connected = True
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
            s = struct.Struct('iiff')
            values = s.unpack(data)
            print ("%s: received [%s]" % (datetime.now(), values))
            self.state, self.colour, self.motor_one,  self.motor_two = values
        except IOError:
            self.connected = False

    def stop(self):
        self.terminated = True
        try:
            self.client_sock.close()
        except:
            pass
        self.server_sock.close()
