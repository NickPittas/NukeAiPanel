"""
Retry utilities for Nuke AI Panel.

Provides robust retry mechanisms with exponential backoff, jitter,
and configurable retry conditions.
"""

import asyncio
import random
import time
from typing import Callable, Any, Optional, Union, Type, Tuple
from functools import wraps
from dataclasses import dataclass

from tenacity import (
    Retrying,
    RetryError,
    stop_after_attempt,
    stop_after_delay,
    wait_exponential,
    wait_fixed,
    wait_random,
    retry_if_exception_type,
    retry_if_result,
    before_sleep_log,
    after_log
)

from .logger import get_logger
from ..core.exceptions import (
    APIError,
    RateLimitError,
    AuthenticationError,
    ProviderError
)

logger = get_logger(__name__)


@dataclass
class RetryConfig:
    """Configuration for retry behavior."""
    max_attempts: int = 3
    base_delay: float = 1.0
    max_delay: float = 60.0
    exponential_base: float = 2.0
    jitter: bool = True
    retry_on_exceptions: Tuple[Type[Exception], ...] = (
        APIError,
        RateLimitError,
        ConnectionError,
        TimeoutError,
    )
    stop_on_exceptions: Tuple[Type[Exception], ...] = (
        AuthenticationError,
    )


def should_retry_exception(exception: Exception, retry_config: RetryConfig) -> bool:
    """
    Determine if an exception should trigger a retry.
    
    Args:
        exception: The exception that occurred
        retry_config: Retry configuration
        
    Returns:
        True if should retry, False otherwise
    """
    # Never retry these exceptions
    if isinstance(exception, retry_config.stop_on_exceptions):
        return False
    
    # Retry these exceptions
    if isinstance(exception, retry_config.retry_on_exceptions):
        return True
    
    # Special handling for rate limit errors
    if isinstance(exception, RateLimitError):
        return True
    
    # Special handling for API errors with specific status codes
    if isinstance(exception, APIError):
        # Retry on server errors (5xx) and some client errors
        if exception.status_code:
            return exception.status_code >= 500 or exception.status_code in [408, 429]
    
    return False


def calculate_delay(attempt: int, config: RetryConfig) -> float:
    """
    Calculate delay for retry attempt.
    
    Args:
        attempt: Current attempt number (1-based)
        config: Retry configuration
        
    Returns:
        Delay in seconds
    """
    # Exponential backoff
    delay = config.base_delay * (config.exponential_base ** (attempt - 1))
    
    # Cap at max delay
    delay = min(delay, config.max_delay)
    
    # Add jitter to prevent thundering herd
    if config.jitter:
        jitter_amount = delay * 0.1  # 10% jitter
        delay += random.uniform(-jitter_amount, jitter_amount)
    
    return max(0, delay)


def retry_with_backoff(
    max_attempts: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    exponential_base: float = 2.0,
    jitter: bool = True,
    retry_on: Optional[Tuple[Type[Exception], ...]] = None,
    stop_on: Optional[Tuple[Type[Exception], ...]] = None,
    before_retry: Optional[Callable] = None,
    after_retry: Optional[Callable] = None
):
    """
    Decorator for retrying functions with exponential backoff.
    
    Args:
        max_attempts: Maximum number of retry attempts
        base_delay: Base delay between retries in seconds
        max_delay: Maximum delay between retries in seconds
        exponential_base: Base for exponential backoff
        jitter: Whether to add random jitter to delays
        retry_on: Tuple of exception types to retry on
        stop_on: Tuple of exception types to never retry on
        before_retry: Callback called before each retry
        after_retry: Callback called after each retry
        
    Usage:
        @retry_with_backoff(max_attempts=5, base_delay=2.0)
        def unreliable_function():
            # Function that might fail
            pass
    """
    config = RetryConfig(
        max_attempts=max_attempts,
        base_delay=base_delay,
        max_delay=max_delay,
        exponential_base=exponential_base,
        jitter=jitter,
        retry_on_exceptions=retry_on or RetryConfig.retry_on_exceptions,
        stop_on_exceptions=stop_on or RetryConfig.stop_on_exceptions
    )
    
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            
            for attempt in range(1, config.max_attempts + 1):
                try:
                    result = func(*args, **kwargs)
                    
                    # Call after_retry callback on success
                    if after_retry and attempt > 1:
                        after_retry(attempt - 1, None, result)
                    
                    return result
                    
                except Exception as e:
                    last_exception = e
                    
                    # Check if we should retry
                    if not should_retry_exception(e, config):
                        logger.error(f"Not retrying {func.__name__} due to {type(e).__name__}: {e}")
                        raise
                    
                    # Don't retry on last attempt
                    if attempt == config.max_attempts:
                        logger.error(f"Max attempts ({config.max_attempts}) reached for {func.__name__}")
                        raise
                    
                    # Calculate delay
                    delay = calculate_delay(attempt, config)
                    
                    # Log retry attempt
                    logger.warning(
                        f"Attempt {attempt}/{config.max_attempts} failed for {func.__name__}: "
                        f"{type(e).__name__}: {e}. Retrying in {delay:.2f}s"
                    )
                    
                    # Call before_retry callback
                    if before_retry:
                        before_retry(attempt, e, delay)
                    
                    # Wait before retry
                    time.sleep(delay)
                    
                    # Call after_retry callback
                    if after_retry:
                        after_retry(attempt, e, None)
            
            # This should never be reached, but just in case
            if last_exception:
                raise last_exception
        
        return wrapper
    return decorator


