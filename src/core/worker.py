"""
Worker pool for executing jobs in parallel.
Uses threads to simulate job execution (threads are sufficient since
workers just call time.sleep, which releases the GIL).
"""

import time
from queue import Queue, Empty
from threading import Thread
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def _execute_job(job_id, duration, result_queue):
    """Worker function that simulates job execution via sleep."""
    try:
        start_time = time.time()
        time.sleep(duration)
        end_time = time.time()
        result_queue.put({
            'job_id': job_id,
            'status': 'completed',
            'actual_duration': end_time - start_time,
            'start_time': start_time,
            'end_time': end_time,
        })
    except Exception as e:
        result_queue.put({
            'job_id': job_id,
            'status': 'failed',
            'error': str(e),
        })


class WorkerPool:
    """Manages a pool of worker threads for job execution."""

    def __init__(self, num_workers=4):
        self.num_workers = num_workers
        self.result_queue = Queue()
        self.active_jobs = {}   # job_id -> Thread
        self.completed_jobs = {}
        self.running = False
        logger.info(f"Initialized WorkerPool with {num_workers} workers")

    def start(self):
        self.running = True
        logger.info("WorkerPool started")

    def stop(self):
        self.running = False
        for job_id, thread in list(self.active_jobs.items()):
            thread.join(timeout=2)
        self.active_jobs.clear()
        logger.info("WorkerPool stopped")

    def submit_job(self, job):
        """Submit a job for execution. Returns True if accepted."""
        if len(self.active_jobs) >= self.num_workers:
            return False

        thread = Thread(
            target=_execute_job,
            args=(job.job_id, job.duration, self.result_queue),
            daemon=True,
        )
        thread.start()
        self.active_jobs[job.job_id] = thread

        job.start_execution()
        logger.debug(f"Submitted job {job.job_id} to worker pool")
        return True

    def check_completions(self):
        """Return list of job IDs that finished since last check."""
        completed = []
        while True:
            try:
                result = self.result_queue.get_nowait()
                job_id = result['job_id']
                if job_id in self.active_jobs:
                    self.active_jobs.pop(job_id)
                self.completed_jobs[job_id] = result
                completed.append(job_id)
                logger.debug(f"Job {job_id} completed with status: {result['status']}")
            except Empty:
                break
        return completed

    def get_num_active(self):
        return len(self.active_jobs)

    def has_capacity(self):
        return len(self.active_jobs) < self.num_workers

    def get_result(self, job_id):
        return self.completed_jobs.get(job_id)
