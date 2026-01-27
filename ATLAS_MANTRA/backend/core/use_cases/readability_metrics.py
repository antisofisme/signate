"""
Readability Metrics Module for MANTRA Validator

Implements standard readability formulas:
- Flesch-Kincaid Grade Level (US grade level)
- Flesch Reading Ease (0-100 score)
- Gunning Fog Index (years of education)
- SMOG Index (Simple Measure of Gobbledygook)
- Automated Readability Index (ARI)

Target ranges for technical decisions:
- Flesch-Kincaid Grade: 8-14 (High School to College)
- Flesch Reading Ease: 30-60 (Difficult to Fairly Difficult)
- Gunning Fog: 10-15 (Hard to Difficult)

References:
- https://en.wikipedia.org/wiki/Flesch%E2%80%93Kincaid_readability_tests
- https://en.wikipedia.org/wiki/Gunning_fog_index
- https://en.wikipedia.org/wiki/SMOG
"""

from dataclasses import dataclass
from typing import List, Tuple, Optional
import re
import math


@dataclass
class ReadabilityScore:
    """Complete readability assessment."""
    flesch_kincaid_grade: float  # US grade level (1-18+)
    flesch_reading_ease: float   # 0-100 (higher = easier)
    gunning_fog: float           # Years of education needed
    smog_index: float            # Years of education needed
    ari: float                   # Automated Readability Index

    # Derived assessments
    grade_level: str             # Elementary, Middle, High, College, Graduate
    is_appropriate: bool         # True if within target range for technical docs
    complexity_warning: Optional[str]  # Warning if too complex or too simple

    # Raw metrics
    word_count: int
    sentence_count: int
    syllable_count: int
    complex_word_count: int      # Words with 3+ syllables
    char_count: int


# =============================================================================
# Syllable Counting
# =============================================================================

# Common suffixes that don't add syllables
SILENT_SUFFIXES = {'es', 'ed', 'e'}

# Vowels for syllable detection
VOWELS = set('aeiouy')

# Words with known syllable counts (exceptions)
SYLLABLE_EXCEPTIONS = {
    'area': 3, 'idea': 3, 'create': 2, 'created': 3,
    'database': 3, 'interface': 3, 'microservice': 4,
    'postgresql': 4, 'kubernetes': 4, 'architecture': 4,
    'implementation': 5, 'infrastructure': 4, 'authentication': 5,
    'authorization': 5, 'configuration': 5, 'orchestration': 4,
    'containerization': 6, 'virtualization': 6, 'scalability': 5,
    'availability': 6, 'reliability': 5, 'maintainability': 6,
    'observability': 6, 'idempotent': 4, 'asynchronous': 5,
    'synchronous': 4, 'monolithic': 4, 'distributed': 4,
    'decentralized': 5, 'centralized': 4, 'normalized': 4,
    'denormalized': 5, 'serialization': 6, 'deserialization': 7,
}


def count_syllables(word: str) -> int:
    """
    Count syllables in a word using vowel groups method.

    This is an approximation that works well for English text.
    """
    word = word.lower().strip()

    # Check exceptions first
    if word in SYLLABLE_EXCEPTIONS:
        return SYLLABLE_EXCEPTIONS[word]

    # Remove non-alphabetic characters
    word = re.sub(r'[^a-z]', '', word)

    if not word:
        return 0

    if len(word) <= 3:
        return 1

    # Count vowel groups
    syllables = 0
    prev_was_vowel = False

    for i, char in enumerate(word):
        is_vowel = char in VOWELS

        if is_vowel and not prev_was_vowel:
            syllables += 1

        prev_was_vowel = is_vowel

    # Adjust for silent 'e' at end
    if word.endswith('e') and syllables > 1:
        syllables -= 1

    # Adjust for 'le' ending (e.g., "table", "handle")
    if word.endswith('le') and len(word) > 2 and word[-3] not in VOWELS:
        syllables += 1

    # Adjust for common suffixes
    if word.endswith('ed'):
        # 'ed' adds syllable only if preceded by 't' or 'd'
        if len(word) > 2 and word[-3] in 'td':
            syllables += 0  # Already counted
        elif syllables > 1:
            syllables -= 0  # Silent 'ed'

    # Minimum 1 syllable
    return max(1, syllables)


