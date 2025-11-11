# Load Testing Guide

## Overview
This load testing script simulates multiple concurrent users accessing the Digital Signage API to measure performance under load.

## Prerequisites
```bash
pip install aiohttp
```

## Usage

### Basic Test (10 users, 60 seconds)
```bash
python tests/load_test.py
```

### Custom Parameters
```bash
# 50 concurrent users for 5 minutes
python tests/load_test.py --users 50 --duration 300

# Test against different server
python tests/load_test.py --base-url http://localhost:8001 --users 20
```

### Parameters
- `--users, -u`: Number of concurrent virtual users (default: 10)
- `--duration, -d`: Test duration in seconds (default: 60)
- `--base-url, -b`: Base URL of the API (default: http://192.168.5.12:8001)

## Test Scenarios
The script simulates realistic user behavior:

1. **Login** - Authenticate and get JWT token
2. **List Devices** - Get device list (cached)
3. **List Content** - Get content list (cached)
4. **List Playlists** - Get playlist list  
5. **Health Check** - Monitor system health

## Output

### Console Output
- Real-time progress updates
- Summary statistics per endpoint
- Overall performance metrics

### JSON Report
Detailed results saved to `load_test_results_YYYYMMDD_HHMMSS.json` containing:
- Configuration details
- Per-endpoint statistics
- Response time percentiles
- Success/failure rates
- Raw request data

## Performance Targets

| Metric | Target | Acceptable |
|--------|--------|------------|
| Success Rate | 99%+ | 95%+ |
| Average Response Time | < 100ms | < 200ms |
| 95th Percentile | < 200ms | < 500ms |
| Requests per Second | 100+ | 50+ |

## Example Results
```
OVERALL STATISTICS
==============================================================
Total Success Rate: 99.8%
Requests per Second: 125.3
Average Response Time: 85ms
Median Response Time: 72ms
95th Percentile: 178ms
```

## Tips
1. Run from a machine with good network connectivity to the server
2. Start with small user counts and gradually increase
3. Monitor server resources during the test (CPU, memory, database connections)
4. Run multiple tests to account for variability
5. Test during both low and high traffic periods