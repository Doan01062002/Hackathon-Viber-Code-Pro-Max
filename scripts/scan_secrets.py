#!/usr/bin/env python3
"""Quét secret trong file phiên chat AI (.jsonl) trước khi commit.

Ảnh dán vào chat nằm trong file dưới dạng base64. Chuỗi base64 đủ dài sẽ tình
cờ chứa mọi tiền tố key ta đi tìm — một ảnh 250KB sinh ra "AIza…" là chuyện
bình thường. Nên bóc hết blob base64 ra rồi mới quét phần văn bản còn lại.

Chuỗi đã review và xác nhận vô hại được bỏ qua qua allowlist SHA-256
(docs/ai-log/.secret-allowlist). Lưu hash, không lưu giá trị — allowlist nằm
trong git nên không được chứa thứ ta đang cố giấu.

Dùng:
    scan_secrets.py <file.jsonl>              quét
    scan_secrets.py <file.jsonl> --print-hashes   in hash để bỏ vào allowlist

Exit 0 = sạch, exit 1 = có secret.
"""

import hashlib
import json
import re
import sys
from pathlib import Path

# Mẫu key của các nhà cung cấp phổ biến. Chỉ áp lên văn bản, không áp lên base64.
PATTERNS = {
    "OpenAI": re.compile(r"\bsk-(?:proj-)?[A-Za-z0-9_-]{20,}"),
    "Anthropic": re.compile(r"\bsk-ant-[A-Za-z0-9_-]{20,}"),
    "GitHub token": re.compile(r"\b(?:ghp|gho|ghu|ghs)_[A-Za-z0-9]{36}\b"),
    "GitHub PAT": re.compile(r"\bgithub_pat_\w{60,}\b"),
    "AWS access key": re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    "Google API key": re.compile(r"\bAIza[A-Za-z0-9_-]{35}\b"),
    "Slack token": re.compile(r"\bxox[baprs]-[A-Za-z0-9-]{10,}"),
    "Private key": re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
}

# Dòng .env kiểu FOO_API_KEY=<giá trị thật>. Bỏ qua placeholder.
ENV_ASSIGN = re.compile(
    r"\b([A-Z][A-Z0-9_]*(?:API_KEY|SECRET|TOKEN|PASSWORD))\s*=\s*([^\s\"',]{8,})"
)
PLACEHOLDER = re.compile(
    r"^(your|xxx|\.\.\.|<|\$\{|changeme|placeholder|dummy|example|sk-\.\.\.)",
    re.IGNORECASE,
)


def is_media_block(o):
    """Block ảnh/tài liệu: {"type":"image","source":{"data":"<base64>"}}"""
    return o.get("type") in ("image", "document") and isinstance(o.get("source"), dict)


def is_raw_blob(key, value):
    """Base64 trần dưới khoá "data"."""
    return key == "data" and isinstance(value, str) and len(value) > 500


def strip_blobs(obj):
    """Trả về text của node, bỏ mọi base64 ảnh/tài liệu."""
    out = []
    stack = [obj]
    while stack:
        o = stack.pop()
        if isinstance(o, dict):
            if is_media_block(o):
                continue  # bỏ cả nhánh
            stack.extend(v for k, v in o.items() if not is_raw_blob(k, v))
        elif isinstance(o, list):
            stack.extend(o)
        elif isinstance(o, str):
            out.append(o)
    return "\n".join(out)


ALLOWLIST_PATH = (
    Path(__file__).resolve().parent.parent / "docs" / "ai-log" / ".secret-allowlist"
)


def digest(value):
    return hashlib.sha256(value.encode()).hexdigest()


def load_allowlist():
    """Đọc SHA-256 đã duyệt. Bỏ dòng trống và comment."""
    if not ALLOWLIST_PATH.exists():
        return set()
    allowed = set()
    for line in ALLOWLIST_PATH.read_text(encoding="utf-8").splitlines():
        line = line.split("#", 1)[0].strip()
        if line:
            allowed.add(line.lower())
    return allowed


def scan(path):
    findings = []
    with open(path, "r", encoding="utf-8", errors="replace") as fh:
        for lineno, line in enumerate(fh, 1):
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except json.JSONDecodeError:
                continue
            text = strip_blobs(obj)

            for name, pat in PATTERNS.items():
                for m in pat.findall(text):
                    findings.append((lineno, name, m))

            for var, val in ENV_ASSIGN.findall(text):
                if not PLACEHOLDER.match(val):
                    findings.append((lineno, f"gán biến {var}", val))
    return findings


def dedupe(findings, key):
    """Bỏ trùng, giữ nguyên thứ tự."""
    seen, out = set(), []
    for f in findings:
        k = key(f)
        if k not in seen:
            seen.add(k)
            out.append(f)
    return out


def report_hashes(findings, name):
    print(f"# SHA-256 các phát hiện trong {name}")
    print("# Review từng dòng, xoá dòng nào là key THẬT (đi thu hồi key đó),")
    print("# rồi chép phần còn lại vào docs/ai-log/.secret-allowlist")
    for lineno, kind, value in dedupe(findings, lambda f: digest(f[2])):
        print(f"{digest(value)}  # {kind} (dòng {lineno})")


def report_blocking(blocking, name, note, path):
    # Ra stderr: caller (export_ai_log.sh) giữ stdout cho JSON hook.
    err = sys.stderr
    print(f"🚨 PHÁT HIỆN SECRET trong: {name}{note}", file=err)
    for lineno, kind, value in dedupe(blocking, lambda f: (f[1], f[2])):
        masked = value[:6] + "…(đã cắt)" if len(value) > 6 else "…"
        print(f"     dòng {lineno}: {kind} → {masked}", file=err)
    print("", file=err)
    print("   Nếu là key THẬT: thu hồi key đó ngay, rồi xoá/che trong file phiên.", file=err)
    print("   Nếu vô hại (key mẫu, ví dụ trong tài liệu): lấy hash bằng", file=err)
    print(f"     python3 scripts/scan_secrets.py {path} --print-hashes", file=err)
    print("   rồi thêm vào docs/ai-log/.secret-allowlist", file=err)


def main():
    args = sys.argv[1:]
    if not args or len(args) > 2:
        print("Dùng: scan_secrets.py <file.jsonl> [--print-hashes]", file=sys.stderr)
        return 2

    path = args[0]
    name = path.rsplit("/", 1)[-1]
    findings = scan(path)

    if "--print-hashes" in args:
        report_hashes(findings, name)
        return 0

    allowed = load_allowlist()
    blocking = [f for f in findings if digest(f[2]) not in allowed]
    skipped = len(findings) - len(blocking)
    note = f" ({skipped} mục đã duyệt trong allowlist)" if skipped else ""

    if not blocking:
        print(f"🔍 Sạch: {name}{note}", file=sys.stderr)
        return 0

    report_blocking(blocking, name, note, path)
    return 1


if __name__ == "__main__":
    sys.exit(main())