def is_complex_word(word: str) -> bool:
    """
    Determine if a word is 'complex' (3+ syllables).

    Excludes proper nouns and common suffixes per Gunning Fog rules.
    """
    word = word.lower().strip()

    # Remove common suffixes that don't indicate complexity
    if word.endswith('ing') or word.endswith('ed') or word.endswith('es'):
        base = re.sub(r'(ing|ed|es)$', '', word)
        if count_syllables(base) < 3:
            return False

    return count_syllables(word) >= 3


# =============================================================================
# Text Parsing
# =============================================================================

def tokenize_sentences(text: str) -> List[str]:
    """Split text into sentences."""
    # Handle common abbreviations
    text = re.sub(r'\b(Mr|Mrs|Ms|Dr|Prof|Sr|Jr|vs|etc|i\.e|e\.g)\.',
                  r'\1<DOT>', text, flags=re.IGNORECASE)

    # Split on sentence-ending punctuation
    sentences = re.split(r'[.!?]+', text)

    # Restore dots
    sentences = [s.replace('<DOT>', '.').strip() for s in sentences]

    # Filter empty sentences
    return [s for s in sentences if s and len(s.split()) >= 2]


def tokenize_words(text: str) -> List[str]:
    """Extract words from text."""
    # Remove punctuation except apostrophes
    text = re.sub(r"[^\w\s']", ' ', text)

    # Split and filter
    words = text.split()

    # Filter out numbers and single characters
    return [w for w in words if len(w) > 1 and not w.isdigit()]


def analyze_text(text: str) -> Tuple[int, int, int, int, int]:
    """
    Analyze text and return metrics.

    Returns:
        (word_count, sentence_count, syllable_count, complex_word_count, char_count)
    """
    if not text or not text.strip():
        return (0, 0, 0, 0, 0)

    sentences = tokenize_sentences(text)
    words = tokenize_words(text)

    word_count = len(words)
    sentence_count = max(1, len(sentences))  # At least 1 sentence

    syllable_count = sum(count_syllables(w) for w in words)
    complex_word_count = sum(1 for w in words if is_complex_word(w))
    char_count = sum(len(w) for w in words)

    return (word_count, sentence_count, syllable_count, complex_word_count, char_count)


# =============================================================================
# Readability Formulas
# =============================================================================

def flesch_kincaid_grade(words: int, sentences: int, syllables: int) -> float:
    """
    Calculate Flesch-Kincaid Grade Level.

    Formula: 0.39 * (words/sentences) + 11.8 * (syllables/words) - 15.59

    Returns US grade level (1-18+).
    """
    if words == 0 or sentences == 0:
        return 0.0

    asl = words / sentences  # Average Sentence Length
    asw = syllables / words  # Average Syllables per Word

    grade = 0.39 * asl + 11.8 * asw - 15.59

    return max(0, round(grade, 1))


def flesch_reading_ease(words: int, sentences: int, syllables: int) -> float:
    """
    Calculate Flesch Reading Ease score.

    Formula: 206.835 - 1.015 * (words/sentences) - 84.6 * (syllables/words)

    Returns 0-100 (higher = easier to read).
    Interpretation:
    - 90-100: Very Easy (5th grade)
    - 80-90: Easy (6th grade)
    - 70-80: Fairly Easy (7th grade)
    - 60-70: Standard (8th-9th grade)
    - 50-60: Fairly Difficult (10th-12th grade)
    - 30-50: Difficult (College)
    - 0-30: Very Difficult (College Graduate)
    """
    if words == 0 or sentences == 0:
        return 0.0

    asl = words / sentences
    asw = syllables / words

    score = 206.835 - 1.015 * asl - 84.6 * asw

    return max(0, min(100, round(score, 1)))


def gunning_fog_index(words: int, sentences: int, complex_words: int) -> float:
    """
    Calculate Gunning Fog Index.

    Formula: 0.4 * ((words/sentences) + 100 * (complex_words/words))

    Returns years of formal education needed.
    """
    if words == 0 or sentences == 0:
        return 0.0

    asl = words / sentences
    pcw = (complex_words / words) * 100  # Percentage of complex words

    fog = 0.4 * (asl + pcw)

    return max(0, round(fog, 1))


