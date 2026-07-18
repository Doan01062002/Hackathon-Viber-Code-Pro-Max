# Script tự động deploy Backend lên VPS Ubuntu không dùng quyền root (cổng 8000)

set -e

echo "=== [1/4] Tạo file môi trường .env ==="
cat << 'EOF' > .env
DATABASE_URL="postgresql+psycopg://appadmin:dtkien2003@viber-coding-pro-max-db.czciyckimjww.ap-southeast-1.rds.amazonaws.com:5432/viber_coding_pro_max?sslmode=require"
EOF
echo "Đã tạo xong file .env kết nối RDS PostgreSQL."

echo "=== [2/4] Tạo và thiết lập Python Virtual Environment ==="
# Thử tạo virtual environment bằng python3 mặc định của hệ thống
python3 -m venv .venv || {
    echo "Không tạo được venv. Đang cài đặt venv không dùng sudo..."
    apt install python3-venv --user || exit 1
    python3 -m venv .venv
}
source .venv/bin/activate
pip install --upgrade pip

echo "=== [3/4] Cài đặt dependencies (ai + backend) ==="
pip install -r requirements.txt

echo "=== [4/4] Khởi chạy Backend ngầm dưới cổng 8000 ==="
# Tắt tiến trình cũ đang chạy trên cổng 8000 (nếu có)
kill -9 $(lsof -t -i:8000) 2>/dev/null || true

# Chạy ngầm uvicorn bằng nohup trên cổng 8000
nohup .venv/bin/uvicorn backend.main:app --host 0.0.0.0 --port 8000 > uvicorn.log 2>&1 &

echo "Đợi 3 giây kiểm tra trạng thái máy chủ..."
sleep 3

if curl -s http://localhost:8000/health | grep -q "ok"; then
    echo "=================================================="
    echo "🎉 TRIỂN KHAI BACKEND THÀNH CÔNG!"
    echo "Địa chỉ truy cập nội bộ: http://localhost:8000"
    echo "=================================================="
else
    echo "❌ Có lỗi xảy ra khi khởi động. Vui lòng xem log tại uvicorn.log:"
    cat uvicorn.log
fi

