"""
Tests for MANTRA Retrieval Enhancements

Tests for:
1. RRF (Reciprocal Rank Fusion)
2. Cross-Encoder Reranking
3. Integration with EnhancedRetrievalEngine
"""

import pytest
from typing import Dict, List


# ============================================================================
# TEST: RRF FUSION
# ============================================================================

class TestRRFFusion:
    """Test RRF (Reciprocal Rank Fusion) implementation."""

    def test_rrf_basic(self):
        """Test basic RRF fusion."""
        from core.retrieval.fusion import RRFusion, fuse_rrf

        # Two ranked lists
        vector_scores = {"doc1": 0.95, "doc2": 0.85, "doc3": 0.75}
        keyword_scores = {"doc2": 0.90, "doc3": 0.80, "doc4": 0.70}

        fuser = RRFusion(k=60)
        results = fuser.fuse(
            score_lists=[vector_scores, keyword_scores],
            source_names=["vector", "keyword"],
        )

        # doc2 should be highest (appears in both)
        assert results[0].doc_id == "doc2"
        assert results[0].num_sources == 2

        # Verify all docs are present
        result_ids = [r.doc_id for r in results]
        assert set(result_ids) == {"doc1", "doc2", "doc3", "doc4"}

    def test_rrf_quick_function(self):
        """Test fuse_rrf convenience function."""
        from core.retrieval.fusion import fuse_rrf

        scores1 = {"a": 1.0, "b": 0.8, "c": 0.6}
        scores2 = {"b": 0.9, "c": 0.7, "d": 0.5}

        results = fuse_rrf([scores1, scores2], k=60, top_k=3)

        # Should return (doc_id, score) tuples
        assert len(results) == 3
        assert all(isinstance(r, tuple) for r in results)
        assert all(len(r) == 2 for r in results)

    def test_rrf_vs_linear(self):
        """Compare RRF vs linear fusion results."""
        from core.retrieval.fusion import (
            ScoreFusion, FusionConfig, FusionMethod,
        )

        # Scores with different scales
        vector_scores = {"doc1": 0.99, "doc2": 0.50}  # High variance
        keyword_scores = {"doc2": 0.80, "doc1": 0.20}  # Different ranking

        # RRF fusion
        rrf_fusion = ScoreFusion(FusionConfig(method=FusionMethod.RRF))
        rrf_results = rrf_fusion.fuse([vector_scores, keyword_scores])

        # Linear fusion
        linear_fusion = ScoreFusion(FusionConfig(
            method=FusionMethod.WEIGHTED_LINEAR,
            weights=[0.5, 0.5],
        ))
        linear_results = linear_fusion.fuse([vector_scores, keyword_scores])

        # Both should work, but may have different rankings
        assert len(rrf_results.results) == 2
        assert len(linear_results.results) == 2

    def test_rrf_empty_input(self):
        """Test RRF with empty input."""
        from core.retrieval.fusion import RRFusion

        fuser = RRFusion()
        results = fuser.fuse([])

        assert results == []


# ============================================================================
# TEST: RERANKER
# ============================================================================

class TestReranker:
    """Test reranker implementations."""

    def test_reranker_config(self):
        """Test reranker configuration."""
        from core.retrieval.reranker import (
            Reranker, RerankerConfig, RerankerMethod,
        )

        config = RerankerConfig(
            method=RerankerMethod.CROSS_ENCODER,
            top_k=5,
            model_name="cross-encoder/ms-marco-MiniLM-L-6-v2",
        )

        reranker = Reranker(config)
        assert reranker.config.method == RerankerMethod.CROSS_ENCODER
        assert reranker.config.top_k == 5

    def test_reranker_candidates(self):
        """Test reranker candidate creation."""
        from core.retrieval.reranker import RerankerCandidate

        candidate = RerankerCandidate(
            doc_id="test-123",
            text="This is a test document about API design.",
            original_score=0.85,
            metadata={"code": "TEST-001"},
        )

        assert candidate.doc_id == "test-123"
        assert candidate.original_score == 0.85

    def test_reranker_tfidf_fallback(self):
        """Test TF-IDF fallback reranker."""
        from core.retrieval.reranker import (
            Reranker, RerankerConfig, RerankerMethod,
            RerankerCandidate,
        )

        # Force fallback by using NONE method
        config = RerankerConfig(
            method=RerankerMethod.NONE,
            top_k=3,
        )

        reranker = Reranker(config)

        candidates = [
            RerankerCandidate(
                doc_id="doc1",
                text="Database design patterns for PostgreSQL",
                original_score=0.8,
            ),
            RerankerCandidate(
                doc_id="doc2",
                text="React component architecture",
                original_score=0.7,
            ),
            RerankerCandidate(
                doc_id="doc3",
                text="Database schema optimization techniques",
                original_score=0.6,
            ),
        ]

        response = reranker.rerank(
            query="database design",
            candidates=candidates,
        )

        assert len(response.results) <= 3
        assert response.method_used == RerankerMethod.NONE

    def test_reranker_available_methods(self):
        """Test getting available reranking methods."""
        from core.retrieval.reranker import Reranker

        reranker = Reranker()
        methods = reranker.get_available_methods()

        # NONE should always be available
        from core.retrieval.reranker import RerankerMethod
        assert RerankerMethod.NONE in methods


