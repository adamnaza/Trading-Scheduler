"""
FIFO (First-In-First-Out) Scheduler.
Non-preemptive, processes jobs in arrival order.
"""

from collections import deque
from typing import Optional
from core.job import TradingJob
from schedulers.base_scheduler import BaseScheduler


class FIFOScheduler(BaseScheduler):
    """
    First-Come-First-Served scheduling.
    Simple, fair, but can have poor performance with mixed workloads.
    """
    
    def __init__(self, num_workers=4):
        super().__init__(num_workers)
        self.ready_queue = deque()  # FIFO queue
    
    def submit_job(self, job: TradingJob):
        """
        Add job to end of FIFO queue.
        
        Args:
            job: TradingJob to schedule
        """
        self.ready_queue.append(job)
        self.all_jobs[job.job_id] = job
    
    def get_next_job(self) -> Optional[TradingJob]:
        """
        Get next job from front of queue.
        
        Returns:
            Next job or None if queue is empty
        """
        if self.ready_queue:
            return self.ready_queue.popleft()
        return None
