import time
from datetime import datetime
from host_comms import Host_comms
import threading

comms = Host_comms()
comms.connect()
time.sleep(3)
input("input")
for i in range (0, 30):
    comms.send_packet(3, 2,0.5,0.5)
    print (datetime.now())
    time.sleep(0.03)
    comms.send_packet(3, 3,0.5,0.5)
    print (datetime.now())
    time.sleep(0.03)

