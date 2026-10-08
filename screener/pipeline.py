"""The whole pipeline in one call, shared by the command line and the web app."""
from pathlib import Path

import numpy as np

from .cleaning import clean_for_keywords, clean_for_model, clean_lines
from .fields import extract_fields
from .matcher import combined_scores, cosine_scores, embed_documents, keyword_scores, rank
from .pdf_reader import read_resume
from .skills import find_skills
from .summary import summarize


def screen_texts(job_text, resumes, encode):
    """Rank resumes against a job. `resumes` is a list of (file name, raw text).

    Returns one result per resume, best match first.
    """
    candidates = []
    for name_of_file, raw in resumes:
        fields = extract_fields(raw)
        name = fields["name"]
        candidates.append({
            "file": name_of_file,
            "fields": fields,
            "model_text": clean_for_model(raw, name=name),      # blind: no name or contact details
            "keyword_text": clean_for_keywords(raw, name=name),
            "summary": summarize(clean_lines(raw, name=name)),
        })

    vectors = embed_documents([clean_for_model(job_text)] + [c["model_text"] for c in candidates], encode)
    semantic = cosine_scores(vectors[0], vectors[1:])
    keyword = keyword_scores(clean_for_keywords(job_text), [c["keyword_text"] for c in candidates])
    combined = combined_scores(semantic, keyword)
    for i, candidate in enumerate(candidates):
        if not candidate["model_text"]:
            combined[i] = -np.inf  # no text at all (e.g. a scanned PDF): always ranked last

    job_skills = find_skills(job_text)
    results = []
    for position, i in enumerate(rank(combined), start=1):
        candidate = candidates[i]
        has = set(candidate["fields"]["skills"])
        results.append({
            "rank": position,
            "file": candidate["file"],
            "semantic_similarity": round(float(semantic[i]), 3),
            "keyword_similarity": round(float(keyword[i]), 3),
            "combined_score": round(float(combined[i]), 3) if np.isfinite(combined[i]) else None,
            "matched_skills": [s for s in job_skills if s in has],
            "missing_skills": [s for s in job_skills if s not in has],
            "fields": candidate["fields"],
            "summary": candidate["summary"],
            "no_text_found": not candidate["model_text"],
        })
    return results


def screen(job_text, resume_paths, encode):
    """Same as screen_texts, for resume files on disk."""
    return screen_texts(job_text, [(Path(p).name, read_resume(p)) for p in resume_paths], encode)
