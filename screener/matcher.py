"""Step 5 - score every resume against the job, then rank.

Two kinds of score, and the ranking uses both:

1. Semantic similarity (meaning). The job and each resume become vectors with
   the sentence transformer all-MiniLM-L6-v2, and we take cosine similarity.
   This is what notices that "built predictive models" and "machine learning"
   are about the same thing, even with no shared words.

   The model reads at most 256 tokens (about 190 words) and silently ignores
   the rest. On the evaluation set, 64% of resumes are longer than that, and
   55% of all resume text was never seen by the first version, which embedded
   each resume in one go. So each document is cut into overlapping 150-word
   chunks, every chunk is embedded, and the document's vector is the average
   of its chunk vectors.

2. Keyword similarity (TF-IDF). Shared words, where words that are rare across
   the resumes count more ("Hadoop" says much more than "team"). This is what
   the second Colab notebook did.

On 166 de-duplicated resumes (see evaluation/results.md), keywords alone beat
meaning alone, because tech roles are defined by their tools. Averaging the
two did best, so the final ranking is the average of both, after putting
them on the same scale.

Why NumPy: once vectors are scaled to length 1, cosine similarity is just a
dot product, so scoring every resume is one matrix multiplication.
"""
import numpy as np

MODEL_NAME = "all-MiniLM-L6-v2"
CHUNK_WORDS = 150   # comfortably under the 256-token limit
OVERLAP_WORDS = 30  # a sentence cut at a chunk boundary still appears whole in one chunk


def load_encoder(model_name=MODEL_NAME):
    """Return a function that turns a list of strings into a 2-D array of vectors."""
    from sentence_transformers import SentenceTransformer  # slow import, so only when needed

    model = SentenceTransformer(model_name)

    def encode(texts):
        return model.encode(texts, batch_size=32, show_progress_bar=False, convert_to_numpy=True)

    encode.model = model  # kept so callers can reach the tokenizer (the evaluation counts tokens)
    return encode


# --- 1. semantic similarity ---------------------------------------------------

def chunk_words(text, size=CHUNK_WORDS, overlap=OVERLAP_WORDS):
    """Split text into windows of `size` words; neighbouring windows share `overlap` words."""
    words = text.split()
    if len(words) <= size:
        return [" ".join(words)]
    step = size - overlap
    chunks = []
    for start in range(0, len(words), step):
        chunks.append(" ".join(words[start:start + size]))
        if start + size >= len(words):
            break
    return chunks


def to_unit_length(vectors):
    """Scale every vector (row) to length 1, so that a dot product equals cosine similarity."""
    vectors = np.asarray(vectors, dtype=np.float32)
    lengths = np.linalg.norm(vectors, axis=-1, keepdims=True)
    return vectors / np.maximum(lengths, 1e-12)


def embed_documents(documents, encode):
    """One unit-length vector per document: the average of its chunk vectors.

    All chunks of all documents go to the model in one batch (much faster than
    one call per chunk); `owner` remembers which document each chunk came from.
    """
    chunks, owner = [], []
    for doc_index, document in enumerate(documents):
        for chunk in chunk_words(document):
            chunks.append(chunk)
            owner.append(doc_index)
    chunk_vectors = to_unit_length(encode(chunks))
    owner = np.array(owner)
    averages = [chunk_vectors[owner == i].mean(axis=0) for i in range(len(documents))]
    return to_unit_length(np.stack(averages))


def cosine_scores(job_vector, resume_vectors):
    """Cosine similarity between one job and every resume, as one matrix product."""
    return to_unit_length(resume_vectors) @ to_unit_length(job_vector)


# --- 2. keyword similarity ----------------------------------------------------

def keyword_scores(job_text, resume_texts):
    """TF-IDF cosine similarity between the job and each resume.

    Fitted on this job plus these resumes, so "rare" means rare among the
    candidates being compared. Same settings as the second Colab notebook.
    """
    from sklearn.feature_extraction.text import TfidfVectorizer

    vectorizer = TfidfVectorizer(stop_words="english", max_features=1500, ngram_range=(1, 2))
    matrix = vectorizer.fit_transform([job_text] + list(resume_texts))
    return (matrix[1:] @ matrix[0].T).toarray().ravel()  # TF-IDF rows already have length 1


# --- combining and ranking ----------------------------------------------------

def standardise(scores):
    """Rescale to average 0 and spread 1, so two different kinds of score can be averaged fairly."""
    scores = np.asarray(scores, dtype=np.float64)
    spread = scores.std()
    return (scores - scores.mean()) / spread if spread > 0 else np.zeros_like(scores)


def combined_scores(semantic, keyword):
    """The final ranking score: meaning and keywords count equally."""
    return (standardise(semantic) + standardise(keyword)) / 2


def rank(scores):
    """Positions of the scores from best to worst; ties keep their original order."""
    return [int(i) for i in np.argsort(-np.asarray(scores), kind="stable")]
