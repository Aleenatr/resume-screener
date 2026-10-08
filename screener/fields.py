"""Step 3 - pull 11 structured fields out of a resume.

Everything here is rules: regular expressions plus the skills vocabulary, no
model. Rules are easy to test and easy to explain, and when one can't find a
field it returns None (or an empty list) instead of a confident wrong guess.

The 11 fields: name, email, phone, linkedin, github, degree, graduation_year,
cgpa, experience_years, skills, certifications.
"""
import re

from .cleaning import fix_broken_characters, remove_contact_details
from .skills import find_skills
from .summary import split_sentences

EMAIL = re.compile(r"[\w.+-]+@[\w-]+(?:\.[\w-]+)+")
# Indian mobile numbers: optional +91 or 0, then 10 digits starting with 6-9,
# optionally split 5 + 5 ("+91 98765 43210"). The first version used the same
# idea but missed numbers written with a space in the middle.
PHONE = re.compile(r"(?<![\w+])(?:\+91[\s-]?|0)?[6-9]\d{4}[\s-]?\d{5}(?!\d)")
LINKEDIN = re.compile(r"linkedin\.com/in/[\w-]+", re.IGNORECASE)
GITHUB = re.compile(r"github\.com/[\w-]+", re.IGNORECASE)
YEAR = re.compile(r"\b(?:19[89]\d|20[0-4]\d)\b")

# "CGPA: 8.03", "CGPA of 8.03/10", "GPA - 3.6/4" ... and "8.03 CGPA".
CGPA_BEFORE = re.compile(r"\b(?:CGPA|GPA|CPI)\b\s*(?:of|:|-)?\s*(\d{1,2}\.\d{1,2})(?:\s*/\s*(\d{1,2}))?", re.IGNORECASE)
CGPA_AFTER = re.compile(r"\b(\d{1,2}\.\d{1,2})(?:\s*/\s*(\d{1,2}))?\s*(?:CGPA|GPA|CPI)\b", re.IGNORECASE)

# "3 years of experience", "2.5+ yrs of industry experience" ... and the
# public dataset's "Exprience - 24 months" (its typo, hence "expe?rience").
EXPERIENCE_YEARS = re.compile(
    r"(\d{1,2}(?:\.\d)?)\s*\+?\s*(?:years?|yrs?)\b(?:\s+of)?(?:\s+[a-z-]+){0,2}\s+experience", re.IGNORECASE)
EXPERIENCE_MONTHS = re.compile(r"expe?rience\s*[-:]?\s*(\d{1,3})\s*months?", re.IGNORECASE)

# Highest level first: the first level that matches is the highest degree.
DEGREE_LEVELS = [
    ("PhD", re.compile(r"\bPh\.?\s?D\b|\bDoctorate\b", re.IGNORECASE)),
    ("Master's", re.compile(
        r"\bM\.?\s?Tech\b|\bM\.E\.|\bMCA\b|\bMBA\b|\bPGDM\b|\bM\.?\s?Sc\b|\bM\.?\s?Com\b|\bLLM\b"
        r"|\bMasters?\s+(?:of|in)\s+\w+", re.IGNORECASE)),
    ("Bachelor's", re.compile(
        r"\bB\.?\s?Tech\b|\bB\.E\b|\bBCA\b|\bBBA\b|\bB\.?\s?Sc\b|\bB\.?\s?Com\b|\bLLB\b|\bB\.A\b"
        r"|\bBachelors?\s+(?:of|in)\s+\w+", re.IGNORECASE)),
    ("Diploma", re.compile(r"\bDiploma\b", re.IGNORECASE)),
]

# Words that mean a line is a heading, not a name ("Curriculum Vitae", "Career Objective").
HEADING_WORDS = {"resume", "curriculum", "vitae", "cv", "profile", "summary", "objective", "skills",
                 "education", "experience", "contact", "details", "career", "personal", "declaration"}


def _first(pattern, text):
    match = pattern.search(text)
    return match.group().strip() if match else None


def extract_name(text):
    """The first short line near the top that looks like a person's name.

    Same rule as the first version (2-5 words, letters only, first few lines),
    plus two checks: skip headings like "Curriculum Vitae", and every word
    must start with a capital letter.
    """
    for line in text.strip().splitlines()[:8]:
        line = line.strip()
        words = line.split()
        if not 2 <= len(words) <= 5:
            continue
        if not re.fullmatch(r"[A-Za-z][A-Za-z.' -]*", line):
            continue
        if any(w.lower().strip(".") in HEADING_WORDS for w in words):
            continue
        if all(w[0].isupper() for w in words):
            return line
    return None


def extract_degree(text):
    """The highest degree mentioned, e.g. "Bachelor's (B.Tech)"."""
    for level, pattern in DEGREE_LEVELS:
        match = pattern.search(text)
        if match:
            return f"{level} ({match.group().strip()})"
    return None


def extract_graduation_year(text):
    """The latest year written next to any degree ("B.Tech 2023 - 2027" -> 2027)."""
    years = []
    for _, pattern in DEGREE_LEVELS:
        for match in pattern.finditer(text):
            nearby = text[max(0, match.start() - 40): match.end() + 150]
            years += [int(y) for y in YEAR.findall(nearby)]
    return max(years) if years else None


def extract_cgpa(text):
    """"8.03" or "8.03/10" - only if it is a sensible grade (at most 10)."""
    for pattern in (CGPA_BEFORE, CGPA_AFTER):
        for match in pattern.finditer(text):
            value, scale = match.group(1), match.group(2)
            if float(value) <= 10:
                return f"{value}/{scale}" if scale else value
    return None


def extract_experience_years(text):
    """The largest experience figure stated, in years (months are divided by 12)."""
    figures = [float(m) for m in EXPERIENCE_YEARS.findall(text)]
    figures += [int(m) / 12 for m in EXPERIENCE_MONTHS.findall(text)]
    return round(max(figures), 1) if figures else None


def extract_certifications(text, limit=5):
    """Up to `limit` short sentences that mention a certificate or certification."""
    found = []
    for sentence in split_sentences(text):
        # 3+ words, so a heading like "CERTIFICATIONS" doesn't count as one
        if "certif" in sentence.lower() and len(sentence.split()) >= 3 and len(sentence) <= 120 \
                and sentence not in found:
            found.append(sentence)
    return found[:limit]


def extract_fields(text):
    """All 11 fields for one resume."""
    text = fix_broken_characters(text)
    # Skills are searched without contact details, so an email address like
    # "java.dev@..." or a "github.com/..." link can't count as a skill.
    without_contacts = remove_contact_details(text)
    return {
        "name": extract_name(text),
        "email": _first(EMAIL, text),
        "phone": _first(PHONE, text),
        "linkedin": _first(LINKEDIN, text),
        "github": _first(GITHUB, text),
        "degree": extract_degree(text),
        "graduation_year": extract_graduation_year(text),
        "cgpa": extract_cgpa(text),
        "experience_years": extract_experience_years(text),
        "skills": find_skills(without_contacts),
        "certifications": extract_certifications(without_contacts),
    }
