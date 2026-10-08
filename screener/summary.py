"""Step 4 - a short extractive summary using frequency-based sentence scoring.

"Extractive" means we copy the resume's own sentences rather than writing new
ones ("abstractive", which is what an LLM does). The idea is Luhn's, from
1958: the words a writer repeats are what the text is about.

1. Split the resume into sentences (each bullet point counts as one).
2. Count how often each meaningful word appears, ignoring filler words.
3. Divide by the biggest count, so every word weighs between 0 and 1.
4. Score a sentence by the AVERAGE weight of its words. The first version
   used the SUM, which simply rewarded the longest sentences, and it also
   counted filler words like "the" and "and".
5. Return the top sentences in the order they appear in the resume - the
   first version returned them in score order, which reads oddly.
"""
import re
from collections import Counter

STOPWORDS = set("""
a about above after again against all also am an and any are as at be because been before being
below between both but by can could did do does doing down during each etc few for from further had
has have having he her here hers him his how i if in into is it its just me more most my no nor not
now of off on once only or other our out over own same she should so some such than that the their
them then there these they this those through to too under until up us use used using various very
was we well were what when where which while who whom why will with would you your
""".split())

MIN_WORDS, MAX_WORDS = 6, 40  # skip fragments like "Skills:" and run-on lines

_LINE_BULLET = re.compile(r"^(?:[-–*•●▪◦■►➢❖✓✔]|\d+[.)])\s+")
_INLINE_BULLET = re.compile(r"\s*[•●▪◦■►➢❖✓✔*]\s*")
_STOPS_MID_PHRASE = re.compile(r"(?:,|\b(?:and|or|of|with|in|on|to|for|the|a|an|by|from|at|as|using|&))$", re.IGNORECASE)
_SENTENCE_END = re.compile(r"(?<=[.!?])\s+(?=[A-Z0-9])")
_WORD = re.compile(r"[a-z][a-z0-9+#.-]*[a-z0-9+#]|[a-z]")


def _paragraphs(text):
    """Re-join lines that a PDF wrapped in the middle of a sentence.

    The next line only counts as the same sentence carrying on when that is
    obvious: it starts with a small letter, or the line before stops mid-phrase
    (on a comma or a word like "and", "of", "with"). Anything else - a new
    bullet point, a heading, a list of skills - starts a new paragraph.
    """
    paragraphs = []
    for line in text.splitlines():
        line = line.strip()
        if not line:
            paragraphs.append("")  # a blank line: nothing may join across it
            continue
        new_bullet = bool(_LINE_BULLET.match(line))
        line = _LINE_BULLET.sub("", line)
        previous = paragraphs[-1] if paragraphs else ""
        if previous and not new_bullet and (line[0].islower() or _STOPS_MID_PHRASE.search(previous)):
            paragraphs[-1] = f"{previous} {line}"
        else:
            paragraphs.append(line)
    return [p for p in paragraphs if p]


def split_sentences(text):
    """Break text into sentences: paragraphs, then bullet symbols, then sentence ends."""
    sentences = []
    for paragraph in _paragraphs(text):
        for piece in _INLINE_BULLET.split(paragraph):
            sentences += [s.strip() for s in _SENTENCE_END.split(piece) if s.strip()]
    return sentences


def content_words(sentence):
    """The words of a sentence that carry meaning (lowercase, no filler words)."""
    return [w for w in _WORD.findall(sentence.lower()) if w not in STOPWORDS]


def is_keyword_list(sentence):
    """"Python, Django, SQL, Docker" is a list of keywords, not a sentence worth quoting."""
    return sentence.count(",") >= len(sentence.split()) / 2


def summarize(text, n_sentences=3):
    """The n most representative sentences of the text, in their original order."""
    sentences = [s for s in split_sentences(text)
                 if MIN_WORDS <= len(s.split()) <= MAX_WORDS and not is_keyword_list(s)]
    counts = Counter(w for s in sentences for w in content_words(s))
    if not counts:
        return ""
    top_count = max(counts.values())
    weight = {word: count / top_count for word, count in counts.items()}

    def score(sentence):
        words = content_words(sentence)
        return sum(weight[w] for w in words) / len(words) if words else 0.0

    best = sorted(range(len(sentences)), key=lambda i: score(sentences[i]), reverse=True)[:n_sentences]
    chosen = [sentences[i] for i in sorted(best)]
    return " ".join(s if s.endswith((".", "!", "?")) else s + "." for s in chosen)
