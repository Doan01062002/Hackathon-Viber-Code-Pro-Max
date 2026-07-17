import sys
import types
import hashlib

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
