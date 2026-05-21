from flask import Flask, render_template, Response, request, jsonify
import cv2
from ultralytics import YOLO
import threading
import time
import os
import logging
import atexit
# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s in %(module)s: %(message)s',
)
logger = logging.getLogger(__name__)
app = Flask(__name__, template_folder='../frontend/templates', static_folder='../frontend/static')

# Tải mô hình YOLO
MODEL_PATH = os.getenv('YOLO_MODEL_PATH', os.path.join(os.path.dirname(os.path.abspath(__file__)), 'best.pt'))
CONF_THRESHOLD = float(os.getenv('YOLO_CONF_THRESHOLD', '0.5'))
FRAME_WIDTH = int(os.getenv('FRAME_WIDTH', '640'))
FRAME_HEIGHT = int(os.getenv('FRAME_HEIGHT', '480'))
try:
    model = YOLO(MODEL_PATH)
    logger.info(f"Đã tải mô hình {MODEL_PATH} thành công!")
except Exception as e:
    logger.error(f"Lỗi khi tải mô hình: {e}")
    model = None

class CameraStream:
    """Manage camera capture and YOLO inference in a background thread."""

    def __init__(self, src=0, model=None):
        self.src = src
        self.model = model
        self.cap = cv2.VideoCapture(self.src)
        # Thiết lập độ phân giải camera
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, FRAME_WIDTH)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, FRAME_HEIGHT)
        
        self.grabbed, self.frame = self.cap.read()
        self.annotated_frame = None
        if self.grabbed:
            if self.model:
                results = self.model.predict(source=self.frame, conf=0.5, show=False, verbose=False)
                self.annotated_frame = results[0].plot()
            else:
                self.annotated_frame = self.frame.copy()
        
        self.started = False
        self.read_lock = threading.Lock()
        self.thread = None

    def start(self):
        """Start the background thread for frame capture and inference."""
        if self.started:
            return self
        self.started = True
        self.thread = threading.Thread(target=self.update, args=())
        self.thread.daemon = True
        self.thread.start()
        return self

    def update(self):
        """Continuously read frames, run YOLO inference, and store annotated frames."""
        while self.started:
            grabbed, frame = self.cap.read()
            if not grabbed:
                time.sleep(0.01)
                continue
            
            # Chạy suy luận YOLO trực tiếp trên background thread này
            if self.model:
                results = self.model.predict(source=frame, conf=0.5, show=False, verbose=False)
                annotated = results[0].plot()
            else:
                annotated = frame.copy()
                
            with self.read_lock:
                self.grabbed = grabbed
                self.frame = frame
                self.annotated_frame = annotated

    def read(self):
        """Thread‑safe retrieval of the latest annotated frame."""
        with self.read_lock:
            if self.annotated_frame is not None:
                return self.grabbed, self.annotated_frame.copy()
            return self.grabbed, None

    def stop(self):
        """Stop the background thread and release the camera resource."""
        self.started = False
        if self.thread:
            self.thread.join(timeout=1.0)
        if self.cap.isOpened():
            self.cap.release()

# Cấu hình Camera mặc định (0 để dùng Webcam máy tính)
DEFAULT_CAMERA_URL = 0
current_camera_url = DEFAULT_CAMERA_URL
camera_stream = None
stream_lock = threading.Lock()

def get_camera_stream():
    global camera_stream
    with stream_lock:
        if camera_stream is None:
            camera_stream = CameraStream(src=current_camera_url, model=model)
            camera_stream.start()
        return camera_stream

def release_camera_stream():
    global camera_stream
    with stream_lock:
        if camera_stream is not None:
            camera_stream.stop()
            camera_stream = None

# Ensure camera resources are released on process exit
atexit.register(release_camera_stream)
def generate_frames():
    while True:
        stream = get_camera_stream()
        success, frame = stream.read()
        if not success or frame is None:
            time.sleep(0.03)  # Tránh chiếm dụng tài nguyên CPU khi chưa sẵn sàng
            continue
            
        # Chuyển đổi khung hình OpenCV sang định dạng JPEG
        ret, buffer = cv2.imencode('.jpg', frame)
        if not ret:
            continue
            
        frame_bytes = buffer.tobytes()
        
        # Yield luồng dữ liệu (multipart)
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
        
        # Giới hạn tốc độ gửi để tiết kiệm băng thông mạng (~30 FPS)
        time.sleep(0.03)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/video_feed')
def video_feed():
    # Route này trả về luồng video liên tục
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')


@app.route('/health')
def health():
    """Simple health check endpoint."""
    return jsonify(status='ok')
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
        # Khởi động lại camera stream
        release_camera_stream()
        return jsonify({"status": "success", "message": "Đã cập nhật camera url!"})
    return jsonify({"status": "error", "message": "Thiếu thông tin URL."})

if __name__ == '__main__':
    # Chạy Flask server
    app.run(host='0.0.0.0', port=5000, debug=True)
