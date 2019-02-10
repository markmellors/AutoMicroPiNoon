# file: rfcomm-server.py
# auth: Albert Huang <albert@csail.mit.edu>
# desc: simple demonstration of a server application that uses RFCOMM sockets
#
# $Id: rfcomm-server.py 518 2007-08-10 07:20:07Z albert $

import explorerhat
from bluetooth import *
from datetime import datetime

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
                   
print "Waiting for connection on RFCOMM channel %d" % port

client_sock, client_info = server_sock.accept()
print "Accepted connection from ", client_info

try:
    while True:
        data = client_sock.recv(1024)
        if len(data) == 0: 
            print "socket data length is %d" % len(data)
            continue
        print "%s: received [%s]" % (datetime.now(), data)
	values = data.split(",")
        if len(values) != 2:
            print "data length is %d - skipping" % len(values)
            continue
        motor_one,  motor_two = [float(f) for f in data.split(",")]
        explorerhat.motor.one.speed(motor_one)
        explorerhat.motor.two.speed(motor_two)
except IOError:
    pass

print "disconnected"

client_sock.close()
server_sock.close()
print "all done"
