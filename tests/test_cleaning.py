from screener.cleaning import clean_for_keywords, clean_for_model, fix_broken_characters


def test_repairs_text_decoded_with_the_wrong_encoding():
    assert fix_broken_characters("NaÃ¯ve Bayes") == "Naïve Bayes"
    assert fix_broken_characters("â\x80¢ Python") == "• Python"


def test_leaves_normal_accents_alone():
    assert fix_broken_characters("café résumé") == "café résumé"


def test_keyword_cleaning_keeps_symbols_inside_skill_names():
    # The first version turned all three of these into "c" / "aspnet" / "nodejs".
    assert clean_for_keywords("Skills: C++, C#, ASP.NET and Node.js!") == "skills c++ c# asp.net and node.js"


def test_model_cleaning_keeps_punctuation_but_drops_bullets():
    assert clean_for_model("• Built REST APIs.\n• Wrote tests.") == "Built REST APIs. Wrote tests."


def test_blind_screening_removes_name_and_contact_details():
    text = "Priya Sharma\npriya.s@example.com | +91 98765 43210 | linkedin.com/in/priya-s\nPython developer"
    cleaned = clean_for_model(text, name="Priya Sharma")
    for private in ("Priya", "@", "98765", "linkedin"):
        assert private not in cleaned
    assert "Python developer" in cleaned
