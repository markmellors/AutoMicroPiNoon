from bluetooth_comms import Comms
import threading
import time
from comm_codes import Colour, State
comm_link = Comms()
comm_thread = threading.Thread(target=comm_link.run)
comm_thread.daemon = True
comm_thread.start()

while True:
    if comm_link.connected:
        print (State(comm_link.state).name)
        print (Colour(comm_link.colour).name)
        print (comm_link.motor_one)
    else:
        print("not connected")
        comm_link.state = State(OFFLINE).value
    time.sleep(0.1)

print ("finishing")

comm_link.stop()
comm_thread.join()