def smog_index(sentences: int, complex_words: int) -> float:
    """
    Calculate SMOG Index (Simple Measure of Gobbledygook).

    Formula: 1.0430 * sqrt(complex_words * (30/sentences)) + 3.1291

    Returns years of education needed.
    Note: SMOG is designed for 30+ sentences; we extrapolate for shorter texts.
    """
    if sentences == 0:
        return 0.0

    # Extrapolate to 30 sentences
    polysyllables_per_30 = complex_words * (30 / sentences)

    smog = 1.0430 * math.sqrt(polysyllables_per_30) + 3.1291

    return max(0, round(smog, 1))


def automated_readability_index(words: int, sentences: int, chars: int) -> float:
    """
    Calculate Automated Readability Index (ARI).

    Formula: 4.71 * (chars/words) + 0.5 * (words/sentences) - 21.43

    Returns US grade level.
    """
    if words == 0 or sentences == 0:
        return 0.0

    avg_chars = chars / words
    avg_words = words / sentences

    ari = 4.71 * avg_chars + 0.5 * avg_words - 21.43

    return max(0, round(ari, 1))


# =============================================================================
# Grade Level Classification
# =============================================================================

def classify_grade_level(fk_grade: float) -> str:
    """Classify Flesch-Kincaid grade into educational level."""
    if fk_grade <= 5:
        return "Elementary"
    elif fk_grade <= 8:
        return "Middle School"
    elif fk_grade <= 12:
        return "High School"
    elif fk_grade <= 16:
        return "College"
    else:
        return "Graduate"


def assess_appropriateness(
    fk_grade: float,
    fog: float,
    reading_ease: float
) -> Tuple[bool, Optional[str]]:
    """
    Assess if readability is appropriate for technical decisions.

    Target ranges:
    - Flesch-Kincaid Grade: 8-14 (High School to early College)
    - Gunning Fog: 10-15
    - Flesch Reading Ease: 30-60 (Difficult to Fairly Difficult)

    Returns:
        (is_appropriate, warning_message)
    """
    warnings = []

    # Too simple
    if fk_grade < 6:
        warnings.append(f"Text may be too simple (Grade {fk_grade}). Add technical detail.")
    if reading_ease > 70:
        warnings.append(f"Reading ease too high ({reading_ease}). Consider more precise terminology.")

    # Too complex
    if fk_grade > 16:
        warnings.append(f"Text too complex (Grade {fk_grade}). Simplify for broader understanding.")
    if fog > 18:
        warnings.append(f"Gunning Fog too high ({fog}). Reduce sentence length or complex words.")
    if reading_ease < 20:
        warnings.append(f"Reading ease too low ({reading_ease}). Text may be impenetrable.")

    is_appropriate = (6 <= fk_grade <= 16) and (8 <= fog <= 18) and (20 <= reading_ease <= 70)

    warning = "; ".join(warnings) if warnings else None

    return is_appropriate, warning


# =============================================================================
# Main Function
# =============================================================================

def calculate_readability(text: str) -> ReadabilityScore:
    """
    Calculate comprehensive readability metrics for text.

    Args:
        text: Input text to analyze

    Returns:
        ReadabilityScore with all metrics and assessments
    """
    # Analyze text
    word_count, sentence_count, syllable_count, complex_count, char_count = analyze_text(text)

    # Handle empty/short text
    if word_count < 3:
        return ReadabilityScore(
            flesch_kincaid_grade=0,
            flesch_reading_ease=0,
            gunning_fog=0,
            smog_index=0,
            ari=0,
            grade_level="Unknown",
            is_appropriate=False,
            complexity_warning="Text too short for readability analysis",
            word_count=word_count,
            sentence_count=sentence_count,
            syllable_count=syllable_count,
            complex_word_count=complex_count,
            char_count=char_count
        )

    # Calculate metrics
    fk_grade = flesch_kincaid_grade(word_count, sentence_count, syllable_count)
    fk_ease = flesch_reading_ease(word_count, sentence_count, syllable_count)
    fog = gunning_fog_index(word_count, sentence_count, complex_count)
    smog = smog_index(sentence_count, complex_count)
    ari = automated_readability_index(word_count, sentence_count, char_count)

    # Classify and assess
    grade_level = classify_grade_level(fk_grade)
    is_appropriate, warning = assess_appropriateness(fk_grade, fog, fk_ease)

    return ReadabilityScore(
        flesch_kincaid_grade=fk_grade,
        flesch_reading_ease=fk_ease,
        gunning_fog=fog,
        smog_index=smog,
        ari=ari,
        grade_level=grade_level,
        is_appropriate=is_appropriate,
        complexity_warning=warning,
        word_count=word_count,
        sentence_count=sentence_count,
        syllable_count=syllable_count,
        complex_word_count=complex_count,
        char_count=char_count
    )


