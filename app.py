import io
from PIL import Image
import cv2
from flask import Flask, render_template, request, Response
import os
from ultralytics import YOLO

app = Flask(__name__, static_folder='static')

@app.route("/")
def index():
    return render_template('index.html')

@app.route('/ppe')
def ppe():
    return render_template('PPE.html')  # Render PPE.html page

@app.route("/predict_img", methods=["POST"])
def predict_img():
    if 'file' in request.files:
        f = request.files['file']
        basepath = os.path.dirname(__file__)
        filepath = os.path.join(basepath, 'uploads', f.filename)
        f.save(filepath)
        print(filepath)

        file_extension = f.filename.rsplit('.', 1)[1].lower()

        if file_extension == 'jpg':
            img = cv2.imread(filepath)
            frame = cv2.imencode('.jpg', img)[1].tobytes()

            image = Image.open(io.BytesIO(frame))

            # Perform object detection
            yolo = YOLO('best.pt')
            results = yolo(image, save=True)
            res_plotted = results[0].plot()
            output_path = os.path.join('static', f.filename)
            cv2.imwrite(output_path, res_plotted)
            return render_template('PPE.html', image_path=f.filename)

    return "File format not supported or file not uploaded properly."

@app.route("/predict_video", methods=["POST"])
def predict_video():
    if 'file' in request.files:
        f = request.files['file']
        basepath = os.path.dirname(__file__)
        filepath = os.path.join(basepath, 'uploads', f.filename)
        f.save(filepath)

        file_extension = f.filename.rsplit('.', 1)[1].lower()

        if file_extension == 'mp4':
            video_path = filepath
            cap = cv2.VideoCapture(video_path)
            frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            fourcc = cv2.VideoWriter_fourcc(*'avc1')
            output_path = os.path.join('static', f.filename)
            out = cv2.VideoWriter(output_path, fourcc, 30.0, (frame_width, frame_height))
            yolo = YOLO('best.pt')
            frames = [] 
            i = 0
            while cap.isOpened():
                ret, frame = cap.read()
                if not ret:
                    break
                i += 1
                if i < 10:
                    continue
                i = 0
                results = yolo(frame, save=False)
                res_plotted = results[0].plot()

                # Append processed frame to list
                frames.append(res_plotted)

                if cv2.waitKey(1) == ord('q'):
                    break

            # Write all frames to output video
            for frame in frames:
                out.write(frame)

            cap.release()
            out.release()
            cv2.destroyAllWindows()
            return render_template('PPE.html', video_path=f.filename)

@app.route("/webcam")
def webcam():
    # Render the HTML page for the webcam feed
    return render_template('video_feed.html')

@app.route("/webcam_feed")
def webcam_feed():
    cap = cv2.VideoCapture(0)
    model = YOLO('best.pt')
    
    def generate():
        while True:
            success, frame = cap.read()
            if not success:
                break
            ret, buffer = cv2.imencode('.jpg', frame) 
            frame = buffer.tobytes()
            print(type(frame))
            
            img = Image.open(io.BytesIO(frame))
 
            
            results = model(img, save=True)              
            print(results)
            cv2.waitKey(1)
            res_plotted = results[0].plot()
            cv2.imshow("result", res_plotted)
            if cv2.waitKey(1) == ord('q'):
                break

            # 直接對 res_plotted 進行編碼，不進行顏色空間轉換
            frame = cv2.imencode('.jpg', res_plotted)[1].tobytes()
                
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n\r\n')
    return Response(generate(), mimetype='multipart/x-mixed-replace; boundary=frame')

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)