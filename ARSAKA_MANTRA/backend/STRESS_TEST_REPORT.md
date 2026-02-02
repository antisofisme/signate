================================================================================
MANTRA RETRIEVAL STRESS TEST REPORT
Generated: 2026-01-30T19:13:07.971594
================================================================================

## Summary

| Test | Success Rate | Avg Time | P95 Time | P99 Time |
|------|-------------|----------|----------|----------|
| query_expansion | 86.7% | 0.02ms | 0.03ms | 0.08ms |
| intent_detection | 93.3% | 0.07ms | 0.10ms | 0.23ms |
| dependency_graph | 100.0% | 0.00ms | 0.01ms | 0.03ms |
| conflict_detection | 100.0% | 0.01ms | 0.01ms | 0.04ms |
| combined_retrieval | 100.0% | 0.12ms | 0.25ms | 0.38ms |
| edge_cases | 100.0% | 0.15ms | 1.06ms | 1.06ms |
| concurrent_load | 100.0% | 0.06ms | 0.08ms | 0.12ms |

## Identified Weaknesses

- LOW SUCCESS RATE: query_expansion has 86.7% success rate
- LOW SUCCESS RATE: intent_detection has 93.3% success rate
- ERROR in intent_detection: Expected QueryIntent.FULL, got QueryIntent.PRD_EXPORT

## Recommendations

- Expand intent detection patterns for edge cases
- Add fallback intent for unrecognized patterns
- Add more domain-specific synonym mappings
- Consider using ML-based query expansion