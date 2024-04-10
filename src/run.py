import queue
from flask import Flask, render_template, Response
import numpy as np
import cv2
import whisper
import torch
from flask_socketio import SocketIO
from videostreamhandler import VideoStreamHandler
from controlstream import ControlStream
from audiostreamhandler import AudioStreamHandler
from lidarstreamhandler import LidarStreamHandler
from decisionmaker import DecisionMaker

flask_instance = Flask(__name__)
socketio = SocketIO(flask_instance) # websocket

HOST_IP = "" # empty string for all available interfaces
VSH_PORT = 5005
CS_PORT = 5006
AUS_PORT = 5007
LSH_PORT = 5008

model = whisper.load_model("tiny.en")

vsh = VideoStreamHandler(HOST_IP, VSH_PORT)
cs = ControlStream(HOST_IP, CS_PORT)
ash = AudioStreamHandler(HOST_IP, AUS_PORT)
lsh = LidarStreamHandler(HOST_IP, LSH_PORT)

dm = DecisionMaker(vsh, lsh, cs, ash)

def gen_video_frame():
    """Gets frames from the VideoStreamHandler object and yields them as a byte stream for display on the webpage."""
    while True:
        frame = vsh.get_frame()
        if frame is not None and type(frame) == np.ndarray:
            #print("frame get")
            frame_bytes = frame.tobytes()
            yield (b'--frame\r\n'b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')  # concat frame one by one and show result
            if cv2.waitKey(1) == 27:
                break

def gen_lidar_frame():
    """Gets frames from the LidarStreamHandler object and yields them as a byte stream for display on the webpage."""
    while True:
        frame = lsh.get_frame()
        if frame and type(frame) == np.ndarray:
            frame_bytes = frame.tobytes()
            yield (b'--frame\r\n'b'Content-Type: image/png\r\n\r\n' + frame_bytes + b'\r\n')  # concat frame one by one and show result

def gen_audio():
    """Gets audio data from the AudioStreamHandler object and yields it as a byte stream for playback on the webpage."""
    while True:
        audio = ash.get_audio()
        if audio is not None and type(audio) == np.ndarray:
            yield audio.tobytes()

@socketio.on('json')
def handle_control(json):
    """Handles control data sent from the joystick on the webpage and sets it in the DecisionMaker object."""
    # separate x and y from the json into two variables for easier use
    data = [float(json['x']) / 100.0, float(json['y']) / 100.0]
    np_data = np.array(data, dtype=np.float32)

    # set the control data in the DecisionMaker object
    dm.set_control_data(np_data)

@flask_instance.route('/')
def index():
    return render_template('index.html')

@flask_instance.route('/video_feed')
def video_feed():
    return Response(gen_video_frame(), mimetype='multipart/x-mixed-replace; boundary=frame')

@flask_instance.route('/lidar_feed')
def lidar_feed():
    return Response(gen_lidar_frame(), mimetype='multipart/x-mixed-replace; boundary=frame')

@flask_instance.route('/audio_feed')
def audio_feed():
    return Response(gen_audio(), mimetype='audio/x-wav')

def main():
    # ash.start()
    vsh.start()
    lsh.start()
    cs.start()
    dm.start()
    flask_instance.run(host="0.0.0.0", port=80, use_reloader=False)

if __name__ == "__main__":
    try:
        main()
    except (KeyboardInterrupt, SystemExit):
        # ash.stop()
        vsh.stop()
        lsh.stop()
        cs.stop()
        dm.stop()
        print("Exiting safely...")