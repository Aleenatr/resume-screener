"""Step 2 - clean the raw text.

There are two cleaners, because the two consumers want different things:

- clean_for_model() keeps capital letters and punctuation. The sentence
  transformer was trained on ordinary sentences, so stripping punctuation
  (what the first version did) only throws information away.
- clean_for_keywords() lowercases everything for keyword matching, but keeps
  the symbols that are part of skill names. The first version deleted every
  character that wasn't a letter or digit, which turned "C++" and "C#" into "c".

Both start the same way (clean_lines): repair broken characters, then remove
contact details, so the model never sees a candidate's name, email, phone
number or profile links. That is "blind screening": the score can only come
from what the person has done.
"""
import re

# Text saved as UTF-8 but read back as Latin-1 turns "ï" into "Ã¯" and the
# bullet "•" into "â" + "\x80" + "¢". The public dataset is full of this.
# A broken character is one lead character followed by 1-3 continuation
# characters, exactly like the UTF-8 bytes it came from, so encoding it back
# to bytes and decoding those bytes as UTF-8 restores the original.
_BROKEN = re.compile(
    r"[Â-ß][\u0080-¿]"         # was a 2-byte character
    r"|[à-ï][\u0080-¿]{2}"     # was a 3-byte character
    r"|[ð-ô][\u0080-¿]{3}"     # was a 4-byte character
)

_EMAIL = re.compile(r"[\w.+-]+@[\w-]+(?:\.[\w-]+)+")
_LINK = re.compile(r"(?:https?://|www\.)\S+|\b(?:linkedin|github)\.com/\S*", re.IGNORECASE)
_PHONE = re.compile(r"(?<![\w+])(?:\+?\d{1,3}[\s-]?)?\d{5}[\s-]?\d{5}(?!\d)")
_BULLETS = re.compile("[•●▪◦■►➢❖✓✔·*]")


def fix_broken_characters(text):
    """Repair text that was decoded with the wrong encoding ("NaÃ¯ve" -> "Naïve")."""
    def repair(match):
        try:
            return match.group().encode("latin-1").decode("utf-8")
        except UnicodeError:
            return match.group()  # it only looked broken - leave it alone
    return _BROKEN.sub(repair, text).replace(" ", " ")


def remove_contact_details(text, name=None):
    """Blind screening: drop email addresses, phone numbers, links and the name."""
    text = _EMAIL.sub(" ", text)
    text = _LINK.sub(" ", text)
    text = _PHONE.sub(" ", text)
    if name:
        text = re.sub(re.escape(name), " ", text, flags=re.IGNORECASE)
    return text


def clean_lines(text, name=None):
    """Fixed and anonymised, but line breaks kept (the summary needs them)."""
    return remove_contact_details(fix_broken_characters(text), name)


def clean_for_model(text, name=None):
    """What the sentence transformer reads: one tidy line of normal text."""
    text = _BULLETS.sub(" ", clean_lines(text, name))
    return re.sub(r"\s+", " ", text).strip()


def clean_for_keywords(text, name=None):
    """What keyword matching reads: lowercase, but "c++", "c#" and ".net" survive."""
    text = clean_for_model(text, name).lower()
    text = re.sub(r"[^a-z0-9+#./\s-]", " ", text)
    return re.sub(r"\s+", " ", text).strip()
