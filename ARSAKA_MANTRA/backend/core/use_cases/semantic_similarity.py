"""
Semantic Similarity Module for MANTRA Validator

Provides semantic similarity calculation between texts using:
1. Sentence-BERT (if sentence-transformers is available) - Most accurate
2. TF-IDF Cosine Similarity (fallback) - Lightweight but less semantic

SBERT produces 384-dimensional embeddings that capture semantic meaning,
allowing us to detect similarity even when different words are used.

Usage:
    from semantic_similarity import calculate_semantic_similarity

    score = calculate_semantic_similarity(
        "Use PostgreSQL for all data storage",
        "PostgreSQL was chosen because it provides better reliability"
    )
    # Returns 0.0 to 1.0 (higher = more similar)
"""

from typing import List, Tuple, Optional, Dict, Any
import re
import math
from collections import Counter
from functools import lru_cache

# =============================================================================
# Module State
# =============================================================================

_sbert_model = None
_sbert_available = None


def _check_sbert_available() -> bool:
    """Check if sentence-transformers is available."""
    global _sbert_available
    if _sbert_available is None:
        try:
            from sentence_transformers import SentenceTransformer
            _sbert_available = True
        except ImportError:
            _sbert_available = False
    return _sbert_available


def _get_sbert_model():
    """Get or initialize SBERT model (lazy loading)."""
    global _sbert_model
    if _sbert_model is None and _check_sbert_available():
        from sentence_transformers import SentenceTransformer
        # Use a lightweight but effective model
        # all-MiniLM-L6-v2: 384 dimensions, 80MB, fast
        _sbert_model = SentenceTransformer('all-MiniLM-L6-v2')
    return _sbert_model


# =============================================================================
# SBERT-based Similarity
# =============================================================================

def cosine_similarity_vectors(vec1: List[float], vec2: List[float]) -> float:
    """Calculate cosine similarity between two vectors."""
    if not vec1 or not vec2 or len(vec1) != len(vec2):
        return 0.0

    dot_product = sum(a * b for a, b in zip(vec1, vec2))
    magnitude1 = math.sqrt(sum(a * a for a in vec1))
    magnitude2 = math.sqrt(sum(b * b for b in vec2))

    if magnitude1 == 0 or magnitude2 == 0:
        return 0.0

    return dot_product / (magnitude1 * magnitude2)


def sbert_similarity(text1: str, text2: str) -> float:
    """
    Calculate semantic similarity using Sentence-BERT.

    Returns:
        Similarity score from 0.0 to 1.0
    """
    model = _get_sbert_model()
    if model is None:
        return -1.0  # Indicates SBERT not available

    # Generate embeddings
    embeddings = model.encode([text1, text2], convert_to_numpy=True)

    # Calculate cosine similarity
    similarity = cosine_similarity_vectors(
        embeddings[0].tolist(),
        embeddings[1].tolist()
    )

    # Clamp to [0, 1] range (cosine can be negative for very different texts)
    return max(0.0, min(1.0, similarity))


# =============================================================================
# TF-IDF Fallback (when SBERT not available)
# =============================================================================

# Stop words for TF-IDF
STOP_WORDS = {
    'the', 'a', 'an', 'is', 'are', 'was', 'were', 'be', 'been', 'being',
    'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could',
    'should', 'may', 'might', 'must', 'shall', 'can', 'need', 'to', 'of',
    'in', 'for', 'on', 'with', 'at', 'by', 'from', 'as', 'into', 'through',
    'during', 'before', 'after', 'above', 'below', 'between', 'under',
    'and', 'or', 'but', 'if', 'while', 'this', 'that', 'these', 'those',
    'it', 'its', 'we', 'our', 'they', 'their', 'all', 'each', 'which',
}


def tokenize(text: str) -> List[str]:
    """Tokenize text into words, removing stop words."""
    # Lowercase and extract words
    words = re.findall(r'\b[a-z]+\b', text.lower())
    # Filter stop words and short words
    return [w for w in words if w not in STOP_WORDS and len(w) > 2]


def calculate_tf(tokens: List[str]) -> Dict[str, float]:
    """Calculate term frequency."""
    if not tokens:
        return {}
    counter = Counter(tokens)
    total = len(tokens)
    return {word: count / total for word, count in counter.items()}


def calculate_idf(docs: List[List[str]]) -> Dict[str, float]:
    """Calculate inverse document frequency."""
    if not docs:
        return {}

    # Count documents containing each word
    doc_count = Counter()
    for doc in docs:
        unique_words = set(doc)
        for word in unique_words:
            doc_count[word] += 1

    # Calculate IDF
    total_docs = len(docs)
    return {
        word: math.log(total_docs / count) + 1
        for word, count in doc_count.items()
    }


def tfidf_similarity(text1: str, text2: str) -> float:
    """
    Calculate similarity using TF-IDF cosine similarity.

    This is a lightweight fallback when SBERT is not available.
    It captures lexical similarity with IDF weighting.

    Returns:
        Similarity score from 0.0 to 1.0
    """
    tokens1 = tokenize(text1)
    tokens2 = tokenize(text2)

    if not tokens1 or not tokens2:
        return 0.0

    # Calculate IDF across both documents
    idf = calculate_idf([tokens1, tokens2])

    # Calculate TF for each document
    tf1 = calculate_tf(tokens1)
    tf2 = calculate_tf(tokens2)

    # Get all unique words
    all_words = set(tf1.keys()) | set(tf2.keys())

    # Build TF-IDF vectors
    vec1 = [tf1.get(w, 0) * idf.get(w, 0) for w in all_words]
    vec2 = [tf2.get(w, 0) * idf.get(w, 0) for w in all_words]

    return cosine_similarity_vectors(vec1, vec2)


