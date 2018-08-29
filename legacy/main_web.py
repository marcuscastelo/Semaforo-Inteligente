# main.py

from flask import Flask, render_template, Response
from camera import VideoCamera

import os
app = Flask(__name__ ,template_folder=os.path.abspath('html'))

@app.route('/')
def index():
    #print (os.
    return render_template('index.html')

def gen(camera):
    while True:
        frame = camera.get_frame()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n\r\n')

@app.route('/video_feed_v')
def video_feed_v():
    return Response(gen(VideoCamera('video.mp4')),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/video_feed_h')
def video_feed_h():
    return Response(gen(VideoCamera('_video.mp4')),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)