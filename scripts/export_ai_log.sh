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

# Không có thư mục phiên là chuyện bình thường: đồng đội có thể dùng Codex,
# Cursor, hay công cụ khác. Báo ra stderr rồi thoát êm — script này chạy trong
# hook Stop, không được làm ồn hay chặn lượt trả lời của ai.
if [ ! -d "$SRC_DIR" ]; then
    {
        echo "ℹ️  Không tìm thấy phiên Claude Code cho repo này: $SRC_DIR"
        echo "   Dùng công cụ AI khác? Xuất log thủ công và bỏ vào docs/ai-log/sessions/,"
        echo "   rồi khai báo trong docs/ai-log/tools-used.md"
    } >&2
    exit 1
fi

shopt -s nullglob
SESSIONS=("$SRC_DIR"/*.jsonl)
shopt -u nullglob

if [ ${#SESSIONS[@]} -eq 0 ]; then
    echo "ℹ️  Không có file .jsonl nào trong $SRC_DIR" >&2
    exit 1
fi

# --- Quét secret ---------------------------------------------------------
# Ảnh dán vào chat được nhúng dạng base64 ngay trong file phiên. Base64 ngẫu
# nhiên chắc chắn sẽ khớp mọi mẫu key (một ảnh 250KB đủ sinh ra "AIza…" tình
# cờ), nên quét thẳng bằng grep là báo động giả 100%. Phải bóc ảnh ra trước.
FOUND_SECRET=0
for f in "${SESSIONS[@]}"; do
    if ! python3 "$REPO_ROOT/scripts/scan_secrets.py" "$f"; then
        FOUND_SECRET=1
    fi
done

if [ $FOUND_SECRET -eq 1 ]; then
    # In ra stderr VÀ trả JSON systemMessage ra stdout, để khi chạy trong hook
    # Stop thì cảnh báo vẫn hiện lên. Bị chặn mà im lặng là tệ nhất: người dùng
    # tưởng log đã được cập nhật.
    {
        echo ""
        echo "❌ DỪNG — không copy gì cả."
        echo "   File phiên chứa thứ trông giống API key. Nếu commit là lộ ra ngoài."
        echo "   Xử lý: là key thật thì thu hồi ngay rồi xoá/che trong file phiên;"
        echo "   là giá trị vô hại thì thêm hash vào docs/ai-log/.secret-allowlist."
    } >&2
    printf '{"systemMessage":"⚠️  AI log KHÔNG được cập nhật: phát hiện secret trong file phiên. Chạy `bash scripts/export_ai_log.sh` để xem chi tiết."}\n'
    exit 1
fi

# --- Copy ----------------------------------------------------------------
mkdir -p "$DEST"

# Ngày lấy từ mtime của file, không phải ngày hôm nay — phiên có thể cũ.
COUNT=0
for f in "${SESSIONS[@]}"; do
    id="$(basename "$f" .jsonl)"
    short="${id:0:8}"
    day="$(date -r "$f" +%Y-%m-%d 2>/dev/null || stat -c %y "$f" | cut -d' ' -f1)"
    out="$DEST/${day}-${short}.jsonl"
    cp "$f" "$out"
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
