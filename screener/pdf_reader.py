"""Step 1 - get the plain text out of a resume file.

PDFs are read with PyMuPDF, the same library the first Colab version used
(older code imports it under its old name, `fitz`). Plain .txt files are read
as they are - that is how the evaluation dataset, which is already text, goes
through exactly the same pipeline.

Files can come from disk (the command line) or from memory (an upload in the
web app); both end up in text_from_bytes().
"""
from pathlib import Path

import pymupdf

SUPPORTED_TYPES = {".pdf", ".txt"}


def text_from_bytes(filename, data):
    """All the text in a .pdf or .txt file, given its name and its raw bytes."""
    kind = Path(filename).suffix.lower()
    if kind == ".txt":
        return data.decode("utf-8", errors="replace")
    if kind == ".pdf":
        with pymupdf.open(stream=data, filetype="pdf") as pdf:
            return "\n".join(page.get_text() for page in pdf)
    raise ValueError(f"{filename}: only .pdf and .txt resumes are supported")


def read_resume(path):
    """All the text in a .pdf or .txt resume on disk."""
    path = Path(path)
    return text_from_bytes(path.name, path.read_bytes())


def find_resumes(folder):
    """Every .pdf and .txt file in a folder, alphabetically, so runs are repeatable."""
    return sorted(p for p in Path(folder).iterdir() if p.suffix.lower() in SUPPORTED_TYPES)
