"""
Priority-Based Preemptive Scheduler.
Jobs with higher priority execute first and can preempt lower priority jobs.
"""

import heapq
from typing import Optional
from core.job import TradingJob, Priority
from schedulers.base_scheduler import BaseScheduler


class PriorityScheduler(BaseScheduler):
    """
    Priority-based preemptive scheduling.
    Higher priority jobs run first. Same priority uses FIFO.
    """
    
    def __init__(self, num_workers=4):
        super().__init__(num_workers)
        self.ready_queue = []  # min-heap (negative priority for max-heap behavior)
        self.counter = 0  # tie-breaker for same priority
    
    def submit_job(self, job: TradingJob):
        """
        Add job to priority queue.
        
        Args:
            job: TradingJob to schedule
        """
        # Negative priority for max-heap (higher priority first)
        # Use counter for FIFO tie-breaking within same priority
        heapq.heappush(
            self.ready_queue,
            (-job.priority.value, self.counter, job)
        )
        self.counter += 1
        self.all_jobs[job.job_id] = job
    
    def get_next_job(self) -> Optional[TradingJob]:
        """
        Get highest priority job.
        
        Returns:
            Highest priority job or None if queue is empty
        """
        if self.ready_queue:
            _, _, job = heapq.heappop(self.ready_queue)
            return job
        return None
    
    def check_preemption(self):
        """
        Check if a higher priority job should preempt running jobs.
        Note: Full preemption logic would require pausing/resuming jobs.
        This is a simplified version for the simulation.
        """
        if not self.ready_queue or not self.running_jobs:
            return
        
        # Get highest priority waiting job
        next_priority = -self.ready_queue[0][0]
        
        # Get lowest priority running job
        running_priorities = [job.priority.value for job in self.running_jobs.values()]
        if running_priorities:
            min_running_priority = min(running_priorities)
            
            # If waiting job has higher priority, signal preemption
            if next_priority > min_running_priority:
                # In a full implementation, we would pause the lower priority job
                # For this simulation, we just track the preemption
                for job_id, job in self.running_jobs.items():
                    if job.priority.value == min_running_priority:
                        job.preemption_count += 1
                        break
