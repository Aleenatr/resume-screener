"""How well does the screener match resumes to the right job?

Data: the public Kaggle file UpdatedResumeDataSet.csv - 962 resumes, each
labelled with one of 25 job categories. Only 166 of them are unique; the rest
are exact copies. Duplicates are removed first. Otherwise the same resume is
scored several times over and the results look better than they are.

Jobs: one job description per category, in job_descriptions/. They were
written before the first evaluation run and have not been edited since.

Every method gives a score to every (resume, job) pair. From those scores:
  top-1 accuracy : for each resume, is its best-matching job the right one?
  top-3 accuracy : is the right job among its 3 best-matching jobs?
  R-precision    : for each job that R resumes truly belong to, what share of
                   the top R ranked resumes really belong to it? (averaged
                   over the 25 jobs - this is the "ranking candidates" view)

Four methods, each scored exactly the way the tool scores one job at a time:
  1. Keywords only (TF-IDF): the approach of the second Colab notebook
  2. Meaning only, whole text: the first Colab version (the model only ever
     sees the first 256 tokens of a resume)
  3. Meaning only, 150-word chunks (the model sees the whole resume)
  4. Meaning + keywords: 3 and 1 averaged after rescaling - the tool's default

Run:  python -m evaluation.evaluate
"""
import csv
import re
import sys
from collections import Counter
from datetime import date
from pathlib import Path

import numpy as np

from screener.cleaning import clean_for_keywords, clean_for_model
from screener.matcher import (CHUNK_WORDS, MODEL_NAME, combined_scores, embed_documents, keyword_scores,
                              load_encoder, to_unit_length)

HERE = Path(__file__).resolve().parent
DATA = HERE.parent / "data" / "raw" / "UpdatedResumeDataSet.csv"
JOBS = HERE / "job_descriptions"
REPORT = HERE / "results.md"


def slug(category):
    """"Network Security Engineer" -> "network_security_engineer" (the job file's name)."""
    return re.sub(r"[^a-z0-9]+", "_", category.lower()).strip("_")


def load_resumes(path=DATA):
    """Unique resumes and their categories, plus how many rows the file had."""
    unique, rows = {}, 0
    with open(path, encoding="utf-8", newline="") as f:
        for row in csv.DictReader(f):
            rows += 1
            key = " ".join(row["Resume"].split())  # same text, ignoring spacing = same resume
            unique.setdefault(key, (row["Resume"], row["Category"]))
    texts = [text for text, _ in unique.values()]
    labels = [category for _, category in unique.values()]
    return texts, labels, rows


def first_version_clean(text):
    """The first Colab version's cleaner, unchanged: lowercase, keep only a-z, 0-9 and spaces."""
    text = text.lower()
    text = re.sub(r"\s+", " ", text)
    text = re.sub(r"[^a-z0-9\s]", "", text)
    return text.strip()


def top_k_accuracy(scores, labels, categories, k):
    truth = [categories.index(label) for label in labels]
    best_k = np.argsort(-scores, axis=1, kind="stable")[:, :k]
    return float(np.mean([truth[i] in best_k[i] for i in range(len(labels))]))


def r_precision(scores, labels, categories):
    labels = np.array(labels)
    values = []
    for j, category in enumerate(categories):
        belongs = labels == category
        top = np.argsort(-scores[:, j], kind="stable")[:belongs.sum()]
        values.append(belongs[top].mean())
    return float(np.mean(values))


def truncation_stats(texts, tokenizer, limit):
    """How many documents run past the model's limit, and how much text it never sees."""
    lengths = [len(tokenizer(t)["input_ids"]) for t in texts]
    longer = sum(n > limit for n in lengths)
    unseen = sum(max(0, n - limit) for n in lengths) / sum(lengths)
    return longer, unseen, int(np.median(lengths))


