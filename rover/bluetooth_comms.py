import bluetooth as bt
from datetime import datetime
import time
import struct
import binascii
from enum import Enum

class Comms:
    '''class to establish a bluetooth comm link with host.'''
    def __init__(self):
        self.server_sock=bt.BluetoothSocket( bt.RFCOMM )
        self.server_sock.bind(("",PORT_ANY))
        self.server_sock.listen(1)
        port = self.server_sock.getsockname()[1]
        self.uuid = "94f39d29-7d6d-437d-973b-fba39e49d4ee"
        self.TIME_OUT = 3
        self.init_communicated_properties()
        self.connected = False
        self.last_signal = None
        self.terminated = False
        bt.advertise_service( self.server_sock, "SampleServer",
                           service_id = self.uuid,
                           service_classes = [ self.uuid, bt.SERIAL_PORT_CLASS ],
                           profiles = [ bt.SERIAL_PORT_PROFILE ],
        #                   protocols = [ bt.OBEX_UUID ]
                            )
        self.connect()

    def init_communicated_properties(self):
        self.state = None
        self.colour = None
        self.motor_one = None
        self.motor_two = None

    def run(self):
        while not self.terminated:
            if not self.connected:
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
        except bt.BluetoothError as e:
            # socket.timeout is presented as BluetoothError w/o errno
            if e.args[0] == 'timed out':
                pass

    def get_latest_data(self):
        try:
            data = self.client_sock.recv(1024)
            data_len = len(data)

            chunk = data[12 * -1:]

            if len(chunk) == 12:
                self.last_signal = time.clock()
                s = struct.Struct('iiff')
                values = s.unpack(data)
                print ("%s: received [%s]" % (datetime.now(), values))
                self.state, self.colour, self.motor_one,  self.motor_two = values

            else:
                print ("%s: partial receive, data length is %d - skipping" % (datetime.now(), len(chunk)))

        except IOError:
            self.connected = False

    def stop(self):
        self.terminated = True
        try:
            self.client_sock.close()
        except:
            pass
        self.server_sock.close()
