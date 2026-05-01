"""
Base scheduler abstract class.
All schedulers inherit from this class.
"""

from abc import ABC, abstractmethod
from typing import List, Optional
from core.job import TradingJob
from core.worker import WorkerPool
from core.metrics import MetricsCollector
import logging

logger = logging.getLogger(__name__)


class BaseScheduler(ABC):
    """
    Abstract base class for all scheduling algorithms.
    """
    
    def __init__(self, num_workers=4):
        """
        Initialize base scheduler.
        
        Args:
            num_workers: Number of parallel workers
        """
        self.worker_pool = WorkerPool(num_workers)
        self.metrics = MetricsCollector()
        self.ready_queue = []
        self.running_jobs = {}  # job_id -> TradingJob
        self.all_jobs = {}      # job_id -> TradingJob
        
    @abstractmethod
    def submit_job(self, job: TradingJob):
        """
        Submit a job to the scheduler.
        Must be implemented by subclasses.
        
        Args:
            job: TradingJob to schedule
        """
        pass
    
    @abstractmethod
    def get_next_job(self) -> Optional[TradingJob]:
        """
        Get the next job to execute based on scheduling policy.
        Must be implemented by subclasses.
        
        Returns:
            TradingJob or None if queue is empty
        """
        pass
    
    def start(self):
        """Start the scheduler"""
        self.worker_pool.start()
        logger.info(f"{self.__class__.__name__} started")
    
    def stop(self):
        """Stop the scheduler"""
        self.worker_pool.stop()
        logger.info(f"{self.__class__.__name__} stopped")
    
    def _has_pending(self):
        """Return True if there are jobs waiting to be scheduled."""
        return bool(self.ready_queue)

    def schedule_step(self):
        """
        Perform one scheduling step:
        1. Check for completed jobs
        2. Try to schedule new jobs if workers are available
        """
        # Check for completions
        completed_ids = self.worker_pool.check_completions()
        for job_id in completed_ids:
            if job_id in self.running_jobs:
                job = self.running_jobs.pop(job_id)
                job.complete_execution()
                self.metrics.record_completion(job)
        
        # Schedule new jobs while there's capacity
        while self.worker_pool.has_capacity() and self._has_pending():
            job = self.get_next_job()
            if job:
                if self.worker_pool.submit_job(job):
                    self.running_jobs[job.job_id] = job
                else:
                    self.ready_queue.insert(0, job)
                    break
            else:
                break
    
    def run_until_complete(self, timeout=None):
        """
        Run scheduler until all jobs complete or timeout.
        
        Args:
            timeout: Maximum time to wait (None for no limit)
        """
        import time
        start_time = time.time()
        
        while True:
            self.schedule_step()
            
            # Check if done
            if not self._has_pending() and not self.running_jobs:
                break
            
            # Check timeout
            if timeout and (time.time() - start_time) > timeout:
                logger.warning("Scheduler timeout reached")
                break
            
            # Small sleep to avoid busy waiting
            time.sleep(0.01)
        
        logger.info(f"Scheduling complete. Total jobs processed: {len(self.metrics.jobs_completed)}")
    
    def get_statistics(self):
        """Get performance statistics"""
        return self.metrics.get_statistics()
    
    def print_summary(self):
        """Print performance summary"""
        self.metrics.print_summary()
    
    def save_results(self, filename):
        """Save results to CSV"""
        self.metrics.save_to_csv(filename)
