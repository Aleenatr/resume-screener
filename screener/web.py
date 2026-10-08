"""Web app: paste a job description, upload resumes, get the ranking in the browser.

    uvicorn screener.web:app --reload        then open http://127.0.0.1:8000

FastAPI does four jobs here:
- GET  /            the upload page: a plain HTML form, no JavaScript
- POST /screen      takes the form, runs the pipeline, shows the results page
- POST /api/screen  the same as JSON, for other programs (try it at /docs)
- POST /api/report  the same as a downloadable CSV report

Design choices worth knowing:
- The model is loaded once, on first use, and kept (get_encoder). Loading it
  takes a second or two and ~90 MB of memory - far too slow to repeat per request.
- The endpoints are plain `def`, not `async def`. Running the model is CPU-heavy
  work; FastAPI runs plain functions in a worker thread, so one long request
  doesn't freeze the server for everyone else.
- "Show only the top N": every uploaded resume is still ranked against all the
  others; only the first N are shown and put in the report.
- The report download needs no server storage: the CSV is built with the page
  and embedded in the download link itself (a data: URL).
- Uploads are read in memory and never saved to disk.
- Pages are rendered with Jinja2, which escapes everything it inserts, so text
  inside an uploaded resume can't inject HTML or scripts into the page.
"""
from functools import lru_cache
from pathlib import Path

from fastapi import Depends, FastAPI, File, Form, HTTPException, Request, Response, UploadFile
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from .matcher import load_encoder
from .pdf_reader import SUPPORTED_TYPES, text_from_bytes
from .pipeline import screen_texts
from .report import to_csv
from .skills import find_skills

MAX_FILES = 50
MAX_BYTES = 5 * 1024 * 1024  # 5 MB per resume
MIN_JOB_CHARS = 20
REPORT_NAME = "resume-ranking.csv"

app = FastAPI(
    title="Resume Screener",
    description="Rank resumes against a job description by meaning and keywords, with 11 extracted fields "
                "and a short summary per candidate. Names and contact details are removed before scoring.",
)
templates = Jinja2Templates(directory=Path(__file__).parent / "templates")


@lru_cache(maxsize=1)
def get_encoder():
    """The sentence-transformer, loaded on first use and then reused."""
    return load_encoder()


def read_uploads(job_description, files):
    """Check the inputs and turn the uploads into (file name, text) pairs.

    Raises ValueError with a message that is safe to show the user.
    """
    if len(job_description.strip()) < MIN_JOB_CHARS:
        raise ValueError("Please paste a job description (at least a sentence or two).")
    files = [f for f in files if f.filename]  # a form submitted with no file chosen sends one empty entry
    if not files:
        raise ValueError("Please choose at least one resume (.pdf or .txt).")
    if len(files) > MAX_FILES:
        raise ValueError(f"Please upload at most {MAX_FILES} resumes at a time.")
    resumes = []
    for upload in files:
        if Path(upload.filename).suffix.lower() not in SUPPORTED_TYPES:
            raise ValueError(f"{upload.filename}: only .pdf and .txt files are supported.")
        data = upload.file.read()
        if len(data) > MAX_BYTES:
            raise ValueError(f"{upload.filename} is larger than 5 MB.")
        try:
            resumes.append((upload.filename, text_from_bytes(upload.filename, data)))
        except Exception:
            raise ValueError(f"{upload.filename} could not be read. Is it a valid PDF?")
    return resumes


def parse_top(value):
    """The "show only the top" box: empty means everyone, otherwise a whole number of 1 or more."""
    value = (value or "").strip()
    if not value:
        return None
    if not value.isdigit() or int(value) < 1:
        raise ValueError("\"Show only the top\" must be a whole number of 1 or more, or empty to show everyone.")
    return int(value)


def rank_uploads(job_description, resumes, top, encode):
    """Rank every upload, then keep the first `top` (or all). Returns (shown, how many were ranked)."""
    ranked = screen_texts(job_description, read_uploads(job_description, resumes), encode)
    return (ranked[:top] if top else ranked), len(ranked)


@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse(request, "index.html", {})


@app.post("/screen", response_class=HTMLResponse)
def screen_page(request: Request, job_description: str = Form(""), top: str = Form(""),
                resumes: list[UploadFile] = File(default=[]), encode=Depends(get_encoder)):
    context = {"job_description": job_description, "top": top}
    try:
        shown, total = rank_uploads(job_description, resumes, parse_top(top), encode)
    except ValueError as problem:
        context["error"] = str(problem)
        return templates.TemplateResponse(request, "index.html", context, status_code=400)
    context.update(results=shown, total=total, job_skills=find_skills(job_description),
                   report_csv=to_csv(shown), report_name=REPORT_NAME)
    return templates.TemplateResponse(request, "index.html", context)


@app.post("/api/screen")
def screen_api(job_description: str = Form(...), resumes: list[UploadFile] = File(...),
               top: int | None = Form(None, ge=1, description="Return only the best N (default: all)"),
               encode=Depends(get_encoder)):
    """Rank uploaded resumes against a job description. Best match first."""
    try:
        shown, total = rank_uploads(job_description, resumes, top, encode)
    except ValueError as problem:
        raise HTTPException(status_code=400, detail=str(problem))
    return {"job_skills": find_skills(job_description), "total_ranked": total, "results": shown}


@app.post("/api/report")
def report_api(job_description: str = Form(...), resumes: list[UploadFile] = File(...),
               top: int | None = Form(None, ge=1, description="Include only the best N (default: all)"),
               encode=Depends(get_encoder)):
    """The same ranking as a CSV report (opens in Excel)."""
    try:
        shown, _ = rank_uploads(job_description, resumes, top, encode)
    except ValueError as problem:
        raise HTTPException(status_code=400, detail=str(problem))
    return Response(content=to_csv(shown), media_type="text/csv; charset=utf-8",
                    headers={"Content-Disposition": f'attachment; filename="{REPORT_NAME}"'})
