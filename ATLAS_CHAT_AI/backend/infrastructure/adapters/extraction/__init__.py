"""
Extraction Adapters

LLM-based fact extraction and summarization.
"""

from .llm_fact_extractor import LLMFactExtractor
from .llm_summarizer import LLMSummarizer

__all__ = [
    "LLMFactExtractor",
    "LLMSummarizer",
]