def async_retry_with_backoff(
    max_attempts: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    exponential_base: float = 2.0,
    jitter: bool = True,
    retry_on: Optional[Tuple[Type[Exception], ...]] = None,
    stop_on: Optional[Tuple[Type[Exception], ...]] = None,
    before_retry: Optional[Callable] = None,
    after_retry: Optional[Callable] = None
):
    """
    Decorator for retrying async functions with exponential backoff.
    
    Args:
        max_attempts: Maximum number of retry attempts
        base_delay: Base delay between retries in seconds
        max_delay: Maximum delay between retries in seconds
        exponential_base: Base for exponential backoff
        jitter: Whether to add random jitter to delays
        retry_on: Tuple of exception types to retry on
        stop_on: Tuple of exception types to never retry on
        before_retry: Callback called before each retry
        after_retry: Callback called after each retry
        
    Usage:
        @async_retry_with_backoff(max_attempts=5, base_delay=2.0)
        async def unreliable_async_function():
            # Async function that might fail
            pass
    """
    config = RetryConfig(
        max_attempts=max_attempts,
        base_delay=base_delay,
        max_delay=max_delay,
        exponential_base=exponential_base,
        jitter=jitter,
        retry_on_exceptions=retry_on or RetryConfig.retry_on_exceptions,
        stop_on_exceptions=stop_on or RetryConfig.stop_on_exceptions
    )
    
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            last_exception = None
            
            for attempt in range(1, config.max_attempts + 1):
                try:
                    result = await func(*args, **kwargs)
                    
                    # Call after_retry callback on success
                    if after_retry and attempt > 1:
                        if asyncio.iscoroutinefunction(after_retry):
                            await after_retry(attempt - 1, None, result)
                        else:
                            after_retry(attempt - 1, None, result)
                    
                    return result
                    
                except Exception as e:
                    last_exception = e
                    
                    # Check if we should retry
                    if not should_retry_exception(e, config):
                        logger.error(f"Not retrying {func.__name__} due to {type(e).__name__}: {e}")
                        raise
                    
                    # Don't retry on last attempt
                    if attempt == config.max_attempts:
                        logger.error(f"Max attempts ({config.max_attempts}) reached for {func.__name__}")
                        raise
                    
                    # Calculate delay
                    delay = calculate_delay(attempt, config)
                    
                    # Log retry attempt
                    logger.warning(
                        f"Attempt {attempt}/{config.max_attempts} failed for {func.__name__}: "
                        f"{type(e).__name__}: {e}. Retrying in {delay:.2f}s"
                    )
                    
                    # Call before_retry callback
                    if before_retry:
                        if asyncio.iscoroutinefunction(before_retry):
                            await before_retry(attempt, e, delay)
                        else:
                            before_retry(attempt, e, delay)
                    
                    # Wait before retry
                    await asyncio.sleep(delay)
                    
                    # Call after_retry callback
                    if after_retry:
                        if asyncio.iscoroutinefunction(after_retry):
                            await after_retry(attempt, e, None)
                        else:
                            after_retry(attempt, e, None)
            
            # This should never be reached, but just in case
            if last_exception:
                raise last_exception
        
        return wrapper
    return decorator


