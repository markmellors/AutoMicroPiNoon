# file: rfcomm-server.py
# auth: Albert Huang <albert@csail.mit.edu>
# desc: simple demonstration of a server application that uses RFCOMM sockets
#
# $Id: rfcomm-server.py 518 2007-08-10 07:20:07Z albert $

import explorerhat
from bluetooth import *
from datetime import datetime
from time import sleep
import struct
import binascii

server_sock=BluetoothSocket( RFCOMM )
server_sock.bind(("",PORT_ANY))
server_sock.listen(1)

port = server_sock.getsockname()[1]

uuid = "94f39d29-7d6d-437d-973b-fba39e49d4ee"

advertise_service( server_sock, "SampleServer",
                   service_id = uuid,
                   service_classes = [ uuid, SERIAL_PORT_CLASS ],
                   profiles = [ SERIAL_PORT_PROFILE ], 
#                   protocols = [ OBEX_UUID ] 
                    )
#explorer output pin mapping to RGB led legs                   
BLUE_PIN = 2
RED_PIN = 0
GREEN_PIN = 1

#brightness (0-100) mapping for different colours
BLUE = [0, 0, 100]
RED = [100, 0, 0]
GREEN = [0, 100, 0]
CYAN = [0, 100, 100]
MAGENTA = [100, 0, 100]
YELLOW = [100, 40, 0]

colour = MAGENTA
explorerhat.output[RED_PIN].brightness(colour[0])
explorerhat.output[GREEN_PIN].brightness(colour[1])
explorerhat.output[BLUE_PIN].brightness(colour[2])

print "Waiting for connection on RFCOMM channel %d" % port

client_sock, client_info = server_sock.accept()
print "Accepted connection from ", client_info
try:
    while True:
        data = client_sock.recv(1024)
        if len(data) == 0: 
            print "socket data length is %d" % len(data)
            continue
        if len(data)>8:
            firstbyte = len(data)-8
            lastbyte = len(data)
            data = data[firstbyte:lastbyte]
            print "data collision, trying last 8 bytes"
        if len(data) != 8:
            print "%s: partial receive, data length is %d - skipping" % (datetime.now(), len(data))
            continue
        s = struct.Struct('2f')
 	values = s.unpack(data)
        print "%s: received [%s]" % (datetime.now(), values)
        motor_one,  motor_two = values
        explorerhat.motor.one.speed(motor_one)
        explorerhat.motor.two.speed(motor_two)
except IOError:
    pass

print "disconnected"

client_sock.close()
server_sock.close()
print "all done"
