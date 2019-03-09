from bluetooth import *
from datetime import datetime
from time
import struct
import binascii

class Comms:
    '''class to establish a bluetooth comm link with host.''' 
    def __init__(self):
        server_sock=BluetoothSocket( RFCOMM )
        server_sock.bind(("",PORT_ANY))
        server_sock.listen(1)
        advertise_service( server_sock, "SampleServer",
                            service_id = uuid,
                            service_classes = [ uuid, SERIAL_PORT_CLASS ],
                            profiles = [ SERIAL_PORT_PROFILE ], 
        #                   protocols = [ OBEX_UUID ] 
                    )
        self.TIME_OUT = 3 
        self.connected = False
        self.last_signal = None
        self.terminated = False
        #call establish connection
        self.start()

    def run(self):
        while not self.terminated:
            if not self.connected
                #establish connection
                self.connect()
            else:
                self.get_latest_data()
            if self.last_signal < (time.clock() - self.TIME_OUT):
                self.connected = False

    def connect(self):
        client_sock, client_info = server_sock.accept()

    def get_latest_data(self):
        data = client_sock.recv(1024)
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
        s = struct.Struct('hff')
 	values = s.unpack(data)
        print "%s: received [%s]" % (datetime.now(), values)
        motor_one,  motor_two = values



