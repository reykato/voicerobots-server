import queue
from flask import Flask, render_template, Response, render_template_string
import numpy as np
import cv2
import whisper
import torch
from flask_socketio import SocketIO
from videostreamhandler import VideoStreamHandler
from controlstream import ControlStream
from audiostreamhandler import AudioStreamHandler


flask_instance = Flask(__name__)
socketio = SocketIO(flask_instance) # websocket

HOST_IP = "" # empty string for all available interfaces
VSH_PORT = 5005
CS_PORT = 5006
AUS_PORT = 5007

control_queue = queue.Queue()
model = whisper.load_model("tiny.en")

vsh = VideoStreamHandler(HOST_IP, VSH_PORT)
cs = ControlStream(HOST_IP, CS_PORT, control_queue)
aus = AudioStreamHandler(HOST_IP, AUS_PORT)

def gen_frames():
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
        audio = aus.get_audio()
        if audio is not None and type(audio) == np.ndarray:
            buffer = np.concatenate((buffer, audio), axis=0)
            if buffer.size > 1000000:
                mathonbuffer = buffer.astype(np.float32) / 32768.0
                result = model.transcribe(mathonbuffer, fp16=torch.cuda.is_available())
                buffer = np.ndarray(shape=(0,))
                print(result['text'])
                yield result["text"]

def gen_audio():
    while True:
        audio = aus.get_audio()
        if audio is not None and type(audio) == np.ndarray:
            yield audio.tobytes()

@socketio.on('json')
def handle_message(json):
    # separate x and y from the json into two variables for easier use
    data = [float(json['x']) / 100.0, float(json['y']) / 100.0]
    np_data = np.array(data, dtype=np.float32)
    control_queue.put(np_data)

@flask_instance.route('/')
def index():
    return render_template('index.html')

@flask_instance.route('/video_feed')
def video_feed():
    return Response(gen_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

@flask_instance.route('/audio_feed')
def audio_feed():
    return Response(gen_audio(), mimetype='audio/x-wav')

@flask_instance.route('/transcription_feed')
def transcription_feed():
    text = gen_audio_to_text()
    return Response(text, content_type='text/plain')

def main():
    vsh.start()
    cs.start()
    # aus.start()
    flask_instance.run(host="0.0.0.0", port=80, use_reloader=False)
    vsh.stop()
    cs.stop()
    # aus.stop()

if __name__ == "__main__":
    main()