# Script tự động deploy Backend lên VPS Ubuntu không dùng quyền root (cổng 8000)

set -e

# Bỏ qua kiểm tra môi trường quản lý bên ngoài (PEP 668) trên Ubuntu đời mới
export PIP_BREAK_SYSTEM_PACKAGES=1


echo "=== [1/4] Tạo file môi trường .env ==="
cat << 'EOF' > .env
DATABASE_URL="postgresql+psycopg://appadmin:dtkien2003@viber-coding-pro-max-db.czciyckimjww.ap-southeast-1.rds.amazonaws.com:5432/viber_coding_pro_max?sslmode=require"
EOF
echo "Đã tạo xong file .env kết nối RDS PostgreSQL."

echo "=== [2/4] Kiểm tra và tự động cài đặt pip cho User ==="
# Kiểm tra nếu python3 -m pip hoạt động, nếu không thì tự cài pip cho user
if ! python3 -m pip --version >/dev/null 2>&1; then
    echo "pip không tìm thấy. Đang tải và cài đặt pip cục bộ..."
    curl -sS https://bootstrap.pypa.io/get-pip.py -o get-pip.py
    python3 get-pip.py --user
    rm get-pip.py
fi

# Cài đặt toàn bộ gói thư viện trực tiếp vào user space thông qua python3 -m pip
python3 -m pip install --user --upgrade pip || echo "Bỏ qua nâng cấp pip"
python3 -m pip install --user -r requirements.txt

echo "=== [2.5/4] Kiểm tra và cấu hình libgomp.so.1 cho LightGBM ==="
mkdir -p $HOME/local_libs
if [ ! -f "$HOME/local_libs/libgomp.so.1" ]; then
    echo "Tự động tải và giải nén libgomp1 cục bộ..."
    TEMP_DIR=$(mktemp -d)
    cd "$TEMP_DIR"
    apt-get download libgomp1 || true
    # Giải nén package deb
    dpkg -x libgomp1_*.deb . || true
    # Tìm file libgomp.so.1 và copy về thư mục cố định
    GOMP_FILE=$(find . -name "libgomp.so.1" | head -n 1)
    if [ -n "$GOMP_FILE" ]; then
        cp "$GOMP_FILE" "$HOME/local_libs/"
        echo "Đã cấu hình xong libgomp.so.1 tại $HOME/local_libs"
    else
        echo "⚠️ Không tìm thấy libgomp.so.1 trong file tải về."
    fi
    cd - >/dev/null
    rm -rf "$TEMP_DIR"
fi

# Thiết lập LD_LIBRARY_PATH để Python có thể gọi thư viện này
export LD_LIBRARY_PATH="$HOME/local_libs:$LD_LIBRARY_PATH"



echo "=== [3/4] Khởi chạy Backend ngầm dưới cổng 8000 ==="
# Tắt tiến trình cũ đang chạy trên cổng 8000 (nếu có)
kill -9 $(lsof -t -i:8000) 2>/dev/null || true

# Chạy ngầm uvicorn bằng nohup trên cổng 8000 thông qua module python3
nohup python3 -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 > uvicorn.log 2>&1 &

echo "=== [4/4] Đợi 3 giây kiểm tra trạng thái máy chủ ==="
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


