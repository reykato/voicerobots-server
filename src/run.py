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

dm = DecisionMaker(vsh, lsh, cs)

def gen_video_frame():
    while True:
        frame = vsh.get_frame()
        if frame is not None and type(frame) == np.ndarray:
            #print("frame get")
            frame_bytes = frame.tobytes()
            yield (b'--frame\r\n'b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')  # concat frame one by one and show result
            if cv2.waitKey(1) == 27:
                break

def gen_audio_to_text():
    buffer = np.ndarray(shape=(0,))

    while True:
        audio = ash.get_audio()
        if audio is not None and type(audio) == np.ndarray:
            buffer = np.concatenate((buffer, audio), axis=0)
            if buffer.size > 1000000:
                mathonbuffer = buffer.astype(np.float32) / 32768.0
                result = model.transcribe(mathonbuffer, fp16=torch.cuda.is_available())
                buffer = np.ndarray(shape=(0,))
                print(result['text'])
                yield result["text"]

def gen_lidar_frame():
    while True:
        frame = lsh.get_frame()
        if frame and type(frame) == np.ndarray:
            frame_bytes = frame.tobytes()
            yield (b'--frame\r\n'b'Content-Type: image/png\r\n\r\n' + frame_bytes + b'\r\n')  # concat frame one by one and show result

def gen_audio():
    while True:
        audio = ash.get_audio()
        if audio is not None and type(audio) == np.ndarray:
            yield audio.tobytes()

@socketio.on('json')
def handle_control(json):
    # separate x and y from the json into two variables for easier use
    data = [float(json['x']) / 100.0, float(json['y']) / 100.0]
    np_data = np.array(data, dtype=np.float32)
    # control_queue.put(np_data)
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

@flask_instance.route('/transcription_feed')
def transcription_feed():
    text = gen_audio_to_text()
    return Response(text, content_type='text/plain')

def main():
    # ash.start()
    vsh.start()
    lsh.start()
    cs.start()
    # dm.start()
    flask_instance.run(host="0.0.0.0", port=80, use_reloader=False)

if __name__ == "__main__":
    try:
        main()
    except (KeyboardInterrupt, SystemExit):
        # ash.stop()
        vsh.stop()
        lsh.stop()
        cs.stop()
        # dm.stop()
        print("Exiting safely...")