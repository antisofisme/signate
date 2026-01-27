"""
Detailed Content Validation Module (Q-026 to Q-030)

Part of MICS Long Content Strategy implementation.
Validates the Layer B content (detailed_content, sections).

Focus on STRUCTURE, not LENGTH - long content is expected here.

Rules:
- Q-026: Has headers/structure if content is long
- Q-027: Code blocks are valid (language identifiers)
- Q-028: Sections are properly typed
- Q-029: Has examples if content mentions rules
- Q-030: Content aligns with statement
"""

from dataclasses import dataclass
from typing import List, Dict, Any, Tuple, Optional
import re

from ..domain.schema import SectionType


@dataclass
class DetailedContentDimension:
    """Quality score for detailed content."""
    dimension: str = "detailed_content"
    score: int = 0
    max_score: int = 20
    rules_passed: List[str] = None
    rules_failed: List[str] = None
    suggestions: List[str] = None

    def __post_init__(self):
        if self.rules_passed is None:
            self.rules_passed = []
        if self.rules_failed is None:
            self.rules_failed = []
        if self.suggestions is None:
            self.suggestions = []


# Valid code block languages (common ones)
VALID_CODE_LANGUAGES = {
    '', 'text', 'plain',
    # Web
    'typescript', 'ts', 'javascript', 'js', 'jsx', 'tsx',
    'html', 'css', 'scss', 'sass', 'less',
    'json', 'yaml', 'yml', 'xml', 'toml',
    # Backend
    'python', 'py', 'java', 'kotlin', 'scala',
    'go', 'golang', 'rust', 'rs', 'c', 'cpp', 'c++', 'csharp', 'cs',
    'ruby', 'rb', 'php', 'perl', 'swift',
    # Database
    'sql', 'postgresql', 'mysql', 'graphql', 'gql',
    # Shell/Config
    'bash', 'sh', 'shell', 'zsh', 'powershell', 'ps1',
    'dockerfile', 'docker', 'nginx', 'apache',
    # Other
    'markdown', 'md', 'diff', 'makefile', 'cmake',
    'mermaid', 'plantuml', 'ascii', 'diagram',
}

# Valid section types
VALID_SECTION_TYPES = {t.value for t in SectionType}

# Keywords that indicate rules/requirements
RULE_KEYWORDS = {
    'must', 'shall', 'should', 'cannot', 'must not', 'shall not',
    'required', 'prohibited', 'mandatory', 'forbidden',
    'always', 'never', 'rule', 'constraint', 'limitation'
}


