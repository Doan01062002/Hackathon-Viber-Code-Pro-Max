#!/bin/bash
# Script tự động deploy Frontend Next.js lên cùng VPS không dùng quyền root (cổng 3000)

set -e

echo "=== [1/4] Kiểm tra và tự động cài đặt Node.js qua NVM ==="
# Load NVM nếu đã cài sẵn
export NVM_DIR="$HOME/.nvm"
[ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"

if ! command -v node &> /dev/null; then
    echo "Không tìm thấy Node.js. Tiến hành cài đặt NVM và Node.js cục bộ..."
    curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.7/install.sh | bash
    
    # Kích hoạt NVM lập tức trong session này
    export NVM_DIR="$HOME/.nvm"
    [ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"
    
    nvm install 20
    nvm use 20
    echo "Cài đặt Node.js $(node -v) thành công!"
else
    echo "Node.js đã được cài đặt: $(node -v)"
fi

echo "=== [2/4] Tạo cấu hình môi trường cho Frontend ==="
cd frontend
cat << 'EOF' > .env.production
NEXT_PUBLIC_API_URL="http://136.116.96.142:8000"
EOF
echo "Đã cấu hình API Gateway của Backend trỏ về: http://136.116.96.142:8000"

echo "=== [3/4] Cài đặt gói thư viện & Build Next.js ==="
npm install
npm run build

echo "=== [4/4] Khởi chạy Frontend ngầm dưới cổng 3000 ==="
# Tắt tiến trình cũ đang chạy trên cổng 3000 (nếu có)
kill -9 $(lsof -t -i:3000) 2>/dev/null || true

# Chạy ngầm Next.js bằng nohup trên cổng 3000
nohup npm run start -- -p 3000 > ../nextjs.log 2>&1 &

echo "Đợi 5 giây để Next.js khởi động..."
sleep 5

echo "=================================================="
echo "🎉 TRIỂN KHAI FRONTEND THÀNH CÔNG!"
echo "Địa chỉ truy cập Website: http://136.116.96.142:3000"
echo "=================================================="