# =============================================================================
# N-gram Similarity (additional signal)
# =============================================================================

def ngram_similarity(text1: str, text2: str, n: int = 3) -> float:
    """
    Calculate character n-gram similarity (Jaccard).

    Useful for catching typos and morphological variations.
    """
    def get_ngrams(text: str, n: int) -> set:
        text = re.sub(r'[^a-z]', '', text.lower())
        if len(text) < n:
            return {text}
        return {text[i:i+n] for i in range(len(text) - n + 1)}

    ngrams1 = get_ngrams(text1, n)
    ngrams2 = get_ngrams(text2, n)

    if not ngrams1 or not ngrams2:
        return 0.0

    intersection = len(ngrams1 & ngrams2)
    union = len(ngrams1 | ngrams2)

    return intersection / union if union > 0 else 0.0


# =============================================================================
# Main API
# =============================================================================

def calculate_semantic_similarity(
    text1: str,
    text2: str,
    use_sbert: bool = True
) -> Tuple[float, str]:
    """
    Calculate semantic similarity between two texts.

    Uses SBERT if available, falls back to TF-IDF + n-gram hybrid.

    Args:
        text1: First text (e.g., statement)
        text2: Second text (e.g., rationale)
        use_sbert: Whether to attempt SBERT (default True)

    Returns:
        (similarity_score, method_used)
        - similarity_score: 0.0 to 1.0 (higher = more similar)
        - method_used: "sbert", "tfidf_hybrid", or "keyword"
    """
    if not text1 or not text2:
        return 0.0, "empty"

    # Try SBERT first
    if use_sbert and _check_sbert_available():
        try:
            score = sbert_similarity(text1, text2)
            if score >= 0:
                return score, "sbert"
        except Exception:
            pass  # Fall through to fallback

    # Fallback: TF-IDF + n-gram hybrid
    tfidf_score = tfidf_similarity(text1, text2)
    ngram_score = ngram_similarity(text1, text2)

    # Weighted combination: TF-IDF captures semantic, n-gram catches surface
    hybrid_score = 0.7 * tfidf_score + 0.3 * ngram_score

    return hybrid_score, "tfidf_hybrid"


def calculate_coherence_score(
    statement: str,
    rationale: str,
    threshold_excellent: float = 0.5,
    threshold_good: float = 0.3,
    threshold_fair: float = 0.15
) -> Tuple[float, str, str]:
    """
    Calculate coherence score between statement and rationale.

    This is the main function used by quality_scoring.py

    Args:
        statement: The decision statement
        rationale: The decision rationale
        threshold_excellent: Score for full coherence points
        threshold_good: Score for partial coherence points
        threshold_fair: Minimum acceptable coherence

    Returns:
        (coherence_score, assessment, method)
        - coherence_score: 0.0 to 1.0
        - assessment: "excellent", "good", "fair", or "poor"
        - method: "sbert" or "tfidf_hybrid"
    """
    score, method = calculate_semantic_similarity(statement, rationale)

    if score >= threshold_excellent:
        assessment = "excellent"
    elif score >= threshold_good:
        assessment = "good"
    elif score >= threshold_fair:
        assessment = "fair"
    else:
        assessment = "poor"

    return score, assessment, method


# =============================================================================
# Batch Processing (for efficiency)
# =============================================================================

def batch_similarity(
    texts: List[str],
    reference: str
) -> List[Tuple[float, str]]:
    """
    Calculate similarity of multiple texts against a reference.

    More efficient than calling calculate_semantic_similarity repeatedly
    when using SBERT (batches embedding generation).

    Args:
        texts: List of texts to compare
        reference: Reference text to compare against

    Returns:
        List of (similarity_score, method) tuples
    """
    if not texts or not reference:
        return [(0.0, "empty") for _ in texts]

    # Try SBERT batch processing
    if _check_sbert_available():
        try:
            model = _get_sbert_model()
            if model:
                # Batch encode all texts + reference
                all_texts = texts + [reference]
                embeddings = model.encode(all_texts, convert_to_numpy=True)

                ref_embedding = embeddings[-1].tolist()
                results = []

                for i, text in enumerate(texts):
                    text_embedding = embeddings[i].tolist()
                    score = cosine_similarity_vectors(text_embedding, ref_embedding)
                    score = max(0.0, min(1.0, score))
                    results.append((score, "sbert"))

                return results
        except Exception:
            pass  # Fall through to fallback

    # Fallback: individual TF-IDF calculations
    return [
        (
            0.7 * tfidf_similarity(text, reference) +
            0.3 * ngram_similarity(text, reference),
            "tfidf_hybrid"
        )
        for text in texts
    ]


# =============================================================================
# Utility Functions
# =============================================================================

def get_similarity_method() -> str:
    """Get the currently available similarity method."""
    if _check_sbert_available():
        return "sbert"
    return "tfidf_hybrid"


def get_model_info() -> Dict[str, Any]:
    """Get information about the similarity model."""
    if _check_sbert_available():
        return {
            "method": "sbert",
            "model": "all-MiniLM-L6-v2",
            "dimensions": 384,
            "description": "Sentence-BERT embeddings for semantic similarity"
        }
    return {
        "method": "tfidf_hybrid",
        "model": "TF-IDF + Character N-grams",
        "dimensions": "variable",
        "description": "Lightweight lexical similarity (SBERT not available)"
    }