# =============================================================================
# Technical Vocabulary (Domain-Aware Readability)
# =============================================================================

# Technical terms that should NOT penalize readability
# These are necessary for precision in technical decisions
TECHNICAL_VOCABULARY = {
    # Databases
    'postgresql', 'postgres', 'mysql', 'mongodb', 'redis', 'elasticsearch',
    'timescaledb', 'cassandra', 'dynamodb', 'sqlite', 'mariadb', 'couchdb',
    'database', 'schema', 'migration', 'query', 'index', 'transaction',
    'normalization', 'denormalization', 'replication', 'sharding', 'partitioning',

    # Architecture
    'microservices', 'microservice', 'monolithic', 'monolith', 'serverless',
    'architecture', 'infrastructure', 'scalability', 'availability', 'reliability',
    'distributed', 'decentralized', 'centralized', 'containerization', 'orchestration',
    'kubernetes', 'docker', 'nomad', 'consul', 'terraform', 'ansible',
    'api', 'rest', 'restful', 'graphql', 'grpc', 'websocket', 'webhook',
    'gateway', 'loadbalancer', 'proxy', 'nginx', 'traefik', 'envoy',

    # Programming
    'asynchronous', 'synchronous', 'async', 'await', 'concurrent', 'parallel',
    'idempotent', 'idempotency', 'middleware', 'endpoint', 'payload', 'serialization',
    'deserialization', 'marshalling', 'unmarshalling', 'callback', 'promise',
    'typescript', 'javascript', 'python', 'fastapi', 'flask', 'django',
    'react', 'vue', 'angular', 'nextjs', 'nuxt', 'vite', 'webpack',

    # Security
    'authentication', 'authorization', 'oauth', 'jwt', 'token', 'encryption',
    'decryption', 'hashing', 'bcrypt', 'argon', 'ssl', 'tls', 'https',
    'cors', 'csrf', 'xss', 'injection', 'sanitization', 'validation',
    'rbac', 'abac', 'acl', 'permission', 'role', 'scope',

    # DevOps & Infrastructure
    'deployment', 'ci', 'cd', 'pipeline', 'workflow', 'artifact',
    'container', 'pod', 'node', 'cluster', 'namespace', 'service',
    'ingress', 'egress', 'configmap', 'secret', 'volume', 'mount',
    'monitoring', 'logging', 'alerting', 'observability', 'metrics',
    'prometheus', 'grafana', 'loki', 'jaeger', 'zipkin', 'datadog',

    # Messaging & Events
    'queue', 'broker', 'publisher', 'subscriber', 'consumer', 'producer',
    'rabbitmq', 'kafka', 'nats', 'redis', 'celery', 'eventbus',
    'event', 'message', 'topic', 'partition', 'offset', 'ack',

    # Caching & Storage
    'cache', 'caching', 'cdn', 'cloudflare', 'minio', 's3', 'blob',
    'bucket', 'object', 'presigned', 'multipart', 'streaming',

    # Data & Analytics
    'json', 'yaml', 'xml', 'csv', 'parquet', 'avro', 'protobuf',
    'etl', 'elt', 'datawarehouse', 'datalake', 'analytics', 'aggregation',
    'timeseries', 'realtime', 'batch', 'streaming', 'windowing',

    # Testing
    'unittest', 'integration', 'e2e', 'mock', 'stub', 'fixture',
    'pytest', 'jest', 'vitest', 'playwright', 'cypress', 'selenium',

    # General Technical
    'backend', 'frontend', 'fullstack', 'devops', 'sre', 'platform',
    'component', 'module', 'service', 'handler', 'controller', 'repository',
    'domain', 'entity', 'aggregate', 'valueobject', 'dto', 'model',
    'interface', 'abstract', 'implementation', 'dependency', 'injection',
    'configuration', 'environment', 'variable', 'parameter', 'argument',
}


def count_technical_terms(text: str) -> Tuple[int, List[str]]:
    """
    Count technical terms in text.

    Returns:
        (count, list of found terms)
    """
    words = text.lower().split()
    words = [re.sub(r'[^\w]', '', w) for w in words]

    found_terms = []
    for word in words:
        if word in TECHNICAL_VOCABULARY:
            found_terms.append(word)

    return len(found_terms), found_terms


