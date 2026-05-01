"""
Hybrid Deadline-Aware Scheduler.
Combines Earliest Deadline First (EDF) for deadline jobs with priority scheduling.
"""

import heapq
import time
from typing import Optional
from core.job import TradingJob
from schedulers.base_scheduler import BaseScheduler


class HybridScheduler(BaseScheduler):
    """
    Hybrid deadline-aware scheduler.
    Uses EDF for jobs with deadlines, priority for others.
    Prioritizes urgent deadlines over normal priority.
    """
    
    def __init__(self, num_workers=4, urgency_threshold=300):
        """
        Initialize hybrid scheduler.
        
        Args:
            num_workers: Number of parallel workers
            urgency_threshold: Seconds before deadline to treat as urgent (default 5 min)
        """
        super().__init__(num_workers)
        self.deadline_queue = []  # min-heap by deadline
        self.priority_queue = []  # max-heap by priority
        self.urgency_threshold = urgency_threshold
        self.counter = 0
    
    def submit_job(self, job: TradingJob):
        """
        Add job to appropriate queue based on whether it has a deadline.
        
        Args:
            job: TradingJob to schedule
        """
        if job.deadline is not None:
            # Add to deadline queue (EDF)
            heapq.heappush(
                self.deadline_queue,
                (job.deadline, self.counter, job)
            )
        else:
            # Add to priority queue
            heapq.heappush(
                self.priority_queue,
                (-job.priority.value, self.counter, job)
            )
        
        self.counter += 1
        self.all_jobs[job.job_id] = job
    
    def get_next_job(self) -> Optional[TradingJob]:
        """
        Get next job using hybrid policy:
        1. If deadline job is urgent (within threshold), run it
        2. Otherwise, run highest priority job
        3. If no priority jobs, run earliest deadline job
        
        Returns:
            Next job or None if queues are empty
        """
        current_time = time.time()
        
        # Check if any deadline job is urgent
        if self.deadline_queue:
            deadline, _, job = self.deadline_queue[0]
            time_to_deadline = deadline - current_time
            
            # If deadline is imminent, prioritize it
            if time_to_deadline < self.urgency_threshold:
                heapq.heappop(self.deadline_queue)
                return job
        
        # Otherwise, prefer priority jobs
        if self.priority_queue:
            _, _, job = heapq.heappop(self.priority_queue)
            return job
        
        # Fall back to deadline jobs (even if not urgent)
        if self.deadline_queue:
            _, _, job = heapq.heappop(self.deadline_queue)
            return job
        
        return None
    
    def _has_pending(self):
        """Check both queues for pending jobs."""
        return bool(self.deadline_queue) or bool(self.priority_queue)

    def get_deadline_status(self):
        """
        Get status of deadline jobs.
        
        Returns:
            dict: Statistics about deadline jobs
        """
        if not self.deadline_queue:
            return {
                'pending_deadline_jobs': 0,
                'urgent_jobs': 0,
                'earliest_deadline': None
            }
        
        current_time = time.time()
        urgent_count = 0
        
        for deadline, _, job in self.deadline_queue:
            if deadline - current_time < self.urgency_threshold:
                urgent_count += 1
        
        return {
            'pending_deadline_jobs': len(self.deadline_queue),
            'urgent_jobs': urgent_count,
            'earliest_deadline': self.deadline_queue[0][0] if self.deadline_queue else None
        }
