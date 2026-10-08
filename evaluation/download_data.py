"""Download the evaluation dataset (UpdatedResumeDataSet.csv) into data/raw/.

It is the widely used public Kaggle "Resume Dataset" file (962 resumes in 25
job categories). This script fetches it from a public Hugging Face mirror, so
no Kaggle login is needed, and checks its SHA-256 fingerprint so every run is
measured on exactly the same file.

Run:  python -m evaluation.download_data
"""
import hashlib
import urllib.request
from pathlib import Path

URL = "https://huggingface.co/datasets/Unknown92/Resume_dataset/resolve/main/UpdatedResumeDataSet.csv"
SHA256 = "5c07cb96644e62c1e91e0f7c74118eb63a6a742b0c84f96c76beb2b8688a2ff1"
TARGET = Path(__file__).resolve().parent.parent / "data" / "raw" / "UpdatedResumeDataSet.csv"


def main():
    TARGET.parent.mkdir(parents=True, exist_ok=True)
    if not TARGET.exists():
        print(f"Downloading {URL}")
        urllib.request.urlretrieve(URL, TARGET)
    digest = hashlib.sha256(TARGET.read_bytes()).hexdigest()
    if digest != SHA256:
        raise SystemExit(f"{TARGET} is not the file the published results were measured on (checksum mismatch).")
    print(f"OK: {TARGET} ({TARGET.stat().st_size:,} bytes, checksum verified)")


if __name__ == "__main__":
    main()
