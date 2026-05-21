// static/js/main.js

document.addEventListener('DOMContentLoaded', () => {
    // 1. Cập nhật đồng hồ thời gian thực
    const clockElement = document.getElementById('live-clock');
    
    function updateClock() {
        const now = new Date();
        const timeString = now.toLocaleTimeString('vi-VN', { hour12: false });
        clockElement.textContent = timeString;
    }
    
    setInterval(updateClock, 1000);
    updateClock(); // Chạy ngay lần đầu

    // 2. Xử lý đổi IP Camera
    const btnUpdateCam = document.getElementById('btn-update-cam');
    const inputCamIp = document.getElementById('camera-ip');
    const videoStream = document.getElementById('video-stream');
    
    btnUpdateCam.addEventListener('click', () => {
        const newUrl = inputCamIp.value;
        
        // Thêm hiệu ứng loading vào nút
        const originalText = btnUpdateCam.innerText;
        btnUpdateCam.innerText = "Đang cập nhật...";
        btnUpdateCam.disabled = true;

        // Gửi request lên server
        fetch('/update_camera', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ url: newUrl })
        })
        .then(response => response.json())
        .then(data => {
            if(data.status === 'success') {
                // Để reload lại ảnh stream, ta gán lại src và thêm timestamp để tránh cache
                videoStream.src = "/video_feed?" + new Date().getTime();
                
                // Trả lại trạng thái nút
                setTimeout(() => {
                    btnUpdateCam.innerText = "Đã cập nhật ✓";
                    btnUpdateCam.style.background = "var(--success)";
                    
                    setTimeout(() => {
                        btnUpdateCam.innerText = originalText;
                        btnUpdateCam.style.background = "";
                        btnUpdateCam.disabled = false;
                    }, 2000);
                }, 500);
            }
        })
        .catch(err => {
            console.error("Lỗi:", err);
            btnUpdateCam.innerText = "Lỗi! Thử lại";
            btnUpdateCam.style.background = "var(--danger)";
            setTimeout(() => {
                btnUpdateCam.innerText = originalText;
                btnUpdateCam.style.background = "";
                btnUpdateCam.disabled = false;
            }, 2000);
        });
    });
});
