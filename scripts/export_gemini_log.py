#!/usr/bin/env python3
"""Xuất file phiên chat Gemini Antigravity IDE vào docs/ai-log/sessions/.

Tự động tìm kiếm thư mục phiên của Antigravity có tương tác với repo này,
quét secret bằng scan_secrets.py, và copy vào docs/ai-log/sessions/.
"""

import sys
import os
import shutil
import hashlib
from datetime import datetime
from pathlib import Path

# Thêm thư mục scripts vào sys.path để import scan_secrets
SCRIPTS_DIR = Path(__file__).resolve().parent
sys.path.append(str(SCRIPTS_DIR))

try:
    import scan_secrets
except ImportError:
    print("❌ Lỗi: Không tìm thấy scan_secrets.py trong thư mục scripts.", file=sys.stderr)
    sys.exit(1)


def find_gemini_sessions(repo_root):
    """Tìm tất cả các tệp log Gemini Antigravity có liên quan đến repo này."""
    home = Path.expanduser(Path("~"))
    brain_dir = home / ".gemini" / "antigravity-ide" / "brain"
    
    if not brain_dir.exists():
        return []

    repo_root_slug = str(repo_root).replace("\\", "/").lower()
    matched_sessions = []

    # Duyệt qua các thư mục phiên trong brain/
    for conv_dir in brain_dir.iterdir():
        if not conv_dir.is_dir():
            continue
        
        # Log của Antigravity lưu ở .system_generated/logs/
        log_file = conv_dir / ".system_generated" / "logs" / "transcript_full.jsonl"
        if not log_file.exists():
            log_file = conv_dir / ".system_generated" / "logs" / "transcript.jsonl"
            
        if not log_file.exists():
            continue

        # Kiểm tra xem phiên này có tương tác với repo này không
        try:
            content = log_file.read_text(encoding="utf-8", errors="ignore").lower()
            if repo_root_slug in content:
                matched_sessions.append((conv_dir.name, log_file))
        except Exception:
            continue

    return matched_sessions


def main():
    repo_root = Path(__file__).resolve().parent.parent
    dest_dir = repo_root / "docs" / "ai-log" / "sessions"
    
    sessions = find_gemini_sessions(repo_root)
    
    if not sessions:
        print("ℹ️  Không tìm thấy phiên Gemini Antigravity nào liên quan đến repo này.", file=sys.stderr)
        return 0

    dest_dir.mkdir(parents=True, exist_ok=True)
    copied_count = 0

    import sanitize_log

    for conv_id, log_path in sessions:
        # Lấy ngày sửa đổi cuối cùng của file log
        mtime = os.path.getmtime(log_path)
        day = datetime.fromtimestamp(mtime).strftime("%Y-%m-%d")
        
        short_id = conv_id[:8]
        out_name = f"{day}-gemini-{short_id}.jsonl"
        out_path = dest_dir / out_name

        # Quét và che các chuỗi nhạy cảm khi xuất log
        sanitize_log.sanitize(log_path, out_path)
        
        # Lấy dung lượng file
        size_kb = os.path.getsize(out_path) / 1024
        print(f"✅ {out_name}  ({size_kb:.1f} KB)", file=sys.stderr)
        copied_count += 1

    if copied_count > 0:
        print(f"\nĐã xuất {copied_count} phiên Gemini → docs/ai-log/sessions/", file=sys.stderr)
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
