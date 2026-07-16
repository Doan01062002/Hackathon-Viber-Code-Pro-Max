#!/usr/bin/env bash
# Kiểm tra ranh giới giữa các module. Chạy trong CI và bằng `make boundaries`.
#
# Quy tắc:
#   1. ai/ không được biết backend tồn tại  (chiều phụ thuộc chỉ là backend -> ai)
#   2. Chỉ services/ được import ai         (controller/model/view không chạm agent)
#   3. Chỉ lib/api/ được gọi fetch()        (feature FE đi qua apiClient)

set -uo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

failed=0

fail() {
  echo "❌ $1"
  failed=1
}

# --- 1. ai/ không được import backend ---
if grep -rnE '^\s*(from|import)\s+backend' ai/src ai/tests 2>/dev/null; then
  fail "ai/ import backend — phá chiều phụ thuộc (chỉ được backend -> ai)"
else
  echo "✅ ai/ không phụ thuộc backend"
fi

# --- 2. Trong backend, chỉ services/ được import ai ---
leaks=$(grep -rnE '^\s*(from|import)\s+ai(\.|\s|$)' backend/src/backend \
  --include='*.py' 2>/dev/null | grep -v '/services/' || true)
if [ -n "$leaks" ]; then
  echo "$leaks"
  fail "controller/model/view import ai trực tiếp — phải đi qua services/"
else
  echo "✅ chỉ backend/services/ import ai"
fi

# --- 3. FE: chỉ lib/api/ được gọi fetch() ---
if [ -d frontend/src ]; then
  raw_fetch=$(grep -rn 'fetch(' frontend/src \
    --include='*.ts' --include='*.tsx' 2>/dev/null | grep -v 'src/lib/api/' || true)
  if [ -n "$raw_fetch" ]; then
    echo "$raw_fetch"
    fail "gọi fetch() ngoài lib/api/ — phải đi qua apiClient"
  else
    echo "✅ FE chỉ gọi HTTP qua lib/api/"
  fi
fi

if [ "$failed" -ne 0 ]; then
  echo ""
  echo "Ranh giới module bị vi phạm. Xem ARCHITECTURE.md."
  exit 1
fi

echo ""
echo "Tất cả ranh giới module hợp lệ."
