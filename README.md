# Resume Screener

Ranks resumes against a job description by **meaning and keywords together**,
and explains every ranking. For each candidate it shows which of the job's
skills they have and which are missing, 11 extracted fields, and a
three-sentence summary.

**In the browser (FastAPI web app):**

```bash
uvicorn screener.web:app --reload        # then open http://127.0.0.1:8000
```

Paste a job description, upload PDF or .txt resumes, and the ranked candidates
appear on the page. Each one shows score bars, matched and missing skills,
extracted fields and a summary.

- **Show only the top N.** Every resume is still ranked against all the others;
  only the best N are shown.
- **Download report.** The candidates shown are saved as a CSV that opens in
  Excel. Cells that look like formulas are neutralised, so a malicious resume
  can't run anything in the spreadsheet (CSV injection).

For other programs, the ranking is available as JSON at `POST /api/screen` and as
CSV at `POST /api/report`. Both take an optional `top`, and there are
interactive docs at `/docs`.

**From the command line:**

```bash
python -m screener --jd examples/job_description.txt --resumes examples/resumes
```

```
#1  ananya_rao.pdf   meaning 0.831 | keywords 0.337
    matched skills : Python, REST APIs, Django, Flask, SQL, PostgreSQL, AWS, Docker, Git
    missing skills : -
    name: Ananya Rao | email: ananya.rao@example.com | phone: +91 90000 00001
    degree: Bachelor's (B.Tech) | graduated: 2025 | CGPA: 8.6/10 | experience: 1.0 yrs
    summary: Backend developer who builds REST APIs in Python. 1 year of internship experience
             with Django and PostgreSQL. Built REST APIs with Django and Django REST Framework
             for a payments dashboard.

#2  karan_mehta.pdf   meaning 0.529 | keywords 0.057
    matched skills : REST APIs, SQL, Git
    missing skills : Python, Django, Flask, PostgreSQL, AWS, Docker
    ...
```

The sample resumes in `examples/resumes/` are fictional people (example.com emails, made-up numbers).

## Results

Measured on **166 unique public resumes across 25 job categories**. Full
report, per-category scores and the most common mistakes are in
[`evaluation/results.md`](evaluation/results.md).

| Method | Top-1 accuracy | Top-3 accuracy | R-precision |
|---|---|---|---|
| Keywords only (TF-IDF) | 87.3% | 95.2% | 82.7% |
| Meaning only, first 256 tokens (the first version) | 67.5% | 83.7% | 61.9% |
| Meaning only, full resume in 150-word chunks | 79.5% | 89.2% | 70.1% |
| **Meaning + keywords (default)** | **89.2%** | **97.6%** | **81.2%** |

- **Top-1 / top-3:** the resume's true job category is the best match, or one of the 3 best matches, out of 25 job descriptions.
- **R-precision:** the "rank the candidates" view. If R resumes truly belong to a job, how many of the top R that the screener ranks are really from that job? Averaged over the 25 jobs.

What the numbers say:

1. **The first version only read the start of each resume.** The model reads at most 256 tokens, and 64% of the resumes are longer, so 55% of all resume text was never seen. Reading the whole resume in overlapping chunks raised top-1 accuracy from 67.5% to 79.5%.
2. **On these resumes, plain keywords beat meaning.** Tech roles are defined by their tools (Hadoop, SAP, Selenium), and TF-IDF gives exactly those rare words the most weight.
3. **Combining both did best** on top-1 and top-3, and about level with keywords on R-precision. The meaning half is what still works when a resume describes a skill in different words from the job post.
4. **Most remaining mistakes are near-identical roles or label problems.** Automation Testing is confused with Testing, and several resumes labelled "Testing" are electronics graduates with no software testing in them at all.

**Caveats:**
- 166 resumes is small: one resume is 0.6 points.
- The job descriptions were written for this evaluation, once, before the first run.
- A category label is not the same thing as a recruiter's judgement of fit.
- An earlier run scored all 25 jobs in one go. It fitted TF-IDF once and rescaled over the whole table, and gave 87.3% top-1 for both keywords and the hybrid. It was switched to scoring one job at a time, exactly as the tool does, before these numbers were final.

