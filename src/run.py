import queue
from flask import Flask, render_template, Response
import numpy as np
import cv2
from flask_socketio import SocketIO
from videostreamhandler import VideoStreamHandler
from controlstream import ControlStream


flask_instance = Flask(__name__)
socketio = SocketIO(flask_instance) # websocket

VS_HOST = "localhost"
CS_HOST = "68.162.66.104"
VSH_PORT = 5005
CS_PORT = 5006

control_queue = queue.Queue()

vsh = VideoStreamHandler(VS_HOST, VSH_PORT)
cs = ControlStream(CS_HOST, CS_PORT, control_queue)


def gen_frames():
    while True:
        frame = vsh.get_frame()
        if frame is not None and type(frame) == np.ndarray:
            print("frame get")
            frame_bytes = frame.tobytes()
            yield (b'--frame\r\n'b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')  # concat frame one by one and show result
            if cv2.waitKey(1) == 27:
                break

@socketio.on('json')
def handle_message(json):
    # separate x and y from the json into two variables for easier use
    data = (float(json['x']) / 100.0, float(json['y']) / 100.0)
    control_queue.put(data)

@flask_instance.route('/')
def index():
    return render_template('index.html')

@flask_instance.route('/video_feed')
def video_feed():
    return Response(gen_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

def main():
    vsh.start()
    cs.start()
    flask_instance.run(host="0.0.0.0", port=80, use_reloader=False)
    vsh.stop()
    cs.stop()

if __name__ == "__main__":
    main()