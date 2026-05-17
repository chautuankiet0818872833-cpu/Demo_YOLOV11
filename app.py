from flask import Flask, render_template, Response, request, jsonify
import cv2
from ultralytics import YOLO

app = Flask(__name__)

# Tải mô hình YOLO
try:
    model = YOLO('best.pt')
    print("Đã tải mô hình best.pt thành công!")
except Exception as e:
    print(f"Lỗi khi tải mô hình: {e}")
    model = None

# Cấu hình Camera mặc định (0 để dùng Webcam máy tính)
DEFAULT_CAMERA_URL = 0
current_camera_url = DEFAULT_CAMERA_URL
cap = None

def get_camera():
    global cap
    if cap is None or not cap.isOpened():
        cap = cv2.VideoCapture(current_camera_url)
        # Tối ưu độ phân giải
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    return cap

def release_camera():
    global cap
    if cap is not None:
        cap.release()
        cap = None

def generate_frames():
    camera = get_camera()
    while True:
        if not camera.isOpened():
            break
            
        success, frame = camera.read()
        if not success:
            # Reconnect on fail? For now just yield empty or break
            break
        
        # Inference bằng YOLO
        if model:
            results = model.predict(source=frame, conf=0.5, show=False, verbose=False)
            annotated_frame = results[0].plot()
        else:
            annotated_frame = frame

        # Chuyển đổi khung hình OpenCV sang định dạng JPEG
        ret, buffer = cv2.imencode('.jpg', annotated_frame)
        if not ret:
            continue
            
        frame_bytes = buffer.tobytes()
        
        # Yield luồng dữ liệu (multipart)
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/video_feed')
def video_feed():
    # Route này trả về luồng video liên tục
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/update_camera', methods=['POST'])
def update_camera():
    global current_camera_url
    data = request.json
    if 'url' in data:
        new_url = data['url']
        if new_url.strip() == "0":
            current_camera_url = 0
        else:
            current_camera_url = new_url
        # Khởi động lại camera
        release_camera()
        return jsonify({"status": "success", "message": "Đã cập nhật camera url!"})
    return jsonify({"status": "error", "message": "Thiếu thông tin URL."})

if __name__ == '__main__':
    # Chạy Flask server
    app.run(host='0.0.0.0', port=5000, debug=True)
