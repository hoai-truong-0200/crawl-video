"""
Timing and Delay Management

Provides human-like timing for actions with randomization.
Prevents detection through consistent timing patterns.
"""

import random
import time
import asyncio
from typing import Optional, Tuple
from enum import Enum


class ActionType(Enum):
    """Types of actions with different timing characteristics"""
    PAGE_LOAD = "page_load"
    CLICK = "click"
    TYPING = "typing"
    READING = "reading"
    THINKING = "thinking"
    SCROLLING = "scrolling"
    NAVIGATION = "navigation"
    FORM_SUBMIT = "form_submit"


class TimingConfig:
    """Configuration for timing delays"""

    # Delay ranges in seconds (min, max)
    DELAYS = {
        ActionType.PAGE_LOAD: (2.0, 5.0),      # Wait after page loads
        ActionType.CLICK: (0.3, 0.8),          # Before/after clicks
        ActionType.TYPING: (0.05, 0.15),       # Between keystrokes
        ActionType.READING: (2.0, 5.0),        # Simulated reading time
        ActionType.THINKING: (1.0, 3.0),       # Decision making
        ActionType.SCROLLING: (0.5, 1.5),      # Between scroll actions
        ActionType.NAVIGATION: (1.5, 3.5),     # Between page navigations
        ActionType.FORM_SUBMIT: (0.5, 1.5),    # Before submitting forms
    }

    def __init__(self, randomness_factor: float = 1.0):
        """
        Initialize timing configuration

        Args:
            randomness_factor: Multiplier for delays (0.5-2.0)
                              Lower = faster, Higher = more cautious
        """
        self.randomness_factor = max(0.1, min(randomness_factor, 3.0))

    def get_delay(
        self,
        action_type: ActionType,
        variance: float = 0.2
    ) -> float:
        """
        Get randomized delay for action type

        Args:
            action_type: Type of action
            variance: Additional random variance (0.0-1.0)

        Returns:
            Delay in seconds
        """
        min_delay, max_delay = self.DELAYS[action_type]

        # Apply randomness factor
        min_delay *= self.randomness_factor
        max_delay *= self.randomness_factor

        # Add variance
        if variance > 0:
            range_size = max_delay - min_delay
            min_delay -= range_size * variance * random.random()
            max_delay += range_size * variance * random.random()

        # Generate random delay
        delay = random.uniform(min_delay, max_delay)

        return max(0.05, delay)  # Minimum 50ms

    def get_delay_range(
        self,
        action_type: ActionType
    ) -> Tuple[float, float]:
        """
        Get delay range for action type

        Args:
            action_type: Type of action

        Returns:
            (min_delay, max_delay) tuple in seconds
        """
        min_delay, max_delay = self.DELAYS[action_type]
        return (
            min_delay * self.randomness_factor,
            max_delay * self.randomness_factor
        )


