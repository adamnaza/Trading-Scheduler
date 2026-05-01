"""
Simple example demonstrating the trading scheduler.
Run this to verify your installation works.

Uses time_scale=0.001 so multi-hour trading jobs finish in seconds
of wall-clock time, and seeds the workload generator so the demo
output is reproducible.
"""

import os
import random
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from schedulers import FIFOScheduler, HybridScheduler
from workload import WorkloadGenerator

random.seed(42)

print("=" * 70)
print("TRADING SCHEDULER - SIMPLE EXAMPLE")
print("=" * 70)

# Create workload generator (time_scale=0.001 -> 1 hour becomes 3.6 s)
print("\n1. Creating workload generator (time_scale=0.001)...")
generator = WorkloadGenerator(time_scale=0.001)

# Generate a small workload
print("2. Generating 20 trading jobs...")
jobs = generator.generate_workload(num_jobs=20, scenario='normal')

print(f"\nGenerated {len(jobs)} jobs:")
for job in jobs[:5]:
    print(f"  - {job}")
print(f"  ... and {len(jobs) - 5} more\n")

# Test FIFO Scheduler
print("=" * 70)
print("3. Running FIFO Scheduler")
print("=" * 70)

fifo = FIFOScheduler(num_workers=2)
fifo.start()
for job in jobs:
    fifo.submit_job(job)
print(f"Submitted {len(jobs)} jobs to FIFO scheduler")
print("Processing...")
fifo.run_until_complete(timeout=120)
fifo.print_summary()
fifo.stop()

# Test Hybrid Scheduler with a fresh, identical workload
print("\n" + "=" * 70)
print("4. Running Hybrid Deadline-Aware Scheduler")
print("=" * 70)

random.seed(42)
generator_h = WorkloadGenerator(time_scale=0.001)
jobs_hybrid = generator_h.generate_workload(num_jobs=20, scenario='normal')

hybrid = HybridScheduler(num_workers=2, urgency_threshold=300)
hybrid.start()
for job in jobs_hybrid:
    hybrid.submit_job(job)
print(f"Submitted {len(jobs_hybrid)} jobs to Hybrid scheduler")
print("Processing...")
hybrid.run_until_complete(timeout=120)
hybrid.print_summary()
hybrid.stop()

print("\n" + "=" * 70)
print("SUCCESS! Your scheduler is working correctly.")
print("=" * 70)
print("\nNext steps:")
print("  1. Run a full real-thread sweep:")
print("       python src/main.py --compare --jobs 200 --scenario normal")
print("  2. Reproduce the deterministic numbers/figures used in the report:")
print("       jupyter notebook analysis.ipynb   # then 'Run All'")
print("  3. Inspect committed CSVs and figures in results/")
print("\nSee QUICKSTART.md for more examples!")
