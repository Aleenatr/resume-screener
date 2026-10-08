import re
import urllib.parse
from pathlib import Path

import numpy as np
from fastapi.testclient import TestClient

from screener.web import app, get_encoder

FIXTURES = Path(__file__).parent / "fixtures"
SAMPLE_PDF = Path(__file__).parent.parent / "examples" / "resumes" / "ananya_rao.pdf"


def fake_encode(texts):  # stands in for the model so the tests need no download
    return np.array([[1.0, 0.1] if "hadoop" in t.lower() else [0.1, 1.0] for t in texts])


app.dependency_overrides[get_encoder] = lambda: fake_encode
client = TestClient(app)
JOB = "Hadoop developer: Hive, Spark, Sqoop."


def uploads(*paths):
    return [("resumes", (p.name, p.read_bytes(), "application/octet-stream")) for p in paths]


def test_home_page_shows_the_upload_form():
    page = client.get("/")
    assert page.status_code == 200
    assert 'name="job_description"' in page.text and 'name="resumes"' in page.text


def test_api_ranks_the_uploaded_resumes():
    response = client.post("/api/screen", data={"job_description": JOB}, files=uploads(*sorted(FIXTURES.glob("*.txt"))))
    assert response.status_code == 200
    results = response.json()["results"]
    assert [r["file"] for r in results] == ["hadoop_engineer.txt", "java_developer.txt"]
    assert results[0]["missing_skills"] == ["Sqoop"]


def test_results_page_lists_candidates_best_first():
    page = client.post("/screen", data={"job_description": JOB}, files=uploads(*sorted(FIXTURES.glob("*.txt"))))
    assert page.status_code == 200
    assert page.text.index("hadoop_engineer.txt") < page.text.index("java_developer.txt")


def test_reads_real_pdf_uploads_in_memory():
    results = client.post("/api/screen", data={"job_description": JOB}, files=uploads(SAMPLE_PDF)).json()["results"]
    assert results[0]["fields"]["name"] == "Ananya Rao"


def test_rejects_files_that_are_not_resumes():
    files = [("resumes", ("photo.png", b"not a resume", "image/png"))]
    response = client.post("/api/screen", data={"job_description": JOB}, files=files)
    assert response.status_code == 400
    assert "only .pdf and .txt" in response.json()["detail"]


def test_asks_for_a_job_description():
    page = client.post("/screen", data={"job_description": "  "}, files=uploads(*sorted(FIXTURES.glob("*.txt"))))
    assert page.status_code == 400
    assert "Please paste a job description" in page.text


def test_uploaded_text_cannot_inject_html():
    evil = [("resumes", ("evil.txt", b"<script>alert('x')</script> Hadoop engineer with Hive", "text/plain"))]
    page = client.post("/screen", data={"job_description": JOB}, files=evil)
    assert "<script>alert" not in page.text


def test_top_n_ranks_everyone_but_shows_only_the_best():
    files = uploads(*sorted(FIXTURES.glob("*.txt")))
    api = client.post("/api/screen", data={"job_description": JOB, "top": "1"}, files=files).json()
    assert api["total_ranked"] == 2 and [r["file"] for r in api["results"]] == ["hadoop_engineer.txt"]
    page = client.post("/screen", data={"job_description": JOB, "top": "1"}, files=uploads(*sorted(FIXTURES.glob("*.txt"))))
    assert "Top 1 of 2 resumes" in page.text
    assert "java_developer.txt" not in page.text


def test_a_bad_top_value_gets_a_friendly_message():
    page = client.post("/screen", data={"job_description": JOB, "top": "0"}, files=uploads(*sorted(FIXTURES.glob("*.txt"))))
    assert page.status_code == 400 and "whole number" in page.text


def test_results_page_offers_the_report_as_a_download():
    page = client.post("/screen", data={"job_description": JOB}, files=uploads(*sorted(FIXTURES.glob("*.txt"))))
    assert 'download="resume-ranking.csv"' in page.text
    link = re.search(r'href="data:text/csv;charset=utf-8,([^"]+)"', page.text).group(1)
    report = urllib.parse.unquote(link)
    assert report.lstrip("\ufeff").startswith("Rank,File")
    assert report.index("hadoop_engineer.txt") < report.index("java_developer.txt")


def test_api_report_is_a_csv_file_download():
    response = client.post("/api/report", data={"job_description": JOB}, files=uploads(*sorted(FIXTURES.glob("*.txt"))))
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/csv")
    assert response.headers["content-disposition"] == 'attachment; filename="resume-ranking.csv"'
