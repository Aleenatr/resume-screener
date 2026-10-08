"""The downloadable report: one CSV row per candidate, best match first.

CSV because it opens straight in Excel or Google Sheets.

Two details:
- The file starts with a byte-order mark (BOM). It tells Excel the file is
  UTF-8, so names with accents and symbols like "C#" show correctly.
- Resumes are untrusted input. A cell starting with = + - or @ is treated as a
  formula by Excel, so a resume containing "=HYPERLINK(...)" could run inside
  the recruiter's spreadsheet ("CSV injection"). Such cells get a leading
  apostrophe, which makes Excel show them as plain text.
"""
import csv
import io

COLUMNS = ["Rank", "File", "Meaning score", "Keyword score", "Matched skills", "Missing skills",
           "Name", "Email", "Phone", "LinkedIn", "GitHub", "Degree", "Graduation year", "CGPA",
           "Experience (years)", "Skills", "Certifications", "Summary"]
FORMULA_STARTS = ("=", "+", "-", "@", "\t", "\r")


def safe_cell(value):
    """Text that Excel will show as text, never run as a formula."""
    if value is None:
        return ""
    text = str(value)
    return "'" + text if text.startswith(FORMULA_STARTS) else text


def to_csv(results):
    """The report for these results, as CSV text."""
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(COLUMNS)
    for r in results:
        f = r["fields"]
        row = [r["rank"], r["file"], r["semantic_similarity"], r["keyword_similarity"],
               "; ".join(r["matched_skills"]), "; ".join(r["missing_skills"]),
               f["name"], f["email"], f["phone"], f["linkedin"], f["github"],
               f["degree"], f["graduation_year"], f["cgpa"], f["experience_years"],
               "; ".join(f["skills"]), "; ".join(f["certifications"]), r["summary"]]
        writer.writerow([safe_cell(value) for value in row])
    return "﻿" + buffer.getvalue()
