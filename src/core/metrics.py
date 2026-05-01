"""
Metrics collection and analysis for scheduler evaluation.
"""

import pandas as pd
import numpy as np
from typing import List, Dict
from core.job import TradingJob


class MetricsCollector:
    """
    Collects and analyzes performance metrics for scheduling algorithms.
    """
    
    def __init__(self):
        """Initialize metrics collector"""
        self.jobs_completed = []
        self.start_time = None
        self.end_time = None
    
    def record_completion(self, job: TradingJob):
        """
        Record completion of a job.
        
        Args:
            job: Completed TradingJob instance
        """
        original_duration = (job.data or {}).get('original_duration', job.duration)
        self.jobs_completed.append({
            'job_id': job.job_id,
            'job_type': job.job_type.value,
            'priority': job.priority.value,
            'duration': job.duration,
            'original_duration': original_duration,
            'arrival_time': job.arrival_time,
            'start_time': job.start_time,
            'completion_time': job.completion_time,
            'wait_time': job.wait_time,
            'turnaround_time': job.turnaround_time,
            'deadline': job.deadline,
            'missed_deadline': job.missed_deadline,
            'slack_time': job.slack_time if job.deadline else None,
            'preemption_count': job.preemption_count,
            'state': job.state.value
        })
    
    def get_dataframe(self) -> pd.DataFrame:
        """
        Get DataFrame of all completed jobs.
        
        Returns:
            pd.DataFrame: Job completion data
        """
        return pd.DataFrame(self.jobs_completed)
    
    def get_statistics(self) -> Dict:
        """
        Calculate comprehensive statistics.
        
        Returns:
            dict: Dictionary of performance metrics
        """
        if not self.jobs_completed:
            return {'error': 'No jobs recorded'}
        
        df = self.get_dataframe()
        
        # Filter for successful completions
        completed = df[df['state'] == 'completed']
        
        if len(completed) == 0:
            return {'error': 'No completed jobs'}
        
        stats = {
            # Latency metrics
            'avg_wait_time': completed['wait_time'].mean(),
            'median_wait_time': completed['wait_time'].median(),
            'p95_wait_time': completed['wait_time'].quantile(0.95),
            'p99_wait_time': completed['wait_time'].quantile(0.99),
            'max_wait_time': completed['wait_time'].max(),
            'std_wait_time': completed['wait_time'].std(),
            
            # Turnaround time
            'avg_turnaround_time': completed['turnaround_time'].mean(),
            'median_turnaround_time': completed['turnaround_time'].median(),
            
            # Deadline compliance
            'total_jobs': len(completed),
            'jobs_with_deadlines': completed['deadline'].notna().sum(),
            'deadline_miss_count': completed['missed_deadline'].sum(),
            'deadline_miss_rate': (completed['missed_deadline'].sum() / 
                                  max(completed['deadline'].notna().sum(), 1) * 100),
            
            # Tardiness (for missed deadlines)
            'avg_tardiness': abs(completed[completed['missed_deadline']]['slack_time'].mean()) 
                           if completed['missed_deadline'].any() else 0,
            
            # Throughput
            'total_duration': completed['completion_time'].max() - completed['arrival_time'].min(),
            'throughput_jobs_per_hour': (len(completed) / 
                                        (completed['completion_time'].max() - 
                                         completed['arrival_time'].min()) * 3600),
            
            # Fairness (coefficient of variation)
            'wait_time_cv': completed['wait_time'].std() / completed['wait_time'].mean(),
            
            # Preemption overhead
            'avg_preemptions': completed['preemption_count'].mean(),
            'total_preemptions': completed['preemption_count'].sum(),
        }
        
        # Per-priority statistics
        for priority in completed['priority'].unique():
            priority_jobs = completed[completed['priority'] == priority]
            stats[f'avg_wait_time_priority_{priority}'] = priority_jobs['wait_time'].mean()
        
        # Per-job-type statistics
        for job_type in completed['job_type'].unique():
            type_jobs = completed[completed['job_type'] == job_type]
            stats[f'avg_wait_time_type_{job_type}'] = type_jobs['wait_time'].mean()
        
        return stats
    
    def print_summary(self):
        """Print a summary of key metrics"""
        stats = self.get_statistics()
        
        if 'error' in stats:
            print(f"Error: {stats['error']}")
            return
        
        print("\n" + "="*60)
        print("SCHEDULER PERFORMANCE SUMMARY")
        print("="*60)
        
        print(f"\nLatency Metrics:")
        print(f"  Average Wait Time:     {stats['avg_wait_time']:.2f}s")
        print(f"  Median Wait Time:      {stats['median_wait_time']:.2f}s")
        print(f"  P95 Wait Time:         {stats['p95_wait_time']:.2f}s")
        print(f"  P99 Wait Time:         {stats['p99_wait_time']:.2f}s")
        print(f"  Max Wait Time:         {stats['max_wait_time']:.2f}s")
        
        print(f"\nDeadline Compliance:")
        print(f"  Jobs with Deadlines:   {stats['jobs_with_deadlines']}")
        print(f"  Deadline Misses:       {stats['deadline_miss_count']}")
        print(f"  Miss Rate:             {stats['deadline_miss_rate']:.2f}%")
        if stats['avg_tardiness'] > 0:
            print(f"  Avg Tardiness:         {stats['avg_tardiness']:.2f}s")
        
        print(f"\nThroughput:")
        print(f"  Total Jobs:            {stats['total_jobs']}")
        print(f"  Jobs/Hour:             {stats['throughput_jobs_per_hour']:.2f}")
        print(f"  Total Duration:        {stats['total_duration']:.2f}s")
        
        print(f"\nFairness:")
        print(f"  Wait Time CV:          {stats['wait_time_cv']:.3f}")
        print(f"  Total Preemptions:     {stats['total_preemptions']}")
        print(f"  Avg Preemptions/Job:   {stats['avg_preemptions']:.2f}")
        
        print("="*60 + "\n")
    
    def save_to_csv(self, filename: str):
        """
        Save detailed job data to CSV.
        
        Args:
            filename: Output CSV filename
        """
        df = self.get_dataframe()
        df.to_csv(filename, index=False)
        print(f"Saved detailed results to {filename}")
