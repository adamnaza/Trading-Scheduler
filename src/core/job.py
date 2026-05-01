"""
Core Job class for trading scheduler.
Represents a computational task with priority, duration, and optional deadline.
"""

import time
from enum import Enum
from dataclasses import dataclass
from typing import Optional


class JobType(Enum):
    """Types of trading jobs"""
    TICK_AGGREGATION = "tick_agg"
    FACTOR_CALCULATION = "factor_calc"
    BACKTESTING = "backtest"
    RISK_ANALYTICS = "risk"
    SIGNAL_GENERATION = "signal"


class Priority(Enum):
    """Job priority levels"""
    LOW = 0
    MEDIUM = 1
    HIGH = 2
    CRITICAL = 3


class JobState(Enum):
    """Job execution states"""
    READY = "ready"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class TradingJob:
    """
    Represents a computational job in the trading system.
    
    Attributes:
        job_id: Unique identifier for the job
        job_type: Type of trading job (tick_agg, backtest, etc.)
        duration: Estimated execution time in seconds
        priority: Job priority level (0=LOW to 3=CRITICAL)
        deadline: Optional deadline as Unix timestamp
        data: Optional dict containing job-specific data (symbol, date, etc.)
    """
    
    job_id: str
    job_type: JobType
    duration: float  # seconds
    priority: Priority
    deadline: Optional[float] = None  # Unix timestamp
    data: Optional[dict] = None
    
    def __post_init__(self):
        """Initialize timing and state tracking"""
        self.arrival_time = time.time()
        self.start_time: Optional[float] = None
        self.completion_time: Optional[float] = None
        self.state = JobState.READY
        
        # Execution tracking
        self.preemption_count = 0
        self.cpu_time = 0.0
        self.remaining_time = self.duration
        
    def start_execution(self):
        """Mark job as started"""
        if self.state == JobState.PAUSED:
            self.preemption_count += 1
        self.state = JobState.RUNNING
        if self.start_time is None:
            self.start_time = time.time()
    
    def pause_execution(self):
        """Pause job execution (preemption)"""
        if self.state == JobState.RUNNING:
            self.state = JobState.PAUSED
    
    def complete_execution(self):
        """Mark job as completed"""
        self.state = JobState.COMPLETED
        self.completion_time = time.time()
    
    def fail_execution(self):
        """Mark job as failed"""
        self.state = JobState.FAILED
        self.completion_time = time.time()
    
    @property
    def wait_time(self) -> Optional[float]:
        """Time from arrival to start of execution"""
        if self.start_time is None:
            return None
        return self.start_time - self.arrival_time
    
    @property
    def turnaround_time(self) -> Optional[float]:
        """Time from arrival to completion"""
        if self.completion_time is None:
            return None
        return self.completion_time - self.arrival_time
    
    @property
    def missed_deadline(self) -> bool:
        """Check if job missed its deadline"""
        if self.deadline is None or self.completion_time is None:
            return False
        return self.completion_time > self.deadline
    
    @property
    def slack_time(self) -> Optional[float]:
        """Time remaining before deadline (negative if missed)"""
        if self.deadline is None:
            return None
        current_time = self.completion_time if self.completion_time else time.time()
        return self.deadline - current_time
    
    def __lt__(self, other):
        """Comparison for priority queue ordering"""
        # Higher priority jobs are "less than" (come first in max-heap)
        return self.priority.value > other.priority.value
    
    def __repr__(self):
        return (f"TradingJob(id={self.job_id}, type={self.job_type.value}, "
                f"priority={self.priority.name}, duration={self.duration:.1f}s, "
                f"deadline={'Yes' if self.deadline else 'No'})")