def main():
    if not DATA.exists():
        sys.exit("Dataset not found - run first:  python -m evaluation.download_data")
    resumes, labels, rows = load_resumes()
    categories = sorted(set(labels))
    jobs = [(JOBS / f"{slug(c)}.txt").read_text(encoding="utf-8") for c in categories]
    encode = load_encoder()
    model = encode.model

    # Every method below is a (resumes x jobs) table of scores.
    keyword_resumes = [clean_for_keywords(t) for t in resumes]
    keywords = np.column_stack([keyword_scores(clean_for_keywords(job), keyword_resumes) for job in jobs])

    whole = (to_unit_length(encode([first_version_clean(t) for t in resumes]))
             @ to_unit_length(encode([first_version_clean(t) for t in jobs])).T)

    chunked = (embed_documents([clean_for_model(t) for t in resumes], encode)
               @ embed_documents([clean_for_model(t) for t in jobs], encode).T)

    both = np.column_stack([combined_scores(chunked[:, j], keywords[:, j]) for j in range(len(jobs))])

    methods = {
        "1. Keywords only - TF-IDF (second notebook)": keywords,
        "2. Meaning only, whole text - first 256 tokens (first version)": whole,
        f"3. Meaning only, {CHUNK_WORDS}-word chunks - full resume": chunked,
        "4. Meaning + keywords (this tool's default)": both,
    }
    table = [(name, top_k_accuracy(s, labels, categories, 1), top_k_accuracy(s, labels, categories, 3),
              r_precision(s, labels, categories)) for name, s in methods.items()]

    longer, unseen, median_tokens = truncation_stats(
        [first_version_clean(t) for t in resumes], model.tokenizer, model.max_seq_length)

    # Where does the default method go wrong?
    predicted = np.argmax(both, axis=1)
    correct, total, confusions = Counter(), Counter(labels), Counter()
    for i, label in enumerate(labels):
        guess = categories[predicted[i]]
        if guess == label:
            correct[label] += 1
        else:
            confusions[label, guess] += 1

    lines = [
        "# Evaluation results",
        "",
        f"Generated by `python -m evaluation.evaluate` on {date.today().isoformat()}.",
        "",
        f"- **Dataset:** `UpdatedResumeDataSet.csv`, {rows} rows but only **{len(resumes)} unique resumes** "
        f"once exact copies are removed, in {len(categories)} job categories",
        f"- **Jobs:** {len(jobs)} job descriptions, one per category (`evaluation/job_descriptions/`)",
        f"- **Model:** `{MODEL_NAME}`, which reads at most {model.max_seq_length} tokens at a time",
        f"- **Resumes longer than {model.max_seq_length} tokens:** {longer} of {len(resumes)} "
        f"({longer / len(resumes):.0%}); median length {median_tokens} tokens",
        f"- **Share of all resume text the first version never showed the model:** {unseen:.0%}",
        "",
        "| Method | Top-1 accuracy | Top-3 accuracy | R-precision |",
        "|---|---|---|---|",
    ]
    lines += [f"| {name} | {t1:.1%} | {t3:.1%} | {rp:.1%} |" for name, t1, t3, rp in table]
    lines += [
        "",
        "- **Top-1:** the best-matching of the 25 jobs is the resume's true category.",
        "- **Top-3:** the true category is among the 3 best-matching jobs.",
        "- **R-precision:** for a job that R resumes truly belong to, the share of the top R ranked resumes "
        "that really belong to it, averaged over the 25 jobs.",
        "",
        f"With {len(resumes)} resumes, one resume is {1 / len(resumes):.1%}, so differences of a point or two "
        "are not meaningful.",
        "",
        "## Default method, per category",
        "",
        "| Category | Resumes | Top-1 correct |",
        "|---|---|---|",
    ]
    lines += [f"| {c} | {total[c]} | {correct[c]} |" for c in categories]
    lines += ["", "## Default method, most common mistakes", "",
              "| True category | Matched to | Times |", "|---|---|---|"]
    lines += [f"| {true} | {guess} | {n} |" for (true, guess), n in confusions.most_common(8)]

    report = "\n".join(lines) + "\n"
    REPORT.write_text(report, encoding="utf-8")
    print(report)


if __name__ == "__main__":
    main()
