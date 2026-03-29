"""
download_dataset.py
-------------------
Downloads the NSL-KDD dataset (KDDTrain+.txt and KDDTest+.txt)
from the publicly available GitHub mirror and saves them to ./data/.
Run once before training: python download_dataset.py
"""

import os
import urllib.request

# Mirror URLs for NSL-KDD dataset
URLS = {
    "KDDTrain+.txt": "https://raw.githubusercontent.com/defcom17/NSL_KDD/master/KDDTrain%2B.txt",
    "KDDTest+.txt":  "https://raw.githubusercontent.com/defcom17/NSL_KDD/master/KDDTest%2B.txt",
}

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")


def download():
    os.makedirs(DATA_DIR, exist_ok=True)
    for filename, url in URLS.items():
        dest = os.path.join(DATA_DIR, filename)
        if os.path.exists(dest):
            print(f"[SKIP] {filename} already exists.")
            continue
        print(f"[DOWNLOAD] Fetching {filename} ...")
        try:
            urllib.request.urlretrieve(url, dest)
            print(f"[OK] Saved to {dest}")
        except Exception as e:
            print(f"[ERROR] Failed to download {filename}: {e}")
            print("  Please download manually from:")
            print("  https://github.com/defcom17/NSL_KDD")


if __name__ == "__main__":
    download()
