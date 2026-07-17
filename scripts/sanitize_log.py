#!/usr/bin/env python3
import sys
from pathlib import Path

# Thêm thư mục scripts vào sys.path để import scan_secrets
SCRIPTS_DIR = Path(__file__).resolve().parent
sys.path.append(str(SCRIPTS_DIR))

try:
    import scan_secrets
except ImportError:
    print("❌ Lỗi: Không tìm thấy scan_secrets.py trong thư mục scripts.", file=sys.stderr)
    sys.exit(1)

def sanitize(input_path, output_path):
    """Quét và che các chuỗi nhạy cảm (secrets) trước khi copy sang thư mục xuất log."""
    findings = scan_secrets.scan(input_path)
    
    # Đọc tệp nguồn
    with open(input_path, "r", encoding="utf-8", errors="replace") as fh:
        content = fh.read()

    if findings:
        import json
        # Sắp xếp các phát hiện theo độ dài chuỗi giảm dần để tránh thay thế một phần
        sorted_findings = sorted(findings, key=lambda x: len(x[2]), reverse=True)
        
        # Tạo danh sách các chuỗi đã xử lý để tránh thay thế lặp lại
        replaced = set()
        for lineno, kind, val in sorted_findings:
            if val in replaced:
                continue
            replaced.add(val)
            
            # Tạo chuỗi đã che (Masked)
            if len(val) > 8:
                masked = f"{val[:4]}...{val[-4:]}_REDACTED"
            else:
                masked = "REDACTED"
            
            # Thay thế cả bản thường (unescaped) và bản đã escape trong JSON
            content = content.replace(val, masked)
            
            escaped_val = json.dumps(val)[1:-1]
            escaped_masked = json.dumps(masked)[1:-1]
            content = content.replace(escaped_val, escaped_masked)
            
    # Ghi ra tệp đích
    with open(output_path, "w", encoding="utf-8") as fh:
        fh.write(content)

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Dùng: python sanitize_log.py <input_file> <output_file>", file=sys.stderr)
        sys.exit(1)
    sanitize(sys.argv[1], sys.argv[2])