def score_detailed_content_quality(record: Dict[str, Any]) -> Tuple[int, DetailedContentDimension]:
    """
    Score detailed_content quality (Q-026 to Q-030).

    Focus on STRUCTURE validation, not length.
    Long content is expected and welcome in detailed_content.

    Args:
        record: Decision record with detailed_content and sections

    Returns:
        (score, dimension) tuple
    """
    detailed_content = record.get('detailed_content') or ''
    sections = record.get('sections') or []
    statement = record.get('statement') or ''

    score = 0
    rules_passed = []
    rules_failed = []
    suggestions = []

    # If no detailed content, return early with neutral score
    if not detailed_content and not sections:
        return 0, DetailedContentDimension(
            score=0,
            max_score=20,
            rules_passed=['Q-026'],  # Optional field - not having it is OK
            rules_failed=[],
            suggestions=[]
        )

    word_count = len(detailed_content.split()) if detailed_content else 0

    # Q-026: Has headers/structure if content is long (4 points)
    has_headers = bool(re.search(r'^#{1,3}\s+.+', detailed_content, re.MULTILINE)) if detailed_content else False
    has_sections = len(sections) > 0

    if word_count <= 200:
        # Short content doesn't need headers
        score += 4
        rules_passed.append('Q-026')
    elif has_headers or has_sections:
        # Long content has structure
        score += 4
        rules_passed.append('Q-026')
    else:
        # Long content without structure
        score += 1
        rules_failed.append('Q-026')
        suggestions.append(
            f'Content is {word_count} words. Add Markdown headers (## Section) '
            'or use sections field for better organization.'
        )

    # Q-027: Code blocks are valid (4 points)
    if detailed_content:
        code_blocks = re.findall(r'```(\w*)\n', detailed_content)

        if not code_blocks:
            # No code blocks - that's fine
            score += 4
            rules_passed.append('Q-027')
        else:
            invalid_langs = [
                lang for lang in code_blocks
                if lang.lower() not in VALID_CODE_LANGUAGES
            ]

            if not invalid_langs:
                score += 4
                rules_passed.append('Q-027')
            else:
                score += 2
                rules_failed.append('Q-027')
                suggestions.append(
                    f'Unknown code block languages: {", ".join(invalid_langs)}. '
                    'Use standard identifiers like typescript, python, bash.'
                )
    else:
        score += 4
        rules_passed.append('Q-027')

    # Q-028: Sections are properly typed (4 points)
    if sections:
        section_types = [s.get('section_type') if isinstance(s, dict) else getattr(s, 'section_type', None) for s in sections]
        invalid_types = [t for t in section_types if t and str(t) not in VALID_SECTION_TYPES]

        if not invalid_types:
            score += 4
            rules_passed.append('Q-028')
        else:
            score += 2
            rules_failed.append('Q-028')
            suggestions.append(
                f'Invalid section types: {", ".join(str(t) for t in invalid_types)}. '
                f'Valid types: {", ".join(VALID_SECTION_TYPES)}.'
            )
    else:
        # No sections is fine
        score += 4
        rules_passed.append('Q-028')

    # Q-029: Has examples if content mentions rules (4 points)
    content_lower = detailed_content.lower() if detailed_content else ''
    mentions_rules = any(kw in content_lower for kw in RULE_KEYWORDS)

    has_examples = (
        'example' in content_lower or
        '// good' in content_lower or
        '// bad' in content_lower or
        '```' in detailed_content or  # Code blocks are examples
        any(
            (s.get('section_type') if isinstance(s, dict) else getattr(s, 'section_type', None)) == 'EXAMPLES'
            for s in sections
        )
    )

    if not mentions_rules:
        # No rules mentioned - examples not required
        score += 4
        rules_passed.append('Q-029')
    elif has_examples:
        # Has rules and examples
        score += 4
        rules_passed.append('Q-029')
    else:
        # Has rules but no examples
        score += 2
        rules_failed.append('Q-029')
        suggestions.append(
            'Content mentions rules but has no examples. '
            'Add code examples showing good/bad patterns.'
        )

    # Q-030: Content aligns with statement (4 points)
    statement_lower = statement.lower()

    # Extract meaningful words from statement (>3 chars, not common words)
    common_words = {
        'the', 'and', 'for', 'are', 'but', 'not', 'you', 'all', 'can',
        'her', 'was', 'one', 'our', 'out', 'has', 'have', 'been', 'will',
        'with', 'this', 'that', 'from', 'they', 'must', 'should', 'shall'
    }
    statement_words = set(
        word for word in re.findall(r'\b\w{4,}\b', statement_lower)
        if word not in common_words
    )

    if not statement_words:
        # No significant words in statement
        score += 4
        rules_passed.append('Q-030')
    elif not detailed_content:
        # No detailed content to check
        score += 4
        rules_passed.append('Q-030')
    else:
        # Check how many statement words appear in content
        words_in_content = sum(1 for w in statement_words if w in content_lower)
        alignment_ratio = words_in_content / len(statement_words) if statement_words else 0

        if alignment_ratio >= 0.5:
            score += 4
            rules_passed.append('Q-030')
        elif alignment_ratio >= 0.25:
            score += 2
            rules_failed.append('Q-030')
            suggestions.append(
                'Detailed content could better align with statement. '
                'Ensure the content elaborates on the key terms.'
            )
        else:
            score += 0
            rules_failed.append('Q-030')
            suggestions.append(
                'Detailed content appears disconnected from statement. '
                'The specification should directly relate to the decision summary.'
            )

    return score, DetailedContentDimension(
        score=score,
        max_score=20,
        rules_passed=rules_passed,
        rules_failed=rules_failed,
        suggestions=suggestions
    )


def has_detailed_content(record: Dict[str, Any]) -> bool:
    """Check if record has any Layer B content."""
    detailed_content = record.get('detailed_content')
    sections = record.get('sections')

    return bool(detailed_content) or bool(sections)


def estimate_content_tokens(record: Dict[str, Any], detail_level: str = 'standard') -> int:
    """
    Estimate token count for a decision at given detail level.

    Token estimates:
    - micro: ~100 tokens (content_summary only)
    - standard: ~500 tokens (statement + rationale + constraints)
    - detailed: ~2000+ tokens (full content)
    - sections: variable (specific sections)

    Args:
        record: Decision record
        detail_level: One of 'micro', 'standard', 'detailed', 'sections'

    Returns:
        Estimated token count
    """
    # Rough estimate: 1 token ~= 4 characters or 0.75 words

    if detail_level == 'micro':
        summary = record.get('content_summary') or record.get('statement', '')[:200]
        return len(summary.split()) * 1.3  # ~100 tokens

    if detail_level == 'standard':
        statement = record.get('statement', '')
        rationale = record.get('rationale', '')
        constraints = record.get('constraints', [])
        constraint_text = ' '.join(
            c.get('statement', '') if isinstance(c, dict) else str(c)
            for c in constraints
        )
        total_words = len(f"{statement} {rationale} {constraint_text}".split())
        return int(total_words * 1.3)  # ~500 tokens

    if detail_level == 'detailed':
        statement = record.get('statement', '')
        rationale = record.get('rationale', '')
        detailed = record.get('detailed_content', '')
        sections_text = ' '.join(
            s.get('content', '') if isinstance(s, dict) else str(s)
            for s in record.get('sections', [])
        )
        total_words = len(f"{statement} {rationale} {detailed} {sections_text}".split())
        return int(total_words * 1.3)

    # sections - estimate based on what's there
    sections = record.get('sections', [])
    sections_text = ' '.join(
        s.get('content', '') if isinstance(s, dict) else str(s)
        for s in sections
    )
    return int(len(sections_text.split()) * 1.3)
