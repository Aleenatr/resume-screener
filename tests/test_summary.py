from screener.summary import split_sentences, summarize

TEXT = """Built machine learning models for fraud detection in Python.
Deployed the fraud detection models as REST APIs used by three teams.
Enjoys cricket and reading on weekends with friends and family.
Improved fraud detection precision by tuning the machine learning models.
Hobbies."""


def test_splits_at_sentence_ends_line_breaks_and_bullets():
    assert split_sentences("One. Two\n• Three") == ["One.", "Two", "Three"]


def test_picks_the_most_representative_sentences_in_original_order():
    # "fraud", "detection" and "models" repeat most, so the sentences built from
    # them win; the hobbies line shares nothing and loses.
    assert summarize(TEXT, n_sentences=2) == (
        "Built machine learning models for fraud detection in Python. "
        "Improved fraud detection precision by tuning the machine learning models."
    )


def test_empty_text_gives_empty_summary():
    assert summarize("") == ""


def test_rejoins_sentences_a_pdf_wrapped_onto_two_lines():
    wrapped = "SUMMARY\nBackend developer with 1 year of experience in Django and\nPostgreSQL.\n- Built REST APIs."
    assert split_sentences(wrapped) == [
        "SUMMARY",
        "Backend developer with 1 year of experience in Django and PostgreSQL.",
        "Built REST APIs.",
    ]


def test_keyword_lists_are_not_quoted_as_sentences():
    text = "Python, Django, Flask, SQL, Docker, AWS, Git, Linux\nBuilt and deployed Django services on AWS with Docker."
    assert summarize(text) == "Built and deployed Django services on AWS with Docker."
