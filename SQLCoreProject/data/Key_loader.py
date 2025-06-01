import os

def load_key():
    path = os.path.join(os.getenv("USERPROFILE") or os.getenv("HOME"), ".tns_key")
    return open(path, "rb").read().ljust(32, b'0')  # 키가 짧으면 오른쪽 0으로 채움