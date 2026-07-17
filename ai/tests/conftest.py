import hashlib
import os
import sys
import types

# ai_service/ nằm cạnh src/ (chưa phải package cài đặt qua pyproject.toml `where=["src"]`),
# nên test cần tự thêm thư mục ai/ vào sys.path để `import ai_service` hoạt động —
# giống cách scripts/train.py đã làm.
_AI_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if _AI_DIR not in sys.path:
    sys.path.insert(0, _AI_DIR)


class MockXXHash:
    def __init__(self, data=b""):
        self.data = data

    def digest(self):
        return hashlib.md5(self.data).digest()

    def hexdigest(self):
        return hashlib.md5(self.data).hexdigest()


def xxh3_128(data=b"", seed=0):
    if isinstance(data, str):
        data = data.encode()
    return MockXXHash(data)


def xxh3_128_hexdigest(data, seed=0):
    if isinstance(data, str):
        data = data.encode()
    return hashlib.md5(data).hexdigest()


# Tạo Module thật để có thể import các hàm từ nó
xxhash_mock = types.ModuleType("xxhash")
xxhash_mock.xxh3_128 = xxh3_128
xxhash_mock.xxh3_128_hexdigest = xxh3_128_hexdigest

sys.modules["xxhash"] = xxhash_mock
