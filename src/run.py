from flask import Flask, render_template, Response
import numpy as np
import cv2
import socket
import pickle
from videostreamhandler import VideoStreamHandler

#Initialize the Flask app
app = Flask(__name__)

host = "" # empty string should specify localhost
port = 5005

vsh = VideoStreamHandler(host, port)

def gen_frames():
    while True:
        frame = vsh.get_frame()
        if frame is not None and type(frame) == np.ndarray:
            print("frame get")
            frame_bytes = frame.tobytes()
            yield (b'--frame\r\n'b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')  # concat frame one by one and show result
            if cv2.waitKey(1) == 27:
                break
            
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/video_feed')
def video_feed():
    return Response(gen_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

def main():
    vsh.start()
    app.run(host="0.0.0.0", port=80, use_reloader=False)
    vsh.stop()

if __name__ == "__main__":
    main()