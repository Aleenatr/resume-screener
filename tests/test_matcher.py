from pathlib import Path

import numpy as np

from screener.pipeline import screen
from screener.matcher import (chunk_words, combined_scores, cosine_scores, embed_documents, keyword_scores,
                              rank, standardise)

FIXTURES = Path(__file__).parent / "fixtures"


def test_chunks_overlap_and_cover_the_whole_text():
    text = " ".join(f"w{i}" for i in range(400))
    chunks = chunk_words(text, size=150, overlap=30)
    assert [len(c.split()) for c in chunks] == [150, 150, 150, 40]
    assert chunks[1].split()[0] == "w120"     # 30 words shared with the first chunk
    assert chunks[-1].split()[-1] == "w399"   # nothing at the end is dropped


def test_short_text_is_one_chunk():
    assert chunk_words("just a few words") == ["just a few words"]


def test_document_vector_is_the_average_of_its_chunk_vectors():
    def fake_encode(texts):  # stands in for the model: "x..." chunks -> [1, 0], others -> [0, 1]
        return np.array([[1.0, 0.0] if t.startswith("x") else [0.0, 1.0] for t in texts])

    long_doc = " ".join(["x"] * 150 + ["y"] * 150)  # chunks start at words 0, 120, 240 -> x, x, y
    vectors = embed_documents([long_doc, "y y y"], fake_encode)
    assert np.allclose(vectors[0], np.array([2, 1]) / np.sqrt(5))  # average of x, x, y, then length 1
    assert np.allclose(vectors[1], [0, 1])


def test_cosine_similarity_ignores_length():
    job = np.array([1.0, 0.0])
    resumes = np.array([[2.0, 0.0], [0.0, 3.0], [1.0, 1.0]])
    assert np.allclose(cosine_scores(job, resumes), [1.0, 0.0, 0.7071], atol=1e-4)


def test_rank_is_best_first_and_keeps_ties_in_order():
    assert rank([0.2, 0.9, 0.5, 0.9]) == [1, 3, 2, 0]


def test_keywords_reward_shared_rare_words():
    scores = keyword_scores("hadoop hive spark developer", ["java spring developer", "hadoop hive spark pipelines"])
    assert scores[1] > scores[0]


def test_meaning_and_keywords_count_equally():
    # Rescaled to the same spread, two opposite rankings cancel out exactly.
    assert np.allclose(combined_scores([0.6, 0.4, 0.5], [0.1, 0.3, 0.2]), [0, 0, 0])
    assert np.allclose(standardise([5, 5, 5]), [0, 0, 0])  # no spread means no information


def test_whole_pipeline_ranks_the_matching_resume_first():
    def fake_encode(texts):  # stand-in for the model: is the text about Hadoop?
        return np.array([[1.0, 0.1] if "hadoop" in t.lower() else [0.1, 1.0] for t in texts])

    resumes = sorted(FIXTURES.glob("*.txt"))
    results = screen("Hadoop developer: Hive, Spark, Sqoop.", resumes, fake_encode)
    best = results[0]
    assert best["file"] == "hadoop_engineer.txt"
    assert best["matched_skills"] == ["Hadoop", "Hive", "Spark"]
    assert best["missing_skills"] == ["Sqoop"]
