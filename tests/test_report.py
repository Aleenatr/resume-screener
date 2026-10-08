import csv
import io

from screener.report import COLUMNS, safe_cell, to_csv

RESULT = {
    "rank": 1, "file": "a.pdf", "semantic_similarity": 0.8, "keyword_similarity": 0.3,
    "matched_skills": ["Python", "SQL"], "missing_skills": ["Docker"],
    "fields": {"name": "Priya Sharma", "email": "p@example.com", "phone": "+91 98765 43210", "linkedin": None,
               "github": None, "degree": "Bachelor's (B.Tech)", "graduation_year": 2025, "cgpa": "8.4/10",
               "experience_years": 2.0, "skills": ["Python", "SQL"], "certifications": []},
    "summary": '=HYPERLINK("http://example.com")',
}


def read(report):
    return list(csv.reader(io.StringIO(report.lstrip("﻿"))))


def test_report_has_a_header_and_one_row_per_candidate():
    rows = read(to_csv([RESULT]))
    assert rows[0] == COLUMNS
    assert rows[1][:6] == ["1", "a.pdf", "0.8", "0.3", "Python; SQL", "Docker"]


def test_report_starts_with_a_bom_so_excel_reads_it_as_utf8():
    assert to_csv([]).startswith("﻿")


def test_cells_that_look_like_formulas_are_neutralised():
    assert safe_cell("=1+1") == "'=1+1"
    assert safe_cell("+91 98765 43210") == "'+91 98765 43210"
    assert safe_cell("Python developer") == "Python developer"
    assert read(to_csv([RESULT]))[1][-1].startswith("'=")