def calculate_domain_aware_readability(text: str) -> ReadabilityScore:
    """
    Calculate readability with adjustment for technical vocabulary.

    Technical terms don't penalize readability because they are
    necessary for precision in technical decisions.

    Adjustment: Each 3 technical terms reduces perceived grade by 0.5
    Maximum adjustment: 4 grade levels
    """
    # Get base readability
    base = calculate_readability(text)

    if base.word_count < 5:
        return base

    # Count technical terms
    tech_count, found_terms = count_technical_terms(text)

    # Calculate adjustment (every 3 tech terms = -0.5 grade level)
    # But cap at 4 grade levels adjustment
    adjustment = min(tech_count / 3 * 0.5, 4.0)

    # Adjust Flesch-Kincaid grade
    adjusted_grade = max(0, base.flesch_kincaid_grade - adjustment)

    # Re-assess appropriateness with adjusted grade
    is_appropriate, warning = assess_appropriateness(
        adjusted_grade, base.gunning_fog, base.flesch_reading_ease
    )

    # Add note about technical adjustment
    if tech_count > 0 and adjustment > 0:
        tech_note = f"Technical vocabulary detected ({tech_count} terms). Grade adjusted from {base.flesch_kincaid_grade} to {adjusted_grade:.1f}."
        if warning:
            warning = tech_note + " " + warning
        else:
            warning = tech_note

    # Create new score with adjusted values
    return ReadabilityScore(
        flesch_kincaid_grade=adjusted_grade,
        flesch_reading_ease=base.flesch_reading_ease,
        gunning_fog=base.gunning_fog,
        smog_index=base.smog_index,
        ari=base.ari,
        grade_level=classify_grade_level(adjusted_grade),
        is_appropriate=is_appropriate,
        complexity_warning=warning,
        word_count=base.word_count,
        sentence_count=base.sentence_count,
        syllable_count=base.syllable_count,
        complex_word_count=base.complex_word_count,
        char_count=base.char_count
    )


# =============================================================================
# Scoring Helper for Quality Module
# =============================================================================

def score_readability(text: str, target_min_grade: float = 8, target_max_grade: float = 14) -> Tuple[int, List[str]]:
    """
    Score readability for quality assessment.

    Returns:
        (score out of 5, list of suggestions)
    """
    if not text or len(text.strip()) < 10:
        return 0, ["Text too short for readability analysis"]

    metrics = calculate_readability(text)
    score = 5  # Start with perfect score
    suggestions = []

    # Flesch-Kincaid Grade Level check
    if metrics.flesch_kincaid_grade < target_min_grade - 2:
        score -= 2
        suggestions.append(f"Text too simple (Grade {metrics.flesch_kincaid_grade}). Add technical precision.")
    elif metrics.flesch_kincaid_grade < target_min_grade:
        score -= 1
        suggestions.append(f"Consider adding more technical detail (Grade {metrics.flesch_kincaid_grade}).")
    elif metrics.flesch_kincaid_grade > target_max_grade + 2:
        score -= 2
        suggestions.append(f"Text too complex (Grade {metrics.flesch_kincaid_grade}). Simplify language.")
    elif metrics.flesch_kincaid_grade > target_max_grade:
        score -= 1
        suggestions.append(f"Consider simplifying slightly (Grade {metrics.flesch_kincaid_grade}).")

    # Gunning Fog check
    if metrics.gunning_fog > 18:
        score -= 1
        suggestions.append(f"Reduce sentence length or complex words (Fog: {metrics.gunning_fog}).")

    return max(0, score), suggestions


def serialize_readability(metrics: ReadabilityScore) -> dict:
    """Serialize ReadabilityScore to dict for API response."""
    return {
        'flesch_kincaid_grade': metrics.flesch_kincaid_grade,
        'flesch_reading_ease': metrics.flesch_reading_ease,
        'gunning_fog': metrics.gunning_fog,
        'smog_index': metrics.smog_index,
        'ari': metrics.ari,
        'grade_level': metrics.grade_level,
        'is_appropriate': metrics.is_appropriate,
        'complexity_warning': metrics.complexity_warning,
        'word_count': metrics.word_count,
        'sentence_count': metrics.sentence_count,
        'syllable_count': metrics.syllable_count,
        'complex_word_count': metrics.complex_word_count,
    }
