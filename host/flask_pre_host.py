from flask import Flask, render_template, Response
from camera import VideoCamera
import time
from multiprocessing import Process
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

class Frame_holder():
    def __init__(self):
        camera = VideoCamera()
        self.frame = camera.get_frame()
        del camera

    def serve_frame(self):
        print("served")
        while True:
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + self.frame + b'\r\n\r\n')

print("launch point")
def launch_video_feed():
    print("launched")
    global frame_holder
    frame_holder = Frame_holder()
    app.run(host='0.0.0.0', debug=False)

if __name__ == '__main__':
    launch_video_feed()
