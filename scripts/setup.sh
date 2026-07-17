#!/bin/bash
# Dựng môi trường dev cho cả 3 module.

set -e

echo "=== Project Setup ==="

# Check Python version
python3 -c "import sys; assert sys.version_info >= (3, 11), 'Python 3.11+ required'"
echo "Python version OK"

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Cài 2 package Python (ai + backend) ở chế độ editable
pip install -r requirements.txt

# Cài dependencies frontend
if command -v npm > /dev/null; then
    (cd frontend && npm install)
else
    echo "⚠️  Không tìm thấy npm — bỏ qua frontend."
    echo "    Cài Node 20+ rồi chạy: cd frontend && npm install"
fi

# Create .env if not exists
if [ ! -f .env ]; then
    cp .env.example .env
    echo "Created .env — please edit with your API keys"
fi

# Create data directories
mkdir -p data/chroma

echo ""
echo "Setup complete!"
echo "  Backend:  make run      -> http://localhost:8000/docs"
echo "  Frontend: make run-fe   -> http://localhost:3000/chat"
