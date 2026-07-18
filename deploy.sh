#!/bin/bash
# Script tự động deploy Backend lên VPS Ubuntu chạy cổng 80

set -e

echo "=== [1/5] Cập nhật hệ thống & cài đặt thư viện hệ thống ==="
sudo apt update
sudo apt install -y python3.11 python3.11-venv python3-pip git curl

echo "=== [2/5] Tạo file môi trường .env ==="
cat << 'EOF' > .env
DATABASE_URL="postgresql+psycopg://appadmin:dtkien2003@viber-coding-pro-max-db.czciyckimjww.ap-southeast-1.rds.amazonaws.com:5432/viber_coding_pro_max?sslmode=require"
EOF
echo "Đã tạo xong file .env kết nối RDS PostgreSQL."

echo "=== [3/5] Tạo và thiết lập Python Virtual Environment ==="
python3.11 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip

echo "=== [4/5] Cài đặt dependencies (ai + backend) ==="
pip install -r requirements.txt

echo "=== [5/5] Khởi chạy Backend ngầm dưới cổng 80 ==="
# Kiểm tra nếu cổng 80 đã bị chiếm, tắt tiến trình cũ đi
sudo kill -9 $(sudo lsof -t -i:80) 2>/dev/null || true

# Chạy ngầm uvicorn bằng nohup
sudo nohup .venv/bin/uvicorn backend.main:app --host 0.0.0.0 --port 80 > uvicorn.log 2>&1 &

echo "Đợi 3 giây kiểm tra trạng thái máy chủ..."
sleep 3

if curl -s http://localhost/health | grep -q "ok"; then
    echo "=================================================="
    echo "🎉 TRIỂN KHAI BACKEND THÀNH CÔNG!"
    echo "Địa chỉ truy cập API Docs: http://136.116.96.142/docs"
    echo "Địa chỉ truy cập Healthcheck: http://136.116.96.142/health"
    echo "=================================================="
else
    echo "❌ Có lỗi xảy ra khi khởi động. Vui lòng xem log tại uvicorn.log:"
    cat uvicorn.log
fi
