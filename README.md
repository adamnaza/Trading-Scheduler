# Task Scheduling for Quantitative Trading Systems

An operating systems project implementing and comparing multiple task scheduling algorithms in the context of algorithmic trading infrastructure.

## Project Overview

This project simulates a trading firm's compute cluster that processes diverse workloads:
- **Tick data aggregation** (1-5 min, high priority, deadline-sensitive)
- **Factor calculations** (10-30 min, medium priority)
- **Backtesting jobs** (1-6 hours, low priority)
- **Risk analytics** (2-4 hours, high priority, regulatory deadlines)

## Scheduling Algorithms Implemented

All four schedulers are non-preemptive.

1. **FIFO (First-In-First-Out)** - Baseline arrival-order scheduler
2. **SJF (Shortest Job First)** - Min-heap on duration; minimizes mean wait
3. **Priority-Based** - Max-heap on priority class (LOW/MEDIUM/HIGH/CRITICAL)
4. **Hybrid Deadline-Aware** - Two-heap policy: dispatches the earliest-deadline job when its slack is below an urgency threshold (default 300 s), otherwise falls back to priority

## Setup

### 1. Create Virtual Environment
```bash
python3 -m venv venv
source venv/bin/activate  # On macOS/Linux
# or
venv\Scripts\activate     # On Windows
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. (Optional) Alpha Vantage API key
The `MarketDataFetcher` can call Alpha Vantage but transparently falls
back to a local mock-data path when no key is set. **No reported
result in the report or in `results/` requires an API key.** If you
want to exercise the live path anyway, create a `.env` file:
```
ALPHA_VANTAGE_API_KEY=your_key_here
```
Get a free key at https://www.alphavantage.co/support/#api-key

## Usage

### Smoke test (recommended first run)
```bash
python example.py
```
Runs FIFO and Hybrid on a 20-job Normal workload with 2 workers and
prints summary statistics. Finishes in a few seconds.

### Run a single scheduler on real threads
```bash
python src/main.py --scheduler fifo --jobs 100 --scenario normal
```

### Run all schedulers on real threads
```bash
python src/main.py --compare --jobs 200 --scenario normal
```

### Reproduce the deterministic numbers and figures used in the report
Open and run every cell of `analysis.ipynb`. It uses a discrete-event
simulator with `random.Random(42)` and writes
`results/summary_all_scenarios.csv`,
`results/scalability_results.csv`, and `results/fig*.png`.

### CLI flags (`src/main.py`)
| Flag | Values | Default | Purpose |
|------|--------|---------|---------|
| `--scheduler` | `fifo`, `sjf`, `priority`, `hybrid` | -- | Run one policy |
| `--compare` | (flag) | off | Run all four policies |
| `--jobs` | int | 100 | Workload size |
| `--scenario` | `normal`, `volatile`, `batch`, `mixed` | `normal` | Job-type mix |
| `--time-scale` | float | 0.001 | Multiplies durations (0.001 -> 1 hr becomes 3.6 s) so wall-clock runs finish quickly |

## Project Structure

```
trading-scheduler/
├── src/
│   ├── core/
│   │   ├── job.py              # Job class definition
│   │   ├── worker.py           # Worker pool implementation
│   │   └── metrics.py          # Metrics collection and analysis
│   ├── schedulers/
│   │   ├── base_scheduler.py   # Abstract base class
│   │   ├── fifo.py            # FIFO scheduler
│   │   ├── priority.py        # Priority-based scheduler
│   │   ├── sjf.py             # Shortest Job First
│   │   └── hybrid.py          # Hybrid deadline-aware
│   ├── workload/
│   │   ├── generator.py       # Workload generation
│   │   └── market_data.py     # Market data fetching
│   └── main.py                # Main entry point
├── tests/                     # Unit tests
├── data/                      # Cached market data
├── results/                   # Experiment results and plots
└── requirements.txt
```

## Evaluation Metrics

- **Latency**: Average, P50, P95, P99 wait times
- **Deadline Compliance**: Miss rate, tardiness
- **Throughput**: Jobs completed per hour
- **Fairness**: Coefficient of variation in wait times
- **Resource Utilization**: CPU usage, idle time

## Example Results (Normal scenario, 200 jobs, 8 workers, seed 42)

Reproduced from `results/summary_all_scenarios.csv`.

| Scheduler | Avg Wait (s) | P99 Wait (s) | Miss % | CV |
|-----------|-------------:|-------------:|-------:|----:|
| FIFO      | 26402        | 59019        | 83.2   | 0.79 |
| SJF       |  6147        | 44981        | 39.6   | 1.63 |
| Priority  |  9872        | 49101        | 67.1   | 1.19 |
| Hybrid    |  7760        | 49032        | 47.7   | 1.52 |

See `Docs/COMP512_final_report.pdf` for full cross-scenario and
scalability tables, figures, and discussion.

## Author

Adam Che Nazahatuhisamudin  
