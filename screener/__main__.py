"""Command line:

    python -m screener --jd examples/job_description.txt --resumes examples/resumes

Reads every .pdf / .txt resume in the folder, ranks them against the job
description and prints, for each candidate: the two similarity scores, which
of the job's skills they have and which are missing, the extracted fields and
a three-sentence summary. `--top 3` keeps only the best 3; `--csv report.csv`
saves them as a spreadsheet report; `--json results.json` saves everything.

For the browser version, see screener/web.py.
"""
import argparse
import json
from pathlib import Path

from .matcher import load_encoder
from .pdf_reader import find_resumes
from .pipeline import screen
from .report import to_csv


def print_report(results, top):
    for r in results[:top]:
        f = r["fields"]
        print(f"#{r['rank']}  {r['file']}   meaning {r['semantic_similarity']:.3f}"
              f" | keywords {r['keyword_similarity']:.3f}")
        if r["no_text_found"]:
            print("    !! no text found - is this a scanned PDF? It needs OCR first.")
        print(f"    matched skills : {', '.join(r['matched_skills']) or '-'}")
        print(f"    missing skills : {', '.join(r['missing_skills']) or '-'}")
        print(f"    name: {f['name'] or '-'} | email: {f['email'] or '-'} | phone: {f['phone'] or '-'}")
        print(f"    degree: {f['degree'] or '-'} | graduated: {f['graduation_year'] or '-'}"
              f" | CGPA: {f['cgpa'] or '-'} | experience: {f['experience_years'] or '-'} yrs")
        print(f"    summary: {r['summary'] or '-'}")
        print()


def main():
    parser = argparse.ArgumentParser(description="Rank resumes against a job description.")
    parser.add_argument("--jd", required=True, help="text file with the job description")
    parser.add_argument("--resumes", required=True, help="folder of .pdf / .txt resumes")
    parser.add_argument("--top", type=int, default=10, help="how many candidates to print (default 10)")
    parser.add_argument("--json", help="also save the full results to this JSON file")
    parser.add_argument("--csv", help="also save the top candidates as a CSV report (opens in Excel)")
    args = parser.parse_args()

    paths = find_resumes(args.resumes)
    if not paths:
        parser.error(f"no .pdf or .txt files found in {args.resumes}")
    job_text = Path(args.jd).read_text(encoding="utf-8")

    results = screen(job_text, paths, load_encoder())
    print(f"Ranked {len(results)} resumes against {Path(args.jd).name} (best match first)\n")
    print_report(results, args.top)
    if args.json:
        Path(args.json).write_text(json.dumps(results, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"Full results saved to {args.json}")
    if args.csv:
        Path(args.csv).write_text(to_csv(results[:args.top]), encoding="utf-8")
        print(f"Report for the top {min(args.top, len(results))} saved to {args.csv}")


if __name__ == "__main__":
    main()
