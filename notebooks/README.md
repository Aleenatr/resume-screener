# Original prototypes

The two Colab notebooks this project started from, exported as `.py` files.
They are kept unchanged for history. They only run inside Google Colab:
they use `!pip`, `display()` and Colab file paths.

| File | Approach |
|---|---|
| `resumescreener_practice1.py` | PDF text extraction (PyMuPDF), cleaning, Sentence Transformers (`all-MiniLM-L6-v2`) and cosine similarity, plus a word-frequency summary |
| `candidate_ranking_by_name.py` | The same ranking idea using TF-IDF on a CSV of resumes, with charts and CSV export |

`evaluation/evaluate.py` re-runs both approaches on the same data as the
current version: methods 1 and 2 in its table.
