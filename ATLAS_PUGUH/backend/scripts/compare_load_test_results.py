#!/usr/bin/env python3
"""
Compare Load Test Results

Compares Phase 1 baseline vs Phase 2 instrumented load test results.

Usage:
    python scripts/compare_load_test_results.py \
        phase1_baseline_stats.csv \
        phase2_instrumented_stats.csv \
        comparison_report.md

Source: Phase 2 Design & Execution Plan - Section 4.4
"""

import sys
import csv
from typing import Dict, Any
from datetime import datetime


def parse_locust_stats(csv_file: str) -> Dict[str, Any]:
    """
    Parse Locust stats CSV file

    Args:
        csv_file: Path to Locust stats CSV file

    Returns:
        Dictionary with aggregated stats
    """
    stats = {
        "total_requests": 0,
        "total_failures": 0,
        "avg_response_time": 0,
        "min_response_time": float('inf'),
        "max_response_time": 0,
        "requests_per_sec": 0,
        "p50": 0,
        "p95": 0,
        "p99": 0,
        "endpoints": []
    }

    with open(csv_file, 'r') as f:
        reader = csv.DictReader(f)

        for row in reader:
            # Skip aggregated row
            if row['Type'] == 'Aggregated':
                stats["total_requests"] = int(row['Request Count'])
                stats["total_failures"] = int(row['Failure Count'])
                stats["avg_response_time"] = float(row['Average Response Time'])
                stats["min_response_time"] = float(row['Min Response Time'])
                stats["max_response_time"] = float(row['Max Response Time'])
                stats["requests_per_sec"] = float(row['Requests/s'])
                stats["p50"] = float(row.get('50%', 0))
                stats["p95"] = float(row.get('95%', 0))
                stats["p99"] = float(row.get('99%', 0))
            else:
                # Individual endpoint stats
                stats["endpoints"].append({
                    "name": row['Name'],
                    "method": row['Type'],
                    "requests": int(row['Request Count']),
                    "failures": int(row['Failure Count']),
                    "avg_time": float(row['Average Response Time']),
                    "rps": float(row['Requests/s'])
                })

    # Calculate failure rate
    stats["failure_rate"] = (stats["total_failures"] / stats["total_requests"] * 100) \
        if stats["total_requests"] > 0 else 0

    return stats


def calculate_improvement(phase1_value: float, phase2_value: float,
                         lower_is_better: bool = True) -> Dict[str, Any]:
    """
    Calculate improvement percentage

    Args:
        phase1_value: Phase 1 metric value
        phase2_value: Phase 2 metric value
        lower_is_better: True if lower values are better (latency)

    Returns:
        Dictionary with improvement data
    """
    if phase1_value == 0:
        return {
            "percent": 0,
            "symbol": "→",
            "interpretation": "N/A"
        }

    diff = phase1_value - phase2_value
    percent = (diff / phase1_value) * 100

    if lower_is_better:
        # For latency, lower is better
        if percent > 0:
            symbol = "✓"
            interpretation = "Better"
        elif percent < 0:
            symbol = "✗"
            interpretation = "Worse"
        else:
            symbol = "→"
            interpretation = "Same"
    else:
        # For throughput, higher is better
        if percent > 0:
            symbol = "✗"
            interpretation = "Worse"
        elif percent < 0:
            symbol = "✓"
            interpretation = "Better"
            percent = abs(percent)
        else:
            symbol = "→"
            interpretation = "Same"

    return {
        "percent": abs(percent),
        "symbol": symbol,
        "interpretation": interpretation
    }


