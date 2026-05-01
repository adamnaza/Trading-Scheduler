"""
Shortest Job First (SJF) Scheduler.
Non-preemptive scheduler that minimizes average wait time.
"""

import heapq
from typing import Optional
from core.job import TradingJob
from schedulers.base_scheduler import BaseScheduler


class SJFScheduler(BaseScheduler):
    """
    Shortest Job First scheduling.
    Always executes the job with shortest estimated duration.
    Minimizes average wait time but can starve long jobs.
    """
    
    def __init__(self, num_workers=4):
        super().__init__(num_workers)
        self.ready_queue = []  # min-heap by duration
        self.counter = 0  # tie-breaker for same duration
    
    def submit_job(self, job: TradingJob):
        """
        Add job to queue sorted by duration.
        
        Args:
            job: TradingJob to schedule
        """
        # Min-heap by duration (shortest first)
        # Use counter for FIFO tie-breaking within same duration
        heapq.heappush(
            self.ready_queue,
            (job.duration, self.counter, job)
        )
        self.counter += 1
        self.all_jobs[job.job_id] = job
    
    def get_next_job(self) -> Optional[TradingJob]:
        """
        Get job with shortest duration.
        
        Returns:
            Shortest job or None if queue is empty
        """
        if self.ready_queue:
            _, _, job = heapq.heappop(self.ready_queue)
            return job
        return None
