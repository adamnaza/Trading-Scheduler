"""
Main entry point for the trading scheduler simulator.
Run experiments comparing different scheduling algorithms.
"""

import argparse
import logging
import sys
import os

# Add src to path
sys.path.insert(0, os.path.dirname(__file__))

from schedulers import FIFOScheduler, PriorityScheduler, SJFScheduler, HybridScheduler
from workload import WorkloadGenerator
from core import JobType
import matplotlib.pyplot as plt
import pandas as pd

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def run_scheduler(scheduler_class, jobs, name):
    """
    Run a single scheduler with given jobs.
    
    Args:
        scheduler_class: Scheduler class to instantiate
        jobs: List of jobs to process
        name: Scheduler name for logging
        
    Returns:
        dict: Performance statistics
    """
    logger.info(f"\n{'='*60}")
    logger.info(f"Running {name}")
    logger.info(f"{'='*60}")
    
    scheduler = scheduler_class(num_workers=4)
    scheduler.start()
    
    # Submit all jobs
    for job in jobs:
        scheduler.submit_job(job)
    
    logger.info(f"Submitted {len(jobs)} jobs to {name}")
    
    # Run until complete
    scheduler.run_until_complete(timeout=300)  # 5 minute timeout
    
    # Get results
    stats = scheduler.get_statistics()
    scheduler.print_summary()
    
    # Save results
    os.makedirs('results', exist_ok=True)
    scheduler.save_results(f'results/{name.lower().replace(" ", "_")}_results.csv')
    
    scheduler.stop()
    
    return stats


def compare_schedulers(num_jobs=100, scenario='normal', time_scale=0.001):
    """
    Compare all scheduling algorithms on the same workload.
    
    Args:
        num_jobs: Number of jobs to generate
        scenario: Workload scenario
        time_scale: Duration scaling factor
    """
    logger.info(f"Generating workload: {num_jobs} jobs, scenario='{scenario}', time_scale={time_scale}")
    
    # Generate workload
    generator = WorkloadGenerator(time_scale=time_scale)
    jobs = generator.generate_workload(num_jobs, scenario=scenario)
    
    logger.info(f"Generated {len(jobs)} jobs")
    
    # Run each scheduler
    schedulers = [
        (FIFOScheduler, "FIFO Scheduler"),
        (SJFScheduler, "Shortest Job First"),
        (PriorityScheduler, "Priority-Based"),
        (HybridScheduler, "Hybrid Deadline-Aware")
    ]
    
    results = {}
    
    for scheduler_class, name in schedulers:
        # Create fresh copy of jobs for each scheduler with reset timing
        import time as _time
        job_copies = []
        for job in jobs:
            from core.job import TradingJob
            if job.deadline is not None:
                deadline_offset = job.deadline - job.arrival_time
                new_deadline = _time.time() + deadline_offset
            else:
                new_deadline = None
            job_copy = TradingJob(
                job_id=job.job_id,
                job_type=job.job_type,
                duration=job.duration,
                priority=job.priority,
                deadline=new_deadline,
                data=job.data
            )
            job_copies.append(job_copy)
        
        stats = run_scheduler(scheduler_class, job_copies, name)
        results[name] = stats
    
    # Create comparison table
    print_comparison_table(results)
    plot_comparison(results)


def print_comparison_table(results):
    """Print comparison table of all schedulers"""
    print("\n" + "="*80)
    print("SCHEDULER COMPARISON")
    print("="*80)
    
    metrics = [
        ('avg_wait_time', 'Avg Wait Time (s)'),
        ('p99_wait_time', 'P99 Wait Time (s)'),
        ('deadline_miss_rate', 'Deadline Miss Rate (%)'),
        ('throughput_jobs_per_hour', 'Throughput (jobs/hr)'),
        ('wait_time_cv', 'Fairness (CV)')
    ]
    
    print(f"\n{'Scheduler':<25}", end='')
    for _, label in metrics:
        print(f"{label:>20}", end='')
    print()
    print("-" * 125)
    
    for scheduler_name, stats in results.items():
        print(f"{scheduler_name:<25}", end='')
        for metric, _ in metrics:
            value = stats.get(metric, 0)
            print(f"{value:>20.2f}", end='')
        print()
    
    print("="*80 + "\n")


