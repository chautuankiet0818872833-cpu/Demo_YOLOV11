import cv2
from ultralytics import YOLO

# 1. Load mô hình đã huấn luyện (đảm bảo file best.pt cùng thư mục với file code này)
model = YOLO('best.pt')

# 2. Kết nối với Camera điện thoại
# CÁCH 1: Dùng Wifi qua app IP Webcam (Android)
# Tải app IP Webcam trên điện thoại. Mở app, kéo xuống dưới cùng chọn "Start server".
# App sẽ hiện một dải IP (Ví dụ: http://192.168.1.15:8080).
# Thay dãy IP đó vào biến camera_url dưới đây (Nhớ thêm /video ở cuối):
camera_url = 'http://192.168.110.250:8080/video'

# CÁCH 2: Dùng cáp USB qua app DroidCam hoặc Iriun Webcam (Android/iOS)
# Tải DroidCam/Iriun trên cả điện thoại và máy tính, cắm cáp để kết nối.
# Máy tính sẽ nhận điện thoại như một webcam ảo (số 0, 1 hoặc 2).
# Nếu dùng Cách 2, hãy comment dòng cap = cv2.VideoCapture(camera_url) ở dưới 
# và bỏ comment dòng cap = cv2.VideoCapture(0)

cap = cv2.VideoCapture(camera_url)
# cap = cv2.VideoCapture(0) # Bỏ comment dòng này nếu dùng DroidCam/Iriun/Webcam Laptop

# Đặt độ phân giải (Tùy chọn, giúp chạy mượt hơn)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

if not cap.isOpened():
    print("Không thể kết nối đến Camera! Vui lòng kiểm tra lại IP hoặc kết nối.")
    exit()

print("Đang bật Camera... Bấm phím 'q' trên cửa sổ Camera để thoát.")

while True:
    # Đọc từng frame ảnh từ camera
    success, frame = cap.read()
    
    if not success:
        print("Lỗi khi đọc khung hình từ Camera.")
        break
    
    # 3. Đưa khung hình vào mô hình để dự đoán (predict)
    # tham số conf=0.5 nghĩa là chỉ hiện những vật thể có độ tin cậy > 50%
    results = model.predict(source=frame, conf=0.5, show=False)
    
    # 4. Vẽ bounding box và tên class lên khung hình
    annotated_frame = results[0].plot()
    
    # Hiển thị khung hình
    cv2.imshow('Test Camera Dien Thoai - YOLO', annotated_frame)
    
    # Nhấn phím 'q' để thoát vòng lặp
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# Giải phóng camera và đóng cửa sổ
cap.release()
cv2.destroyAllWindows()