class RetryManager:
    """
    Advanced retry manager with configurable strategies.
    
    Provides more control over retry behavior including custom
    retry conditions and callbacks.
    """
    
    def __init__(self, config: Optional[RetryConfig] = None):
        """
        Initialize retry manager.
        
        Args:
            config: Retry configuration
        """
        self.config = config or RetryConfig()
        self.stats = {
            'total_attempts': 0,
            'successful_retries': 0,
            'failed_retries': 0,
            'exceptions_by_type': {}
        }
    
    def execute(self, func: Callable, *args, **kwargs) -> Any:
        """
        Execute a function with retry logic.
        
        Args:
            func: Function to execute
            *args: Function arguments
            **kwargs: Function keyword arguments
            
        Returns:
            Function result
            
        Raises:
            Last exception if all retries fail
        """
        last_exception = None
        
        for attempt in range(1, self.config.max_attempts + 1):
            self.stats['total_attempts'] += 1
            
            try:
                result = func(*args, **kwargs)
                
                if attempt > 1:
                    self.stats['successful_retries'] += 1
                    logger.info(f"Function {func.__name__} succeeded on attempt {attempt}")
                
                return result
                
            except Exception as e:
                last_exception = e
                exception_type = type(e).__name__
                self.stats['exceptions_by_type'][exception_type] = (
                    self.stats['exceptions_by_type'].get(exception_type, 0) + 1
                )
                
                # Check if we should retry
                if not should_retry_exception(e, self.config):
                    logger.error(f"Not retrying {func.__name__} due to {exception_type}: {e}")
                    raise
                
                # Don't retry on last attempt
                if attempt == self.config.max_attempts:
                    self.stats['failed_retries'] += 1
                    logger.error(f"Max attempts ({self.config.max_attempts}) reached for {func.__name__}")
                    raise
                
                # Calculate delay and wait
                delay = calculate_delay(attempt, self.config)
                logger.warning(
                    f"Attempt {attempt}/{self.config.max_attempts} failed for {func.__name__}: "
                    f"{exception_type}: {e}. Retrying in {delay:.2f}s"
                )
                time.sleep(delay)
        
        # This should never be reached
        if last_exception:
            raise last_exception
    
    async def execute_async(self, func: Callable, *args, **kwargs) -> Any:
        """
        Execute an async function with retry logic.
        
        Args:
            func: Async function to execute
            *args: Function arguments
            **kwargs: Function keyword arguments
            
        Returns:
            Function result
            
        Raises:
            Last exception if all retries fail
        """
        last_exception = None
        
        for attempt in range(1, self.config.max_attempts + 1):
            self.stats['total_attempts'] += 1
            
            try:
                result = await func(*args, **kwargs)
                
                if attempt > 1:
                    self.stats['successful_retries'] += 1
                    logger.info(f"Async function {func.__name__} succeeded on attempt {attempt}")
                
                return result
                
            except Exception as e:
                last_exception = e
                exception_type = type(e).__name__
                self.stats['exceptions_by_type'][exception_type] = (
                    self.stats['exceptions_by_type'].get(exception_type, 0) + 1
                )
                
                # Check if we should retry
                if not should_retry_exception(e, self.config):
                    logger.error(f"Not retrying {func.__name__} due to {exception_type}: {e}")
                    raise
                
                # Don't retry on last attempt
                if attempt == self.config.max_attempts:
                    self.stats['failed_retries'] += 1
                    logger.error(f"Max attempts ({self.config.max_attempts}) reached for {func.__name__}")
                    raise
                
                # Calculate delay and wait
                delay = calculate_delay(attempt, self.config)
                logger.warning(
                    f"Attempt {attempt}/{self.config.max_attempts} failed for {func.__name__}: "
                    f"{exception_type}: {e}. Retrying in {delay:.2f}s"
                )
                await asyncio.sleep(delay)
        
        # This should never be reached
        if last_exception:
            raise last_exception
    
    def get_stats(self) -> dict:
        """Get retry statistics."""
        total_attempts = self.stats['total_attempts']
        success_rate = (
            (total_attempts - self.stats['failed_retries']) / total_attempts
            if total_attempts > 0 else 0
        )
        
        return {
            'total_attempts': total_attempts,
            'successful_retries': self.stats['successful_retries'],
            'failed_retries': self.stats['failed_retries'],
            'success_rate': success_rate,
            'exceptions_by_type': self.stats['exceptions_by_type'].copy()
        }
    
    def reset_stats(self):
        """Reset retry statistics."""
        self.stats = {
            'total_attempts': 0,
            'successful_retries': 0,
            'failed_retries': 0,
            'exceptions_by_type': {}
        }


# Global retry manager instance
_global_retry_manager: Optional[RetryManager] = None


def get_global_retry_manager() -> RetryManager:
    """Get the global retry manager instance."""
    global _global_retry_manager
    if _global_retry_manager is None:
        _global_retry_manager = RetryManager()
    return _global_retry_manager