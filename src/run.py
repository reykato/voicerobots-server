from flask import Flask, render_template, Response
import numpy as np
import os
os.environ["OPENCV_IO_MAX_IMAGE_PIXELS"] = str(pow(2,40))
import cv2
import socket
import pickle

#Initialize the Flask app
app = Flask(__name__)

host = "" # empty string should specify localhost
port = 5005
max_length = 65540

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind((host, port))

frame_info = None
buffer = None
frame = None

def gen_frames():
    while True:
        data, address = sock.recvfrom(max_length)
        
        if len(data) < 100:
            frame_info = pickle.loads(data)

            if frame_info:
                nums_of_packs = frame_info["packs"]

                for i in range(nums_of_packs):
                    data, address = sock.recvfrom(max_length)

                    if i == 0:
                        buffer = data
                    else:
                        buffer += data

                frame = np.frombuffer(buffer, dtype=np.uint8)
                frame = frame.reshape(frame.shape[0], 1)

                frame = cv2.imdecode(frame, cv2.IMREAD_COLOR)
                # frame = cv2.flip(frame, 1)

                if frame is not None:
                    ret, buffer_test = cv2.imencode('.jpg', frame)
                    frame_test = buffer_test.tobytes()
                
                if frame is not None and type(frame) == np.ndarray:
                    yield (b'--frame\r\n'
                           b'Content-Type: image/jpeg\r\n\r\n' + frame_test + b'\r\n')  # concat frame one by one and show result
                    if cv2.waitKey(1) == 27:
                        break
            

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/video_feed')
def video_feed():
    return Response(gen_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=80, use_reloader=False)