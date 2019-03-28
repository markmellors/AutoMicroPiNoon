from flask import Flask, render_template, Response
from camera import VideoCamera
import time
import threading

class Frame_holder():
    def __init__(self):
        camera = VideoCamera()
        self.frame = camera.get_frame()
        del camera

    def serve_frame(self):
        while True:
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + self.frame + b'\r\n\r\n')

frame_holder = Frame_holder()

import host
app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

def gen(camera):
    while True:
        frame = camera.get_frame()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n\r\n')

@app.route('/video_feed')
def video_feed():
#    return Response(gen(VideoCamera()),
    return Response(frame_holder.serve_frame(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')



def launch_video_feed():
    print("launched")
    host_thread = threading.Thread(target=host.run)
    host_thread.daemon = True
    host_thread.start()
    app.run(host='0.0.0.0', debug=False)

if __name__ == '__main__':
    launch_video_feed()