class DelayManager:
    """Manage delays with timing intelligence"""

    def __init__(self, config: Optional[TimingConfig] = None):
        """
        Initialize delay manager

        Args:
            config: TimingConfig instance
        """
        self.config = config or TimingConfig()
        self.last_action_time = time.time()
        self.action_count = 0

    async def wait(
        self,
        action_type: ActionType,
        variance: float = 0.2
    ) -> float:
        """
        Wait for appropriate delay before action

        Args:
            action_type: Type of action to perform
            variance: Additional random variance

        Returns:
            Actual delay used (seconds)
        """
        delay = self.config.get_delay(action_type, variance)

        # Adjust for rapid actions (add extra delay)
        time_since_last = time.time() - self.last_action_time
        if time_since_last < 0.5:
            delay += random.uniform(0.2, 0.5)

        # Log action
        self.last_action_time = time.time()
        self.action_count += 1

        # Perform delay
        await asyncio.sleep(delay)

        return delay

    def wait_sync(
        self,
        action_type: ActionType,
        variance: float = 0.2
    ) -> float:
        """
        Synchronous version of wait()

        Args:
            action_type: Type of action to perform
            variance: Additional random variance

        Returns:
            Actual delay used (seconds)
        """
        delay = self.config.get_delay(action_type, variance)

        # Adjust for rapid actions
        time_since_last = time.time() - self.last_action_time
        if time_since_last < 0.5:
            delay += random.uniform(0.2, 0.5)

        # Log action
        self.last_action_time = time.time()
        self.action_count += 1

        # Perform delay
        time.sleep(delay)

        return delay

    async def random_pause(
        self,
        min_seconds: float = 0.5,
        max_seconds: float = 2.0
    ) -> float:
        """
        Add random pause (for unpredictability)

        Args:
            min_seconds: Minimum pause duration
            max_seconds: Maximum pause duration

        Returns:
            Actual pause duration
        """
        pause = random.uniform(min_seconds, max_seconds)
        await asyncio.sleep(pause)
        return pause

    async def reading_delay(
        self,
        content_length: Optional[int] = None
    ) -> float:
        """
        Simulate reading time based on content length

        Args:
            content_length: Number of characters/words to read

        Returns:
            Reading time in seconds
        """
        if content_length:
            # Average reading speed: 200-300 words per minute
            # Assuming ~5 characters per word
            words = content_length / 5
            reading_time = (words / 250) * 60  # seconds
            # Add randomness
            reading_time *= random.uniform(0.7, 1.3)
        else:
            # Default reading delay
            reading_time = self.config.get_delay(ActionType.READING)

        await asyncio.sleep(reading_time)
        return reading_time

    async def thinking_delay(self) -> float:
        """
        Simulate thinking/decision time

        Returns:
            Thinking time in seconds
        """
        return await self.wait(ActionType.THINKING)

    def get_stats(self) -> dict:
        """
        Get timing statistics

        Returns:
            Dictionary with stats
        """
        return {
            "total_actions": self.action_count,
            "average_time_between_actions": (
                (time.time() - self.last_action_time) / max(self.action_count, 1)
            ),
            "randomness_factor": self.config.randomness_factor,
        }

    def reset_stats(self) -> None:
        """Reset statistics"""
        self.action_count = 0
        self.last_action_time = time.time()


class RateLimiter:
    """Rate limiting to avoid detection"""

    def __init__(
        self,
        max_actions_per_minute: int = 30,
        max_actions_per_hour: int = 1000
    ):
        """
        Initialize rate limiter

        Args:
            max_actions_per_minute: Maximum actions per minute
            max_actions_per_hour: Maximum actions per hour
        """
        self.max_per_minute = max_actions_per_minute
        self.max_per_hour = max_actions_per_hour

        self.minute_window: list[float] = []
        self.hour_window: list[float] = []

    async def acquire(self) -> None:
        """
        Acquire permission to perform action
        Blocks if rate limit would be exceeded
        """
        current_time = time.time()

        # Clean up old timestamps
        self.minute_window = [
            t for t in self.minute_window
            if current_time - t < 60
        ]
        self.hour_window = [
            t for t in self.hour_window
            if current_time - t < 3600
        ]

        # Check minute limit
        if len(self.minute_window) >= self.max_per_minute:
            # Wait until oldest action expires
            wait_time = 60 - (current_time - self.minute_window[0]) + random.uniform(1, 3)
            await asyncio.sleep(max(0, wait_time))
            current_time = time.time()

        # Check hour limit
        if len(self.hour_window) >= self.max_per_hour:
            # Wait until oldest action expires
            wait_time = 3600 - (current_time - self.hour_window[0]) + random.uniform(10, 30)
            await asyncio.sleep(max(0, wait_time))
            current_time = time.time()

        # Record action
        self.minute_window.append(current_time)
        self.hour_window.append(current_time)

    def get_stats(self) -> dict:
        """
        Get rate limiting statistics

        Returns:
            Dictionary with stats
        """
        current_time = time.time()

        # Clean up
        self.minute_window = [
            t for t in self.minute_window
            if current_time - t < 60
        ]
        self.hour_window = [
            t for t in self.hour_window
            if current_time - t < 3600
        ]

        return {
            "actions_last_minute": len(self.minute_window),
            "actions_last_hour": len(self.hour_window),
            "minute_limit": self.max_per_minute,
            "hour_limit": self.max_per_hour,
            "minute_available": self.max_per_minute - len(self.minute_window),
            "hour_available": self.max_per_hour - len(self.hour_window),
        }


# Global instances for convenience
default_timing = TimingConfig()
default_delay_manager = DelayManager()
default_rate_limiter = RateLimiter()
