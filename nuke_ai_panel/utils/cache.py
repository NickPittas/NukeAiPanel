"""
Caching utilities for Nuke AI Panel.

Provides in-memory and persistent caching with TTL support, encryption,
and automatic cleanup.
"""

import json
import pickle
import hashlib
import time
from typing import Any, Optional, Dict, Union, Callable
from pathlib import Path
from threading import Lock
from dataclasses import dataclass
from datetime import datetime, timedelta
import asyncio

# Handle optional dependencies gracefully
try:
    from cryptography.fernet import Fernet
    HAS_CRYPTOGRAPHY = True
except ImportError:
    HAS_CRYPTOGRAPHY = False
    Fernet = None

try:
    from cachetools import TTLCache, LRUCache
    HAS_CACHETOOLS = True
except ImportError:
    HAS_CACHETOOLS = False
    # Simple fallback implementations
    class TTLCache(dict):
        def __init__(self, maxsize=1000, ttl=3600):
            super().__init__()
            self.maxsize = maxsize
            self.ttl = ttl
    
    class LRUCache(dict):
        def __init__(self, maxsize=1000):
            super().__init__()
            self.maxsize = maxsize

from .logger import get_logger

logger = get_logger(__name__)


@dataclass
class CacheEntry:
    """Represents a cache entry with metadata."""
    value: Any
    created_at: datetime
    expires_at: Optional[datetime]
    access_count: int = 0
    last_accessed: Optional[datetime] = None
    metadata: Optional[Dict[str, Any]] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}
        if self.last_accessed is None:
            self.last_accessed = self.created_at
    
    def is_expired(self) -> bool:
        """Check if the cache entry has expired."""
        if self.expires_at is None:
            return False
        return datetime.now() > self.expires_at
    
    def touch(self):
        """Update access information."""
        self.access_count += 1
        self.last_accessed = datetime.now()


