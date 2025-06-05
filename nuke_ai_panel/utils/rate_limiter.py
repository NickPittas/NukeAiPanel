"""
Rate limiting utilities for Nuke AI Panel.

Provides rate limiting functionality to prevent API abuse and respect
provider rate limits.
"""

import time
import asyncio
from typing import Dict, Optional, Any
from dataclasses import dataclass
from datetime import datetime, timedelta
from collections import deque
import threading

from .logger import get_logger

logger = get_logger(__name__)


@dataclass
class RateLimit:
    """Rate limit configuration."""
    requests_per_minute: int
    requests_per_hour: Optional[int] = None
    requests_per_day: Optional[int] = None
    burst_limit: Optional[int] = None


class RateLimiter:
    """
    Token bucket rate limiter with support for multiple time windows.
    
    Supports:
    - Requests per minute/hour/day limits
    - Burst limiting
    - Per-provider rate limiting
    - Async support
    """
    
    def __init__(self, rate_limit: RateLimit):
        """
        Initialize rate limiter.
        
        Args:
            rate_limit: Rate limit configuration
        """
        self.rate_limit = rate_limit
        self._lock = threading.Lock()
        
        # Token buckets for different time windows
        self._minute_tokens = rate_limit.requests_per_minute
        self._hour_tokens = rate_limit.requests_per_hour or float('inf')
        self._day_tokens = rate_limit.requests_per_day or float('inf')
        
        # Request history for sliding windows
        self._minute_requests = deque()
        self._hour_requests = deque()
        self._day_requests = deque()
        
        # Last refill times
        self._last_minute_refill = time.time()
        self._last_hour_refill = time.time()
        self._last_day_refill = time.time()
        
        # Burst limiting
        self._burst_tokens = rate_limit.burst_limit or rate_limit.requests_per_minute
        self._burst_requests = deque()
    
    def _cleanup_old_requests(self):
        """Remove old requests from history."""
        current_time = time.time()
        
        # Clean minute window
        while self._minute_requests and current_time - self._minute_requests[0] > 60:
            self._minute_requests.popleft()
        
        # Clean hour window
        while self._hour_requests and current_time - self._hour_requests[0] > 3600:
            self._hour_requests.popleft()
        
        # Clean day window
        while self._day_requests and current_time - self._day_requests[0] > 86400:
            self._day_requests.popleft()
        
        # Clean burst window (use 1 second for burst)
        while self._burst_requests and current_time - self._burst_requests[0] > 1:
            self._burst_requests.popleft()
    
    def _refill_tokens(self):
        """Refill token buckets based on elapsed time."""
        current_time = time.time()
        
        # Refill minute tokens
        if current_time - self._last_minute_refill >= 60:
            self._minute_tokens = self.rate_limit.requests_per_minute
            self._last_minute_refill = current_time
        
        # Refill hour tokens
        if current_time - self._last_hour_refill >= 3600:
            self._hour_tokens = self.rate_limit.requests_per_hour or float('inf')
            self._last_hour_refill = current_time
        
        # Refill day tokens
        if current_time - self._last_day_refill >= 86400:
            self._day_tokens = self.rate_limit.requests_per_day or float('inf')
            self._last_day_refill = current_time
        
        # Refill burst tokens (every second)
        if current_time - getattr(self, '_last_burst_refill', 0) >= 1:
            self._burst_tokens = self.rate_limit.burst_limit or self.rate_limit.requests_per_minute
            self._last_burst_refill = current_time
    
    def can_proceed(self) -> bool:
        """
        Check if a request can proceed without blocking.
        
        Returns:
            True if request can proceed, False otherwise
        """
        with self._lock:
            self._cleanup_old_requests()
            self._refill_tokens()
            
            # Check all limits
            minute_ok = len(self._minute_requests) < self.rate_limit.requests_per_minute
            hour_ok = (self.rate_limit.requests_per_hour is None or 
                      len(self._hour_requests) < self.rate_limit.requests_per_hour)
            day_ok = (self.rate_limit.requests_per_day is None or 
                     len(self._day_requests) < self.rate_limit.requests_per_day)
            burst_ok = (self.rate_limit.burst_limit is None or 
                       len(self._burst_requests) < self.rate_limit.burst_limit)
            
            return minute_ok and hour_ok and day_ok and burst_ok
    
    def acquire(self, timeout: Optional[float] = None) -> bool:
        """
        Acquire permission to make a request.
        
        Args:
            timeout: Maximum time to wait in seconds
            
        Returns:
            True if permission acquired, False if timeout
        """
        start_time = time.time()
        
        while True:
            if self.can_proceed():
                with self._lock:
                    current_time = time.time()
                    
                    # Record the request
                    self._minute_requests.append(current_time)
                    self._hour_requests.append(current_time)
                    self._day_requests.append(current_time)
                    self._burst_requests.append(current_time)
                    
                    # Consume tokens
                    self._minute_tokens -= 1
                    self._hour_tokens -= 1
                    self._day_tokens -= 1
                    self._burst_tokens -= 1
                
                return True
            
            # Check timeout
            if timeout is not None and time.time() - start_time >= timeout:
                return False
            
            # Wait a bit before retrying
            time.sleep(0.1)
    
    async def acquire_async(self, timeout: Optional[float] = None) -> bool:
        """
        Async version of acquire.
        
        Args:
            timeout: Maximum time to wait in seconds
            
        Returns:
            True if permission acquired, False if timeout
        """
        start_time = time.time()
        
        while True:
            if self.can_proceed():
                with self._lock:
                    current_time = time.time()
                    
                    # Record the request
                    self._minute_requests.append(current_time)
                    self._hour_requests.append(current_time)
                    self._day_requests.append(current_time)
                    self._burst_requests.append(current_time)
                    
                    # Consume tokens
                    self._minute_tokens -= 1
                    self._hour_tokens -= 1
                    self._day_tokens -= 1
                    self._burst_tokens -= 1
                
                return True
            
            # Check timeout
            if timeout is not None and time.time() - start_time >= timeout:
                return False
            
            # Wait a bit before retrying
            await asyncio.sleep(0.1)
    
    def get_wait_time(self) -> float:
        """
        Get the time to wait before next request can proceed.
        
        Returns:
            Wait time in seconds
        """
        with self._lock:
            self._cleanup_old_requests()
            
            wait_times = []
            current_time = time.time()
            
            # Check minute limit
            if len(self._minute_requests) >= self.rate_limit.requests_per_minute:
                oldest_request = self._minute_requests[0]
                wait_times.append(60 - (current_time - oldest_request))
            
            # Check hour limit
            if (self.rate_limit.requests_per_hour and 
                len(self._hour_requests) >= self.rate_limit.requests_per_hour):
                oldest_request = self._hour_requests[0]
                wait_times.append(3600 - (current_time - oldest_request))
            
            # Check day limit
            if (self.rate_limit.requests_per_day and 
                len(self._day_requests) >= self.rate_limit.requests_per_day):
                oldest_request = self._day_requests[0]
                wait_times.append(86400 - (current_time - oldest_request))
            
            # Check burst limit
            if (self.rate_limit.burst_limit and 
                len(self._burst_requests) >= self.rate_limit.burst_limit):
                oldest_request = self._burst_requests[0]
                wait_times.append(1 - (current_time - oldest_request))
            
            return max(wait_times) if wait_times else 0
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get rate limiter statistics.
        
        Returns:
            Dictionary with statistics
        """
        with self._lock:
            self._cleanup_old_requests()
            
            return {
                'requests_last_minute': len(self._minute_requests),
                'requests_last_hour': len(self._hour_requests),
                'requests_last_day': len(self._day_requests),
                'burst_requests': len(self._burst_requests),
                'minute_limit': self.rate_limit.requests_per_minute,
                'hour_limit': self.rate_limit.requests_per_hour,
                'day_limit': self.rate_limit.requests_per_day,
                'burst_limit': self.rate_limit.burst_limit,
                'can_proceed': self.can_proceed(),
                'wait_time': self.get_wait_time()
            }


class ProviderRateLimiter:
    """
    Rate limiter manager for multiple providers.
    
    Manages separate rate limiters for each AI provider.
    """
    
    def __init__(self):
        """Initialize provider rate limiter."""
        self._limiters: Dict[str, RateLimiter] = {}
        self._lock = threading.Lock()
    
    def add_provider(self, provider: str, rate_limit: RateLimit):
        """
        Add rate limiter for a provider.
        
        Args:
            provider: Provider name
            rate_limit: Rate limit configuration
        """
        with self._lock:
            self._limiters[provider] = RateLimiter(rate_limit)
        logger.debug(f"Added rate limiter for provider: {provider}")
    
    def remove_provider(self, provider: str):
        """
        Remove rate limiter for a provider.
        
        Args:
            provider: Provider name
        """
        with self._lock:
            if provider in self._limiters:
                del self._limiters[provider]
        logger.debug(f"Removed rate limiter for provider: {provider}")
    
    def get_limiter(self, provider: str) -> Optional[RateLimiter]:
        """
        Get rate limiter for a provider.
        
        Args:
            provider: Provider name
            
        Returns:
            RateLimiter instance or None if not found
        """
        with self._lock:
            return self._limiters.get(provider)
    
    def can_proceed(self, provider: str) -> bool:
        """
        Check if a request can proceed for a provider.
        
        Args:
            provider: Provider name
            
        Returns:
            True if request can proceed, False otherwise
        """
        limiter = self.get_limiter(provider)
        if limiter is None:
            return True  # No rate limit configured
        return limiter.can_proceed()
    
    def acquire(self, provider: str, timeout: Optional[float] = None) -> bool:
        """
        Acquire permission for a provider request.
        
        Args:
            provider: Provider name
            timeout: Maximum time to wait in seconds
            
        Returns:
            True if permission acquired, False if timeout
        """
        limiter = self.get_limiter(provider)
        if limiter is None:
            return True  # No rate limit configured
        return limiter.acquire(timeout)
    
    async def acquire_async(self, provider: str, timeout: Optional[float] = None) -> bool:
        """
        Async acquire permission for a provider request.
        
        Args:
            provider: Provider name
            timeout: Maximum time to wait in seconds
            
        Returns:
            True if permission acquired, False if timeout
        """
        limiter = self.get_limiter(provider)
        if limiter is None:
            return True  # No rate limit configured
        return await limiter.acquire_async(timeout)
    
    def get_wait_time(self, provider: str) -> float:
        """
        Get wait time for a provider.
        
        Args:
            provider: Provider name
            
        Returns:
            Wait time in seconds
        """
        limiter = self.get_limiter(provider)
        if limiter is None:
            return 0
        return limiter.get_wait_time()
    
    def get_stats(self, provider: Optional[str] = None) -> Dict[str, Any]:
        """
        Get statistics for providers.
        
        Args:
            provider: Specific provider name or None for all
            
        Returns:
            Dictionary with statistics
        """
        with self._lock:
            if provider:
                limiter = self._limiters.get(provider)
                if limiter:
                    return {provider: limiter.get_stats()}
                return {}
            else:
                return {
                    name: limiter.get_stats() 
                    for name, limiter in self._limiters.items()
                }


def rate_limited(provider: str, rate_limiter: ProviderRateLimiter, timeout: Optional[float] = None):
    """
    Decorator for rate limiting function calls.
    
    Args:
        provider: Provider name
        rate_limiter: ProviderRateLimiter instance
        timeout: Maximum time to wait for rate limit
        
    Usage:
        @rate_limited("openai", my_rate_limiter)
        def call_openai_api():
            return openai.chat.completions.create(...)
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            if not rate_limiter.acquire(provider, timeout):
                raise Exception(f"Rate limit exceeded for provider {provider}")
            return func(*args, **kwargs)
        return wrapper
    return decorator


def async_rate_limited(provider: str, rate_limiter: ProviderRateLimiter, timeout: Optional[float] = None):
    """
    Decorator for rate limiting async function calls.
    
    Args:
        provider: Provider name
        rate_limiter: ProviderRateLimiter instance
        timeout: Maximum time to wait for rate limit
        
    Usage:
        @async_rate_limited("openai", my_rate_limiter)
        async def call_openai_api():
            return await openai.chat.completions.acreate(...)
    """
    def decorator(func):
        async def wrapper(*args, **kwargs):
            if not await rate_limiter.acquire_async(provider, timeout):
                raise Exception(f"Rate limit exceeded for provider {provider}")
            return await func(*args, **kwargs)
        return wrapper
    return decorator


# Global rate limiter instance
_global_rate_limiter: Optional[ProviderRateLimiter] = None


def get_global_rate_limiter() -> ProviderRateLimiter:
    """Get the global rate limiter instance."""
    global _global_rate_limiter
    if _global_rate_limiter is None:
        _global_rate_limiter = ProviderRateLimiter()
    return _global_rate_limiter