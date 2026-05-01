"""
Workload generator for creating realistic trading job streams.
"""

import random
import time
from typing import List
from core.job import TradingJob, JobType, Priority
from workload.market_data import MarketDataFetcher


class WorkloadGenerator:
    """
    Generates realistic trading workloads based on market data and patterns.
    """
    
    def __init__(self, market_data_fetcher=None, time_scale=1.0):
        """
        Initialize workload generator.
        
        Args:
            market_data_fetcher: MarketDataFetcher instance (creates one if None)
            time_scale: Multiplier for job durations (e.g. 0.001 makes 1 hour -> 3.6s)
        """
        self.market_data = market_data_fetcher or MarketDataFetcher()
        self.job_counter = 0
        self.time_scale = time_scale
    
    def generate_job(self, job_type=None, symbol='SPY'):
        """
        Generate a single trading job with realistic parameters.
        
        Args:
            job_type: Specific JobType or None for random
            symbol: Stock symbol for market data
            
        Returns:
            TradingJob: Generated job
        """
        self.job_counter += 1
        
        if job_type is None:
            job_type = random.choice(list(JobType))
        
        # Get market characteristics
        volatility = self.market_data.calculate_volatility(symbol)
        
        # Generate job based on type
        if job_type == JobType.TICK_AGGREGATION:
            tick_count = self.market_data.get_tick_count(symbol)
            duration = 60 + (tick_count / 10000) * 240  # 1-5 minutes
            priority = Priority.HIGH if volatility > 0.02 else Priority.MEDIUM
            deadline = time.time() + random.uniform(300, 600)  # 5-10 min deadline
            
        elif job_type == JobType.FACTOR_CALCULATION:
            duration = random.uniform(600, 1800)  # 10-30 minutes
            priority = Priority.MEDIUM
            deadline = time.time() + 3600 if random.random() < 0.3 else None
            
        elif job_type == JobType.BACKTESTING:
            duration = random.uniform(3600, 21600)  # 1-6 hours
            priority = Priority.LOW if random.random() < 0.7 else Priority.MEDIUM
            deadline = None  # Rarely have deadlines
            
        elif job_type == JobType.RISK_ANALYTICS:
            duration = random.uniform(7200, 14400)  # 2-4 hours
            priority = Priority.HIGH
            # End of day deadline (simulated as 4 hours from now)
            deadline = time.time() + 14400
            
        else:  # SIGNAL_GENERATION
            duration = random.uniform(0.01, 0.1)  # 10-100 milliseconds
            priority = Priority.CRITICAL
            deadline = time.time() + 1  # 1 second deadline
        
        scaled_duration = duration * self.time_scale
        if deadline is not None:
            time_to_deadline = deadline - time.time()
            scaled_deadline = time.time() + (time_to_deadline * self.time_scale)
        else:
            scaled_deadline = None

        job = TradingJob(
            job_id=f"job_{self.job_counter}_{job_type.value}",
            job_type=job_type,
            duration=scaled_duration,
            priority=priority,
            deadline=scaled_deadline,
            data={
                'symbol': symbol,
                'volatility': volatility,
                'original_duration': duration,
            }
        )
        
        return job
    
    def generate_workload(self, num_jobs, scenario='normal', symbols=None):
        """
        Generate a workload with specific mix of job types.
        
        Args:
            num_jobs: Number of jobs to generate
            scenario: Workload scenario ('normal', 'volatile', 'batch', 'mixed')
            symbols: List of symbols to use (default: ['SPY'])
            
        Returns:
            list: List of TradingJob instances
        """
        if symbols is None:
            symbols = ['SPY']
        
        jobs = []
        
        # Define job type distributions for each scenario
        scenarios = {
            'normal': {
                JobType.TICK_AGGREGATION: 0.60,
                JobType.FACTOR_CALCULATION: 0.20,
                JobType.BACKTESTING: 0.15,
                JobType.RISK_ANALYTICS: 0.05
            },
            'volatile': {
                JobType.TICK_AGGREGATION: 0.80,
                JobType.SIGNAL_GENERATION: 0.10,
                JobType.RISK_ANALYTICS: 0.10
            },
            'batch': {
                JobType.BACKTESTING: 0.70,
                JobType.RISK_ANALYTICS: 0.30
            },
            'mixed': {
                JobType.TICK_AGGREGATION: 0.25,
                JobType.FACTOR_CALCULATION: 0.25,
                JobType.BACKTESTING: 0.25,
                JobType.RISK_ANALYTICS: 0.25
            }
        }
        
        distribution = scenarios.get(scenario, scenarios['normal'])
        
        for i in range(num_jobs):
            # Select job type based on distribution
            rand = random.random()
            cumulative = 0
            selected_type = JobType.TICK_AGGREGATION
            
            for job_type, prob in distribution.items():
                cumulative += prob
                if rand < cumulative:
                    selected_type = job_type
                    break
            
            # Random symbol
            symbol = random.choice(symbols)
            
            # Generate job
            job = self.generate_job(job_type=selected_type, symbol=symbol)
            jobs.append(job)
        
        return jobs
