from screener.fields import extract_fields

RESUME = """Priya Sharma
priya.sharma@example.com | +91 98765 43210
linkedin.com/in/priya-sharma | github.com/priya-codes

EDUCATION
B.Tech in Computer Science, Example Institute of Technology, 2021 - 2025, CGPA: 8.4/10

EXPERIENCE
Backend Developer Intern - 2 years of hands-on experience building REST APIs with Django and PostgreSQL.

SKILLS
Python, C++, Django, SQL, Docker, Git

CERTIFICATIONS
AWS Certified Cloud Practitioner (2024)
"""


def test_extracts_all_eleven_fields():
    f = extract_fields(RESUME)
    assert len(f) == 11
    assert f["name"] == "Priya Sharma"
    assert f["email"] == "priya.sharma@example.com"
    assert f["phone"] == "+91 98765 43210"
    assert f["linkedin"] == "linkedin.com/in/priya-sharma"
    assert f["github"] == "github.com/priya-codes"
    assert f["degree"] == "Bachelor's (B.Tech)"
    assert f["graduation_year"] == 2025
    assert f["cgpa"] == "8.4/10"
    assert f["experience_years"] == 2.0
    assert {"Python", "C++", "Django", "SQL", "PostgreSQL", "Docker", "Git", "REST APIs"} <= set(f["skills"])
    assert f["certifications"] == ["AWS Certified Cloud Practitioner (2024)"]


def test_missing_fields_are_none_not_guesses():
    f = extract_fields("CURRICULUM VITAE\nlooking for a role in sales")
    assert f["name"] is None and f["email"] is None and f["degree"] is None and f["cgpa"] is None


def test_months_of_experience_become_years():
    # The public dataset writes experience like this (typo and all).
    assert extract_fields("Python- Exprience - 18 months")["experience_years"] == 1.5


def test_spelled_out_degrees_keep_their_subject():
    assert extract_fields("Bachelor of Engineering in Computer Science")["degree"] == "Bachelor's (Bachelor of Engineering)"