# ============================================================================
# TEST: SEARCHER WITH RRF
# ============================================================================

class TestSearcherRRF:
    """Test HybridSearcher with RRF fusion."""

    def test_searcher_default_uses_rrf(self):
        """Test that searcher defaults to RRF fusion."""
        from core.retrieval.searcher import SearchConfig, FusionMode

        config = SearchConfig()
        assert config.fusion_mode == FusionMode.RRF

    def test_searcher_config_linear(self):
        """Test searcher with linear fusion."""
        from core.retrieval.searcher import SearchConfig, FusionMode

        config = SearchConfig(
            fusion_mode=FusionMode.LINEAR,
            vector_weight=0.6,
            keyword_weight=0.4,
        )

        assert config.fusion_mode == FusionMode.LINEAR
        assert config.vector_weight == 0.6

    def test_searcher_rrf_k_config(self):
        """Test searcher RRF k parameter."""
        from core.retrieval.searcher import SearchConfig, FusionMode

        config = SearchConfig(
            fusion_mode=FusionMode.RRF,
            rrf_k=30,  # Non-default k
        )

        assert config.rrf_k == 30


# ============================================================================
# TEST: INTEGRATION
# ============================================================================

class TestIntegration:
    """Test full integration of enhancements."""

    def test_imports(self):
        """Test all new imports work."""
        from core.retrieval import (
            # Fusion
            FusionMethod, FusionConfig, FusedResult, FusionResponse,
            ScoreFusion, RRFusion, create_rrf_fusion, fuse_rrf,
            # Reranker
            RerankerMethod, RerankerConfig, RerankerCandidate,
            Reranker, create_reranker, create_fast_reranker,
            # Searcher
            FusionMode, SearchConfig,
        )

        # All imports should work
        assert FusionMethod.RRF.value == "rrf"
        assert RerankerMethod.CROSS_ENCODER.value == "cross_encoder"

    def test_create_enhanced_engine(self):
        """Test creating enhanced engine with new features."""
        from core.retrieval import EnhancedRetrievalEngine

        engine = EnhancedRetrievalEngine()

        # Check reranker is configured
        assert engine.reranker is not None
        assert engine._use_reranking is True

        # Get stats
        stats = engine.get_stats()
        assert "reranker" in stats
        assert "reranking" in stats["features_enabled"]


# ============================================================================
# TEST: PERFORMANCE CHARACTERISTICS
# ============================================================================

class TestPerformance:
    """Test performance characteristics of fusion algorithms."""

    def test_rrf_scales_linearly(self):
        """Test RRF performance scales linearly with document count."""
        import time
        from core.retrieval.fusion import RRFusion

        fuser = RRFusion(k=60)

        # Small set
        small_scores = {f"doc{i}": 0.9 - i * 0.01 for i in range(100)}
        start = time.time()
        fuser.fuse([small_scores, small_scores])
        small_time = time.time() - start

        # Large set
        large_scores = {f"doc{i}": 0.9 - i * 0.001 for i in range(1000)}
        start = time.time()
        fuser.fuse([large_scores, large_scores])
        large_time = time.time() - start

        # Should scale roughly linearly (10x docs = ~10x time, with some tolerance)
        assert large_time < small_time * 20  # Allow 2x overhead


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
