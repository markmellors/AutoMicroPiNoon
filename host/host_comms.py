
from bluetooth import *
import struct
import binascii

class Host_comms:
    '''class to establish a bluetooth comm link with rover.''' 
    def __init__(self):
        self.connected = False
        self.was_connected = True

    def connect(self):
        # search for the SampleServer service
        uuid = "94f39d29-7d6d-437d-973b-fba39e49d4ee"
        addr = "B8:27:EB:51:3C:F9"
        service_matches = find_service( uuid = uuid, address = addr )

        if len(service_matches) == 0:
            if self.was_connected:
                print ("couldn't find the SampleServer service")
                self.was_connected = False
            return

        first_match = service_matches[0]
        port = first_match["port"]
        name = first_match["name"]
        host = first_match["host"]

        print ("connecting to \"%s\" on %s" % (name, host))

               # Create the client socket
        self.sock=BluetoothSocket( RFCOMM )
        self.sock.connect((host, port))
        print ("bluetooth connected")
        self.connected = True
        self.was_connected = True
 


    def send_packet(self, state_val, colour_val, power_left, power_right):
        data = (state_val, colour_val, power_left, power_right)
        s = struct.Struct('iiff')
        packed_data = s.pack(*data)
        self.sock.send(packed_data)
