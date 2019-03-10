from bluetooth_comms import Comms
import threading
import time
comm_link = Comms()
comm_thread = threading.Thread(target=comm_link.run)
comm_thread.daemon = True
comm_thread.start()

time.sleep(15)
print (comm_link.state)
print (comm_link.colour)
print ("finishing")

comm_link.stop()
comm_thread.join()