**About the data:** the public file has 962 rows, but only 166 are unique; the rest are exact copies. Duplicates are removed before measuring. Without that step, the same resume is counted several times and every number looks better than it is.

## How it works

```
resume.pdf -> 1. read text -> 2. clean -> 3. extract 11 fields (rules)
                                       -> 4. summarise (word-frequency scoring)
                                       -> 5. score against the job:
                                              meaning : MiniLM vectors of 150-word chunks -> cosine similarity
                                              keywords: TF-IDF vectors -> cosine similarity
                                              -> rescale both to one scale, average, rank
```

| Step | File | What it does |
|---|---|---|
| 1 | `screener/pdf_reader.py` | Text out of a PDF (PyMuPDF) or a .txt file |
| 2 | `screener/cleaning.py` | Repairs broken characters ("NaÃ¯ve" becomes "Naïve") and removes the name, email, phone and links, so the score can't depend on who the person is. Keeps "C++", "C#" and ".NET" intact |
| 3 | `screener/fields.py`, `screener/skills.py` | 11 fields from regular expressions and a ~110-skill vocabulary. A field the rules can't find comes back empty rather than guessed |
| 4 | `screener/summary.py` | Extractive summary: sentences scored by the average importance of their words, filler words ignored, top 3 kept in their original order |
| 5 | `screener/matcher.py` | Meaning: `all-MiniLM-L6-v2` embeddings, averaged over chunks. Keywords: TF-IDF. Cosine similarity in NumPy. The two scores are rescaled and averaged |
| - | `screener/pipeline.py` | Runs steps 1-5 for a batch of resumes, shared by the command line and the web app |
| - | `screener/web.py`, `screener/templates/` | The FastAPI web app: upload page, results page, JSON and CSV endpoints |
| - | `screener/report.py` | The CSV report (Excel-friendly, safe against formula injection) |
| - | `screener/__main__.py` | The command line |

**The 11 fields:** name, email, phone, LinkedIn, GitHub, highest degree,
graduation year, CGPA, years of experience, skills, certifications.

## Run it

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

uvicorn screener.web:app --reload        # web app at http://127.0.0.1:8000
python -m screener --jd examples/job_description.txt --resumes examples/resumes --top 3 --csv report.csv
pytest                                   # 40 tests, no model download needed

python -m evaluation.download_data       # the public dataset, checksum-verified
python -m evaluation.evaluate            # rewrites evaluation/results.md
```

The first run downloads the model (about 90 MB). `python examples/make_sample_resumes.py`
regenerates the sample PDFs.

## Project layout

```
screener/          the pipeline (steps 1-5), the command line and the FastAPI web app (web.py, templates/)
evaluation/        download_data.py, evaluate.py, results.md, job_descriptions/ (25 jobs)
examples/          a job description, 5 fictional sample resume PDFs, and the script that makes them
tests/             unit tests for every step, plus one end-to-end test
notebooks/         the original Colab prototypes this project started from
```

## Limitations

- English only. Phone numbers follow the Indian mobile format.
- Scanned PDFs contain no text. They are flagged and ranked last, and need OCR (for example Tesseract) first.
- Two-column PDFs can come out with lines from both columns mixed together.
- The skills vocabulary is hand-written (about 110 skills), so it misses anything not on the list.
- The web app has no login. Run it locally, or put it behind authentication before sharing it.
- Ranking happens inside the request, which is fine for a few dozen resumes. Hundreds would need a background job queue.
- Similarity is not a probability of being a good hire. Use the ranking to decide who to read first, never to reject people automatically, and keep a human making the decision.

## History

This started as two Colab notebooks, kept in `notebooks/`:
- one ranked resumes with Sentence Transformers;
- the other ranked them with TF-IDF.

This version turns them into a tested package with a web app, and fixes the issues that measuring exposed: truncation, the cleaner deleting "C++", a summary that favoured long sentences, and only 3 fields extracted. It also adds the evaluation.

## Credits

- Model: [`sentence-transformers/all-MiniLM-L6-v2`](https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2).
- Evaluation data: the public Kaggle "Resume Dataset" file `UpdatedResumeDataSet.csv`, downloaded from a Hugging Face mirror. It is not redistributed in this repository.
