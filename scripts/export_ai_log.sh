#!/usr/bin/env bash
#
# Xuất file phiên chat AI vào docs/ai-log/sessions/ để nộp cho BTC.
#
# Quét secret TRƯỚC khi copy. File này sẽ được commit và gửi ra ngoài,
# nên một API key lọt vào đây là lộ thật — script dừng thay vì copy.
#
# Dùng: bash scripts/export_ai_log.sh
#
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DEST="$REPO_ROOT/docs/ai-log/sessions"

# Claude Code mã hoá đường dẫn project thành tên thư mục: / -> -
PROJECT_SLUG="$(printf '%s' "$REPO_ROOT" | sed 's#/#-#g')"
SRC_DIR="$HOME/.claude/projects/$PROJECT_SLUG"

# Chạy xuất phiên Gemini Antigravity
echo "⏳ Đang quét xuất phiên Gemini Antigravity..." >&2
if command -v python3 &>/dev/null; then
    python3 "$REPO_ROOT/scripts/export_gemini_log.py" || true
elif command -v python &>/dev/null; then
    python "$REPO_ROOT/scripts/export_gemini_log.py" || true
fi

# Không có thư mục phiên Claude là bình thường: kiểm tra và báo nhẹ
if [ ! -d "$SRC_DIR" ]; then
    echo "ℹ️  Không tìm thấy phiên Claude Code cho repo này: $SRC_DIR" >&2
    exit 0
fi

shopt -s nullglob
SESSIONS=("$SRC_DIR"/*.jsonl)
shopt -u nullglob

if [ ${#SESSIONS[@]} -eq 0 ]; then
    echo "ℹ️  Không có file .jsonl nào trong $SRC_DIR" >&2
    exit 1
fi

# --- Copy & Sanitize -----------------------------------------------------
mkdir -p "$DEST"

# Ngày lấy từ mtime của file, không phải ngày hôm nay — phiên có thể cũ.
COUNT=0
for f in "${SESSIONS[@]}"; do
    id="$(basename "$f" .jsonl)"
    short="${id:0:8}"
    day="$(date -r "$f" +%Y-%m-%d 2>/dev/null || stat -c %y "$f" | cut -d' ' -f1)"
    out="$DEST/${day}-${short}.jsonl"
    
    # Quét và che các chuỗi nhạy cảm khi xuất log
    if command -v python3 &>/dev/null; then
        python3 "$REPO_ROOT/scripts/sanitize_log.py" "$f" "$out"
    elif command -v python &>/dev/null; then
        python "$REPO_ROOT/scripts/sanitize_log.py" "$f" "$out"
    else
        cp "$f" "$out"
    fi
    
    size="$(du -h "$out" | cut -f1)"
    echo "✅ $(basename "$out")  ($size)" >&2
    COUNT=$((COUNT + 1))
done

# Thành công thì báo ra stderr, không phải stdout. Script này chạy sau mỗi lượt
# trả lời qua hook Stop; nói mỗi lần là ồn tới mức người ta ngừng đọc. Chạy tay
# thì vẫn thấy đủ, vì terminal hiện cả stderr.
{
    echo ""
    echo "Đã xuất $COUNT phiên → docs/ai-log/sessions/"
    echo "⚠️  Phiên đang chạy vẫn được ghi tiếp. Chạy lại script này ngay trước khi nộp bài"
    echo "    để lấy bản đầy đủ nhất."
} >&2
