"""
Basic unit tests for the trading scheduler.
"""

import unittest
import time
from core.job import TradingJob, JobType, Priority
from schedulers import FIFOScheduler, PriorityScheduler, SJFScheduler
from workload import WorkloadGenerator


class TestJob(unittest.TestCase):
    """Test TradingJob class"""
    
    def test_job_creation(self):
        """Test basic job creation"""
        job = TradingJob(
            job_id="test_1",
            job_type=JobType.TICK_AGGREGATION,
            duration=60.0,
            priority=Priority.HIGH
        )
        
        self.assertEqual(job.job_id, "test_1")
        self.assertEqual(job.job_type, JobType.TICK_AGGREGATION)
        self.assertEqual(job.duration, 60.0)
        self.assertEqual(job.priority, Priority.HIGH)
    
    def test_job_timing(self):
        """Test job timing calculations"""
        job = TradingJob(
            job_id="test_2",
            job_type=JobType.FACTOR_CALCULATION,
            duration=10.0,
            priority=Priority.MEDIUM
        )
        
        # Simulate execution
        time.sleep(0.1)
        job.start_execution()
        self.assertIsNotNone(job.start_time)
        self.assertIsNotNone(job.wait_time)
        self.assertGreater(job.wait_time, 0)
        
        time.sleep(0.1)
        job.complete_execution()
        self.assertIsNotNone(job.completion_time)
        self.assertIsNotNone(job.turnaround_time)


class TestSchedulers(unittest.TestCase):
    """Test scheduler implementations"""
    
    def create_test_jobs(self, n=10):
        """Create n test jobs"""
        jobs = []
        for i in range(n):
            job = TradingJob(
                job_id=f"job_{i}",
                job_type=JobType.TICK_AGGREGATION,
                duration=0.1,  # Very short for testing
                priority=Priority(i % 4)
            )
            jobs.append(job)
        return jobs
    
    def test_fifo_scheduler(self):
        """Test FIFO scheduler"""
        scheduler = FIFOScheduler(num_workers=2)
        scheduler.start()
        
        jobs = self.create_test_jobs(5)
        for job in jobs:
            scheduler.submit_job(job)
        
        scheduler.run_until_complete(timeout=10)
        
        stats = scheduler.get_statistics()
        self.assertEqual(stats['total_jobs'], 5)
        
        scheduler.stop()
    
    def test_priority_scheduler(self):
        """Test priority scheduler"""
        scheduler = PriorityScheduler(num_workers=2)
        scheduler.start()
        
        jobs = self.create_test_jobs(5)
        for job in jobs:
            scheduler.submit_job(job)
        
        scheduler.run_until_complete(timeout=10)
        
        stats = scheduler.get_statistics()
        self.assertEqual(stats['total_jobs'], 5)
        
        scheduler.stop()
    
    def test_sjf_scheduler(self):
        """Test SJF scheduler"""
        scheduler = SJFScheduler(num_workers=2)
        scheduler.start()
        
        jobs = self.create_test_jobs(5)
        for job in jobs:
            scheduler.submit_job(job)
        
        scheduler.run_until_complete(timeout=10)
        
        stats = scheduler.get_statistics()
        self.assertEqual(stats['total_jobs'], 5)
        
        scheduler.stop()


class TestWorkloadGenerator(unittest.TestCase):
    """Test workload generation"""
    
    def test_generate_job(self):
        """Test single job generation"""
        generator = WorkloadGenerator()
        job = generator.generate_job(job_type=JobType.TICK_AGGREGATION)
        
        self.assertIsInstance(job, TradingJob)
        self.assertEqual(job.job_type, JobType.TICK_AGGREGATION)
    
    def test_generate_workload(self):
        """Test workload generation"""
        generator = WorkloadGenerator()
        jobs = generator.generate_workload(num_jobs=20, scenario='normal')
        
        self.assertEqual(len(jobs), 20)
        
        # Check job type distribution (approximate)
        tick_jobs = [j for j in jobs if j.job_type == JobType.TICK_AGGREGATION]
        self.assertGreater(len(tick_jobs), 5)  # Should be ~60% = 12


if __name__ == '__main__':
    unittest.main()