class CacheManager:
    """
    Advanced cache manager with support for in-memory and persistent caching.
    
    Features:
    - TTL (Time To Live) support
    - LRU (Least Recently Used) eviction
    - Persistent storage with encryption
    - Async support
    - Cache statistics
    - Automatic cleanup
    """
    
    def __init__(
        self,
        max_size: int = 1000,
        ttl_seconds: int = 3600,
        cache_dir: Optional[Path] = None,
        encrypt: bool = True,
        persistent: bool = True
    ):
        """
        Initialize the cache manager.
        
        Args:
            max_size: Maximum number of items in cache
            ttl_seconds: Default TTL for cache entries
            cache_dir: Directory for persistent cache storage
            encrypt: Whether to encrypt persistent cache
            persistent: Whether to use persistent storage
        """
        self.max_size = max_size
        self.ttl_seconds = ttl_seconds
        self.encrypt = encrypt
        self.persistent = persistent
        
        # Set up cache directory
        if cache_dir is None:
            cache_dir = Path.home() / ".nuke_ai_panel" / "cache"
        self.cache_dir = cache_dir
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # In-memory cache
        self._memory_cache: TTLCache = TTLCache(maxsize=max_size, ttl=ttl_seconds)
        self._cache_lock = Lock()
        
        # Encryption setup
        self._fernet: Optional[Fernet] = None
        if encrypt:
            self._setup_encryption()
        
        # Statistics
        self._stats = {
            'hits': 0,
            'misses': 0,
            'sets': 0,
            'deletes': 0,
            'evictions': 0
        }
        
        # Load persistent cache
        if persistent:
            self._load_persistent_cache()
    
    def _setup_encryption(self):
        """Set up encryption for persistent cache."""
        if not HAS_CRYPTOGRAPHY:
            logger.warning("Cryptography not available, disabling cache encryption")
            self.encrypt = False
            return
            
        key_file = self.cache_dir / "cache.key"
        
        try:
            if key_file.exists():
                with open(key_file, 'rb') as f:
                    key = f.read()
            else:
                key = Fernet.generate_key()
                with open(key_file, 'wb') as f:
                    f.write(key)
                # Set restrictive permissions
                key_file.chmod(0o600)
            
            self._fernet = Fernet(key)
            logger.debug("Cache encryption initialized")
            
        except Exception as e:
            logger.error(f"Failed to setup cache encryption: {e}")
            self.encrypt = False
    
    def _load_persistent_cache(self):
        """Load cache from persistent storage."""
        cache_file = self.cache_dir / "cache.dat"
        
        if not cache_file.exists():
            return
        
        try:
            with open(cache_file, 'rb') as f:
                data = f.read()
            
            if self.encrypt and self._fernet:
                data = self._fernet.decrypt(data)
            
            cache_data = pickle.loads(data)
            
            # Restore non-expired entries
            current_time = datetime.now()
            loaded_count = 0
            
            for key, entry in cache_data.items():
                if not entry.is_expired():
                    with self._cache_lock:
                        self._memory_cache[key] = entry
                    loaded_count += 1
            
            logger.info(f"Loaded {loaded_count} cache entries from persistent storage")
            
        except Exception as e:
            logger.error(f"Failed to load persistent cache: {e}")
    
    def _save_persistent_cache(self):
        """Save cache to persistent storage."""
        if not self.persistent:
            return
        
        cache_file = self.cache_dir / "cache.dat"
        
        try:
            # Get current cache state
            with self._cache_lock:
                cache_data = dict(self._memory_cache)
            
            # Serialize
            data = pickle.dumps(cache_data)
            
            # Encrypt if enabled
            if self.encrypt and self._fernet:
                data = self._fernet.encrypt(data)
            
            # Write to file
            with open(cache_file, 'wb') as f:
                f.write(data)
            
            logger.debug(f"Saved {len(cache_data)} cache entries to persistent storage")
            
        except Exception as e:
            logger.error(f"Failed to save persistent cache: {e}")
    
    def _generate_key(self, key: Union[str, tuple, dict]) -> str:
        """Generate a consistent cache key from various input types."""
        if isinstance(key, str):
            return key
        elif isinstance(key, (tuple, list)):
            key_str = "|".join(str(item) for item in key)
        elif isinstance(key, dict):
            key_str = "|".join(f"{k}:{v}" for k, v in sorted(key.items()))
        else:
            key_str = str(key)
        
        # Hash long keys to keep them manageable
        if len(key_str) > 250:
            return hashlib.sha256(key_str.encode()).hexdigest()
        
        return key_str
    
    def get(self, key: Union[str, tuple, dict], default: Any = None) -> Any:
        """
        Get a value from the cache.
        
        Args:
            key: Cache key
            default: Default value if key not found
            
        Returns:
            Cached value or default
        """
        cache_key = self._generate_key(key)
        
        with self._cache_lock:
            if cache_key in self._memory_cache:
                entry = self._memory_cache[cache_key]
                if not entry.is_expired():
                    entry.touch()
                    self._stats['hits'] += 1
                    return entry.value
                else:
                    # Remove expired entry
                    del self._memory_cache[cache_key]
        
        self._stats['misses'] += 1
        return default
    
    def set(
        self,
        key: Union[str, tuple, dict],
        value: Any,
        ttl: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Set a value in the cache.
        
        Args:
            key: Cache key
            value: Value to cache
            ttl: TTL in seconds (uses default if None)
            metadata: Optional metadata for the entry
        """
        cache_key = self._generate_key(key)
        ttl = ttl or self.ttl_seconds
        
        # Create cache entry
        created_at = datetime.now()
        expires_at = created_at + timedelta(seconds=ttl) if ttl > 0 else None
        
        entry = CacheEntry(
            value=value,
            created_at=created_at,
            expires_at=expires_at,
            metadata=metadata
        )
        
        with self._cache_lock:
            self._memory_cache[cache_key] = entry
        
        self._stats['sets'] += 1
        logger.debug(f"Cached value for key: {cache_key}")
    
    def delete(self, key: Union[str, tuple, dict]) -> bool:
        """
        Delete a value from the cache.
        
        Args:
            key: Cache key
            
        Returns:
            True if key was deleted, False if not found
        """
        cache_key = self._generate_key(key)
        
        with self._cache_lock:
            if cache_key in self._memory_cache:
                del self._memory_cache[cache_key]
                self._stats['deletes'] += 1
                return True
        
        return False
    
    def clear(self):
        """Clear all cache entries."""
        with self._cache_lock:
            self._memory_cache.clear()
        logger.info("Cleared all cache entries")
    
    def cleanup_expired(self) -> int:
        """
        Remove expired entries from cache.
        
        Returns:
            Number of entries removed
        """
        removed_count = 0
        current_time = datetime.now()
        
        with self._cache_lock:
            expired_keys = []
            for key, entry in self._memory_cache.items():
                if entry.is_expired():
                    expired_keys.append(key)
            
            for key in expired_keys:
                del self._memory_cache[key]
                removed_count += 1
        
        if removed_count > 0:
            logger.debug(f"Cleaned up {removed_count} expired cache entries")
        
        return removed_count
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics.
        
        Returns:
            Dictionary with cache statistics
        """
        with self._cache_lock:
            cache_size = len(self._memory_cache)
        
        total_requests = self._stats['hits'] + self._stats['misses']
        hit_rate = self._stats['hits'] / total_requests if total_requests > 0 else 0
        
        return {
            'size': cache_size,
            'max_size': self.max_size,
            'hits': self._stats['hits'],
            'misses': self._stats['misses'],
            'hit_rate': hit_rate,
            'sets': self._stats['sets'],
            'deletes': self._stats['deletes'],
            'evictions': self._stats['evictions']
        }
    
    def get_info(self, key: Union[str, tuple, dict]) -> Optional[Dict[str, Any]]:
        """
        Get information about a cache entry.
        
        Args:
            key: Cache key
            
        Returns:
            Entry information or None if not found
        """
        cache_key = self._generate_key(key)
        
        with self._cache_lock:
            if cache_key in self._memory_cache:
                entry = self._memory_cache[cache_key]
                return {
                    'created_at': entry.created_at,
                    'expires_at': entry.expires_at,
                    'access_count': entry.access_count,
                    'last_accessed': entry.last_accessed,
                    'is_expired': entry.is_expired(),
                    'metadata': entry.metadata
                }
        
        return None
    
    def save(self):
        """Save cache to persistent storage."""
        self._save_persistent_cache()
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - save cache."""
        self.save()


def cached(
    ttl: int = 3600,
    key_func: Optional[Callable] = None,
    cache_manager: Optional[CacheManager] = None
):
    """
    Decorator for caching function results.
    
    Args:
        ttl: TTL in seconds
        key_func: Function to generate cache key from arguments
        cache_manager: Cache manager instance (creates default if None)
        
    Usage:
        @cached(ttl=300)
        def expensive_function(arg1, arg2):
            return some_expensive_computation(arg1, arg2)
    """
    if cache_manager is None:
        cache_manager = CacheManager()
    
    def decorator(func):
        def wrapper(*args, **kwargs):
            # Generate cache key
            if key_func:
                cache_key = key_func(*args, **kwargs)
            else:
                cache_key = (func.__name__, args, tuple(sorted(kwargs.items())))
            
            # Try to get from cache
            result = cache_manager.get(cache_key)
            if result is not None:
                return result
            
            # Compute and cache result
            result = func(*args, **kwargs)
            cache_manager.set(cache_key, result, ttl=ttl)
            
            return result
        
        return wrapper
    return decorator


def async_cached(
    ttl: int = 3600,
    key_func: Optional[Callable] = None,
    cache_manager: Optional[CacheManager] = None
):
    """
    Decorator for caching async function results.
    
    Args:
        ttl: TTL in seconds
        key_func: Function to generate cache key from arguments
        cache_manager: Cache manager instance (creates default if None)
        
    Usage:
        @async_cached(ttl=300)
        async def expensive_async_function(arg1, arg2):
            return await some_expensive_async_computation(arg1, arg2)
    """
    if cache_manager is None:
        cache_manager = CacheManager()
    
    def decorator(func):
        async def wrapper(*args, **kwargs):
            # Generate cache key
            if key_func:
                cache_key = key_func(*args, **kwargs)
            else:
                cache_key = (func.__name__, args, tuple(sorted(kwargs.items())))
            
            # Try to get from cache
            result = cache_manager.get(cache_key)
            if result is not None:
                return result
            
            # Compute and cache result
            result = await func(*args, **kwargs)
            cache_manager.set(cache_key, result, ttl=ttl)
            
            return result
        
        return wrapper
    return decorator


# Global cache instance
_global_cache: Optional[CacheManager] = None


def get_global_cache() -> CacheManager:
    """Get the global cache instance."""
    global _global_cache
    if _global_cache is None:
        _global_cache = CacheManager()
    return _global_cache