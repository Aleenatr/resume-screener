from screener.skills import find_skills


def test_matches_whole_words_only():
    # "java" must not fire inside "javascript", nor "sql" inside "nosql".
    assert find_skills("JavaScript and NoSQL databases") == ["JavaScript"]


def test_a_sql_database_implies_sql():
    assert find_skills("Tuned MySQL queries") == ["SQL", "MySQL"]


def test_matches_skills_that_contain_symbols():
    assert find_skills("C++, C# and ASP.NET") == ["C++", "C#", ".NET"]


def test_ignores_single_letter_languages():
    assert find_skills("Grade C in R block") == []