def generate_comparison_report(phase1_stats: Dict[str, Any],
                              phase2_stats: Dict[str, Any],
                              output_file: str):
    """
    Generate markdown comparison report

    Args:
        phase1_stats: Phase 1 baseline stats
        phase2_stats: Phase 2 instrumented stats
        output_file: Output markdown file path
    """
    report = []

    # Header
    report.append("# Load Test Comparison Report")
    report.append("")
    report.append(f"**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report.append("")
    report.append("Comparison of Phase 1 Baseline vs Phase 2 Instrumented performance.")
    report.append("")

    # Summary
    report.append("## Summary")
    report.append("")
    report.append("| Metric | Phase 1 Baseline | Phase 2 Instrumented | Improvement | Status |")
    report.append("|--------|-----------------|---------------------|-------------|--------|")

    # Throughput (higher is better)
    throughput_imp = calculate_improvement(
        phase1_stats["requests_per_sec"],
        phase2_stats["requests_per_sec"],
        lower_is_better=False
    )
    report.append(f"| **Throughput (req/s)** | {phase1_stats['requests_per_sec']:.2f} | "
                 f"{phase2_stats['requests_per_sec']:.2f} | "
                 f"{throughput_imp['percent']:.1f}% | "
                 f"{throughput_imp['symbol']} {throughput_imp['interpretation']} |")

    # Average latency (lower is better)
    avg_latency_imp = calculate_improvement(
        phase1_stats["avg_response_time"],
        phase2_stats["avg_response_time"],
        lower_is_better=True
    )
    report.append(f"| **Avg Latency (ms)** | {phase1_stats['avg_response_time']:.0f} | "
                 f"{phase2_stats['avg_response_time']:.0f} | "
                 f"{avg_latency_imp['percent']:.1f}% | "
                 f"{avg_latency_imp['symbol']} {avg_latency_imp['interpretation']} |")

    # p95 latency
    p95_imp = calculate_improvement(
        phase1_stats["p95"],
        phase2_stats["p95"],
        lower_is_better=True
    )
    report.append(f"| **p95 Latency (ms)** | {phase1_stats['p95']:.0f} | "
                 f"{phase2_stats['p95']:.0f} | "
                 f"{p95_imp['percent']:.1f}% | "
                 f"{p95_imp['symbol']} {p95_imp['interpretation']} |")

    # p99 latency
    p99_imp = calculate_improvement(
        phase1_stats["p99"],
        phase2_stats["p99"],
        lower_is_better=True
    )
    report.append(f"| **p99 Latency (ms)** | {phase1_stats['p99']:.0f} | "
                 f"{phase2_stats['p99']:.0f} | "
                 f"{p99_imp['percent']:.1f}% | "
                 f"{p99_imp['symbol']} {p99_imp['interpretation']} |")

    # Error rate (lower is better)
    error_rate_imp = calculate_improvement(
        phase1_stats["failure_rate"],
        phase2_stats["failure_rate"],
        lower_is_better=True
    )
    report.append(f"| **Error Rate (%)** | {phase1_stats['failure_rate']:.2f} | "
                 f"{phase2_stats['failure_rate']:.2f} | "
                 f"{error_rate_imp['percent']:.1f}% | "
                 f"{error_rate_imp['symbol']} {error_rate_imp['interpretation']} |")

    report.append("")

    # Detailed stats
    report.append("## Detailed Statistics")
    report.append("")

    report.append("### Phase 1 Baseline")
    report.append("")
    report.append(f"- Total Requests: **{phase1_stats['total_requests']:,}**")
    report.append(f"- Total Failures: **{phase1_stats['total_failures']:,}**")
    report.append(f"- Failure Rate: **{phase1_stats['failure_rate']:.2f}%**")
    report.append(f"- Requests/sec: **{phase1_stats['requests_per_sec']:.2f}**")
    report.append("")
    report.append("**Latency:**")
    report.append(f"- Average: {phase1_stats['avg_response_time']:.0f} ms")
    report.append(f"- p50: {phase1_stats['p50']:.0f} ms")
    report.append(f"- p95: {phase1_stats['p95']:.0f} ms")
    report.append(f"- p99: {phase1_stats['p99']:.0f} ms")
    report.append(f"- Min: {phase1_stats['min_response_time']:.0f} ms")
    report.append(f"- Max: {phase1_stats['max_response_time']:.0f} ms")
    report.append("")

    report.append("### Phase 2 Instrumented")
    report.append("")
    report.append(f"- Total Requests: **{phase2_stats['total_requests']:,}**")
    report.append(f"- Total Failures: **{phase2_stats['total_failures']:,}**")
    report.append(f"- Failure Rate: **{phase2_stats['failure_rate']:.2f}%**")
    report.append(f"- Requests/sec: **{phase2_stats['requests_per_sec']:.2f}**")
    report.append("")
    report.append("**Latency:**")
    report.append(f"- Average: {phase2_stats['avg_response_time']:.0f} ms")
    report.append(f"- p50: {phase2_stats['p50']:.0f} ms")
    report.append(f"- p95: {phase2_stats['p95']:.0f} ms")
    report.append(f"- p99: {phase2_stats['p99']:.0f} ms")
    report.append(f"- Min: {phase2_stats['min_response_time']:.0f} ms")
    report.append(f"- Max: {phase2_stats['max_response_time']:.0f} ms")
    report.append("")

    # Performance targets
    report.append("## Performance Targets")
    report.append("")
    report.append("Target metrics for Phase 2:")
    report.append("")
    report.append("| Metric | Target | Phase 2 Result | Status |")
    report.append("|--------|--------|---------------|--------|")

    targets = {
        "p95 Latency": (200, phase2_stats["p95"], "ms", True),
        "p99 Latency": (500, phase2_stats["p99"], "ms", True),
        "Error Rate": (0.1, phase2_stats["failure_rate"], "%", True),
        "Throughput": (100, phase2_stats["requests_per_sec"], "req/s", False)
    }

    for metric_name, (target, actual, unit, lower_is_better) in targets.items():
        if lower_is_better:
            met = actual <= target
        else:
            met = actual >= target

        status = "✓ Met" if met else "✗ Not Met"
        report.append(f"| **{metric_name}** | < {target} {unit} | "
                     f"{actual:.2f} {unit} | {status} |")

    report.append("")

    # Endpoint breakdown
    report.append("## Endpoint Performance")
    report.append("")
    report.append("### Phase 1 Baseline Endpoints")
    report.append("")
    report.append("| Endpoint | Method | Requests | Failures | Avg Time (ms) | RPS |")
    report.append("|----------|--------|----------|----------|---------------|-----|")
    for ep in phase1_stats["endpoints"]:
        report.append(f"| {ep['name']} | {ep['method']} | {ep['requests']:,} | "
                     f"{ep['failures']} | {ep['avg_time']:.0f} | {ep['rps']:.2f} |")
    report.append("")

    report.append("### Phase 2 Instrumented Endpoints")
    report.append("")
    report.append("| Endpoint | Method | Requests | Failures | Avg Time (ms) | RPS |")
    report.append("|----------|--------|----------|----------|---------------|-----|")
    for ep in phase2_stats["endpoints"]:
        report.append(f"| {ep['name']} | {ep['method']} | {ep['requests']:,} | "
                     f"{ep['failures']} | {ep['avg_time']:.0f} | {ep['rps']:.2f} |")
    report.append("")

    # Key findings
    report.append("## Key Findings")
    report.append("")

    # Throughput
    if throughput_imp["interpretation"] == "Better":
        report.append(f"✓ **Throughput improved by {throughput_imp['percent']:.1f}%** "
                     f"({phase1_stats['requests_per_sec']:.2f} → "
                     f"{phase2_stats['requests_per_sec']:.2f} req/s)")
    elif throughput_imp["interpretation"] == "Worse":
        report.append(f"✗ **Throughput decreased by {throughput_imp['percent']:.1f}%** "
                     f"({phase1_stats['requests_per_sec']:.2f} → "
                     f"{phase2_stats['requests_per_sec']:.2f} req/s)")

    # Latency
    if p95_imp["interpretation"] == "Better":
        report.append(f"✓ **p95 latency reduced by {p95_imp['percent']:.1f}%** "
                     f"({phase1_stats['p95']:.0f} → {phase2_stats['p95']:.0f} ms)")
    elif p95_imp["interpretation"] == "Worse":
        report.append(f"✗ **p95 latency increased by {p95_imp['percent']:.1f}%** "
                     f"({phase1_stats['p95']:.0f} → {phase2_stats['p95']:.0f} ms)")

    # Error rate
    if error_rate_imp["interpretation"] == "Better":
        report.append(f"✓ **Error rate reduced by {error_rate_imp['percent']:.1f}%** "
                     f"({phase1_stats['failure_rate']:.2f}% → "
                     f"{phase2_stats['failure_rate']:.2f}%)")
    elif error_rate_imp["interpretation"] == "Worse":
        report.append(f"✗ **Error rate increased by {error_rate_imp['percent']:.1f}%** "
                     f"({phase1_stats['failure_rate']:.2f}% → "
                     f"{phase2_stats['failure_rate']:.2f}%)")

    report.append("")

    # Recommendations
    report.append("## Recommendations")
    report.append("")

    if phase2_stats["p95"] <= 200:
        report.append("✓ p95 latency target met (< 200ms)")
    else:
        report.append("⚠ p95 latency target not met. Consider:")
        report.append("  - Increasing cache TTLs")
        report.append("  - Optimizing database queries")
        report.append("  - Increasing connection pool size")

    if phase2_stats["failure_rate"] <= 0.1:
        report.append("✓ Error rate target met (< 0.1%)")
    else:
        report.append("⚠ Error rate target not met. Investigate:")
        report.append("  - Application errors in logs")
        report.append("  - Database connection issues")
        report.append("  - Rate limiting thresholds")

    if phase2_stats["requests_per_sec"] >= 100:
        report.append("✓ Throughput target met (> 100 req/s)")
    else:
        report.append("⚠ Throughput target not met. Consider:")
        report.append("  - Horizontal scaling (more instances)")
        report.append("  - Increasing worker processes")
        report.append("  - Optimizing slow endpoints")

    report.append("")

    # Write report
    with open(output_file, 'w') as f:
        f.write('\n'.join(report))

    print(f"✓ Comparison report generated: {output_file}")


def main():
    if len(sys.argv) != 4:
        print("Usage: python compare_load_test_results.py <phase1_csv> <phase2_csv> <output_md>")
        sys.exit(1)

    phase1_csv = sys.argv[1]
    phase2_csv = sys.argv[2]
    output_md = sys.argv[3]

    print(f"Parsing Phase 1 stats: {phase1_csv}")
    phase1_stats = parse_locust_stats(phase1_csv)

    print(f"Parsing Phase 2 stats: {phase2_csv}")
    phase2_stats = parse_locust_stats(phase2_csv)

    print(f"Generating comparison report: {output_md}")
    generate_comparison_report(phase1_stats, phase2_stats, output_md)


if __name__ == "__main__":
    main()
