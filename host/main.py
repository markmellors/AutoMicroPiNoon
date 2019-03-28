from flask import Flask, render_template, Response
from camera import VideoCamera
import time
import cv2

class Frame_holder():
    def __init__(self):
        camera = VideoCamera()
        self.frame = camera.get_frame()
        del camera

    def serve_frame(self):
        while True:
            time.sleep(0.01)
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + self.frame + b'\r\n\r\n')


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


frame_holder = Frame_holder()

def update_video(frame):
    ret, jpeg = cv2.imencode('.jpg', frame)
    frame_holder.frame = jpeg.tobytes()

def launch_video_feed():
    app.run(host='0.0.0.0', debug=False)

if __name__ == '__main__':
    launch_video_feed()