def plot_comparison(results):
    """Generate comparison plots"""
    import matplotlib.pyplot as plt
    
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    fig.suptitle('Scheduler Performance Comparison', fontsize=16, fontweight='bold')
    
    schedulers = list(results.keys())
    
    # Plot 1: Average Wait Time
    wait_times = [results[s].get('avg_wait_time', 0) for s in schedulers]
    axes[0, 0].bar(range(len(schedulers)), wait_times, color=['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728'])
    axes[0, 0].set_xticks(range(len(schedulers)))
    axes[0, 0].set_xticklabels(schedulers, rotation=15, ha='right')
    axes[0, 0].set_ylabel('Seconds')
    axes[0, 0].set_title('Average Wait Time')
    axes[0, 0].grid(axis='y', alpha=0.3)
    
    # Plot 2: Deadline Miss Rate
    miss_rates = [results[s].get('deadline_miss_rate', 0) for s in schedulers]
    axes[0, 1].bar(range(len(schedulers)), miss_rates, color=['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728'])
    axes[0, 1].set_xticks(range(len(schedulers)))
    axes[0, 1].set_xticklabels(schedulers, rotation=15, ha='right')
    axes[0, 1].set_ylabel('Percentage (%)')
    axes[0, 1].set_title('Deadline Miss Rate')
    axes[0, 1].grid(axis='y', alpha=0.3)
    
    # Plot 3: Throughput
    throughput = [results[s].get('throughput_jobs_per_hour', 0) for s in schedulers]
    axes[1, 0].bar(range(len(schedulers)), throughput, color=['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728'])
    axes[1, 0].set_xticks(range(len(schedulers)))
    axes[1, 0].set_xticklabels(schedulers, rotation=15, ha='right')
    axes[1, 0].set_ylabel('Jobs/Hour')
    axes[1, 0].set_title('Throughput')
    axes[1, 0].grid(axis='y', alpha=0.3)
    
    # Plot 4: Fairness (CV)
    fairness = [results[s].get('wait_time_cv', 0) for s in schedulers]
    axes[1, 1].bar(range(len(schedulers)), fairness, color=['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728'])
    axes[1, 1].set_xticks(range(len(schedulers)))
    axes[1, 1].set_xticklabels(schedulers, rotation=15, ha='right')
    axes[1, 1].set_ylabel('Coefficient of Variation')
    axes[1, 1].set_title('Fairness (lower is better)')
    axes[1, 1].grid(axis='y', alpha=0.3)
    
    plt.tight_layout()
    plt.savefig('results/scheduler_comparison.png', dpi=300, bbox_inches='tight')
    print(f"\nSaved comparison plot to results/scheduler_comparison.png")
    plt.close()


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='Trading Task Scheduler Simulator')
    
    parser.add_argument(
        '--scheduler',
        choices=['fifo', 'sjf', 'priority', 'hybrid'],
        help='Run a specific scheduler'
    )
    
    parser.add_argument(
        '--compare',
        action='store_true',
        help='Compare all schedulers'
    )
    
    parser.add_argument(
        '--jobs',
        type=int,
        default=100,
        help='Number of jobs to generate (default: 100)'
    )
    
    parser.add_argument(
        '--scenario',
        choices=['normal', 'volatile', 'batch', 'mixed'],
        default='normal',
        help='Workload scenario (default: normal)'
    )
    
    parser.add_argument(
        '--time-scale',
        type=float,
        default=0.001,
        help='Time scaling factor (default: 0.001, i.e. 1 hour -> 3.6s)'
    )
    
    args = parser.parse_args()
    
    if args.compare:
        compare_schedulers(num_jobs=args.jobs, scenario=args.scenario, time_scale=args.time_scale)
    elif args.scheduler:
        # Run single scheduler
        generator = WorkloadGenerator(time_scale=args.time_scale)
        jobs = generator.generate_workload(args.jobs, scenario=args.scenario)
        
        scheduler_map = {
            'fifo': (FIFOScheduler, "FIFO Scheduler"),
            'sjf': (SJFScheduler, "Shortest Job First"),
            'priority': (PriorityScheduler, "Priority-Based"),
            'hybrid': (HybridScheduler, "Hybrid Deadline-Aware")
        }
        
        scheduler_class, name = scheduler_map[args.scheduler]
        run_scheduler(scheduler_class, jobs, name)
    else:
        parser.print_help()
        print("\nExample usage:")
        print("  python src/main.py --compare --jobs 200 --scenario normal")
        print("  python src/main.py --scheduler hybrid --jobs 100")


if __name__ == '__main__':
    main()
