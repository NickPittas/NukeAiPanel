"""
Event Loop Manager

Provides a singleton event loop manager that maintains a persistent event loop
across multiple chat interactions, preventing "Event loop is closed" errors.
"""

import asyncio
import threading
import logging
import time
import weakref
from typing import Optional, Dict, Any, Set

from ..utils.logger import get_logger

logger = get_logger(__name__)


class EventLoopManager:
    """
    Singleton event loop manager that maintains a persistent event loop
    across multiple chat interactions.
    
    This class ensures that the event loop is properly managed and not closed
    prematurely between chat messages, preventing "Event loop is closed" errors.
    """
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(EventLoopManager, cls).__new__(cls)
                cls._instance._initialized = False
            return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
            
        self._initialized = True
        self._loop = None
        self._thread = None
        self._running = False
        self._tasks = set()
        self._loop_lock = threading.Lock()
        self._sessions = weakref.WeakSet()  # Track client sessions without creating reference cycles
        self._active_sessions = {}  # Track active sessions with their creation time
        self._session_cleanup_interval = 60  # Seconds between session cleanup checks
        self._last_cleanup_time = time.time()
        
        # Initialize the event loop
        self._initialize_loop()
    
    def _initialize_loop(self):
        """Initialize the event loop in a background thread."""
        with self._loop_lock:
            if self._running:
                return
                
            try:
                self._thread = threading.Thread(target=self._run_event_loop, daemon=True)
                self._thread.start()
                self._running = True
                logger.info("Event loop manager initialized with background thread")
                
                # Wait for the loop to be created
                timeout = 5  # seconds
                start_time = time.time()
                while self._loop is None:
                    time.sleep(0.1)
                    if time.time() - start_time > timeout:
                        raise TimeoutError("Timed out waiting for event loop to initialize")
                
                logger.info(f"Event loop initialized: {self._loop}")
            except Exception as e:
                logger.error(f"Failed to initialize event loop: {e}")
                raise
    
    def _run_event_loop(self):
        """Run the event loop in a background thread."""
        try:
            # Create a new event loop for this thread
            self._loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self._loop)
            
            logger.info("Event loop started in background thread")
            
            # Run the event loop forever
            self._loop.run_forever()
            
        except Exception as e:
            logger.error(f"Event loop error: {e}")
        finally:
            # Clean up when the loop stops
            try:
                if self._loop and not self._loop.is_closed():
                    # Cancel all pending tasks
                    pending = asyncio.all_tasks(self._loop)
                    for task in pending:
                        task.cancel()
                    
                    # Run the event loop until all tasks are cancelled
                    if pending:
                        self._loop.run_until_complete(asyncio.gather(*pending, return_exceptions=True))
                    
                    # Close the event loop
                    self._loop.close()
                    
                logger.info("Event loop closed")
            except Exception as e:
                logger.error(f"Error during event loop cleanup: {e}")
            
            self._loop = None
            self._running = False
    
    def get_loop(self) -> Optional[asyncio.AbstractEventLoop]:
        """
        Get the current event loop.
        
        Returns:
            The current event loop or None if not available
        """
        # Ensure the loop is running
        if not self._running or not self._thread or not self._thread.is_alive():
            self._initialize_loop()
            
        return self._loop
    
    def run_coroutine(self, coro, timeout=None):
        """
        Run a coroutine in the managed event loop.
        
        Args:
            coro: The coroutine to run
            timeout: Optional timeout in seconds
            
        Returns:
            The result of the coroutine
            
        Raises:
            Exception: If the coroutine execution fails
        """
        if not self._running:
            self._initialize_loop()
            
        if not self._loop:
            raise RuntimeError("Event loop is not available")
            
        # Create a future to get the result
        future = asyncio.run_coroutine_threadsafe(coro, self._loop)
        
        try:
            # Wait for the result with optional timeout
            return future.result(timeout)
        except Exception as e:
            logger.error(f"Error running coroutine: {e}")
            future.cancel()
            raise
    
    def create_task(self, coro):
        """
        Create a task in the managed event loop.
        
        Args:
            coro: The coroutine to create a task for
            
        Returns:
            The created task
        """
        if not self._running:
            self._initialize_loop()
            
        if not self._loop:
            raise RuntimeError("Event loop is not available")
            
        # Create the task
        task = asyncio.run_coroutine_threadsafe(coro, self._loop)
        self._tasks.add(task)
        
        # Set up callback to remove the task when done
        def _on_task_done(task):
            self._tasks.discard(task)
        
        task.add_done_callback(_on_task_done)
        return task
    
    def shutdown(self):
        """Shutdown the event loop manager."""
        with self._loop_lock:
            if not self._running:
                return
                
            logger.info("Shutting down event loop manager")
            
            try:
                # Clean up all tracked sessions first
                self.cleanup_sessions()
                
                # Stop the event loop
                if self._loop and not self._loop.is_closed():
                    # Cancel all pending tasks
                    for task in self._tasks:
                        task.cancel()
                    
                    # Schedule the loop to stop
                    self._loop.call_soon_threadsafe(self._loop.stop)
                    
                # Wait for the thread to finish
                if self._thread and self._thread.is_alive():
                    self._thread.join(timeout=5)
                    
                self._running = False
                self._loop = None
                self._thread = None
                self._tasks.clear()
                
                logger.info("Event loop manager shutdown complete")
                
            except Exception as e:
                logger.error(f"Error during event loop manager shutdown: {e}")


    def register_session(self, session):
        """
        Register a client session for tracking and proper cleanup.
        
        Args:
            session: The client session to track
        """
        self._sessions.add(session)
        session_id = id(session)
        self._active_sessions[session_id] = {
            'session': session,
            'created_at': time.time(),
            'provider': getattr(session, '_provider_name', 'unknown'),
            'closed': False
        }
        logger.debug(f"Registered session: {session_id}, provider: {self._active_sessions[session_id]['provider']}, total sessions: {len(self._sessions)}")
        
        # Perform periodic cleanup
        self._check_periodic_cleanup()
    
    def _check_periodic_cleanup(self):
        """Check if it's time to perform periodic session cleanup."""
        current_time = time.time()
        if current_time - self._last_cleanup_time > self._session_cleanup_interval:
            self._last_cleanup_time = current_time
            
            # Create a task to perform cleanup
            if self._loop and not self._loop.is_closed():
                self._loop.create_task(self._cleanup_stale_sessions())
    
    async def _cleanup_stale_sessions(self):
        """Clean up sessions that have been open for too long."""
        current_time = time.time()
        stale_threshold = 300  # 5 minutes
        
        stale_sessions = []
        for session_id, info in list(self._active_sessions.items()):
            session = info['session']
            age = current_time - info['created_at']
            
            # Check if session is stale
            if age > stale_threshold and not getattr(session, 'closed', True):
                stale_sessions.append((session_id, session, info['provider'], age))
        
        if stale_sessions:
            logger.warning(f"Found {len(stale_sessions)} stale sessions to clean up")
            for session_id, session, provider, age in stale_sessions:
                try:
                    if not getattr(session, 'closed', True):
                        logger.info(f"Closing stale session {session_id} from provider '{provider}' (age: {age:.1f}s)")
                        await session.close()
                        self._active_sessions[session_id]['closed'] = True
                except Exception as e:
                    logger.error(f"Error closing stale session {session_id}: {e}")
    
    def cleanup_sessions(self):
        """Clean up all tracked sessions."""
        logger.info(f"Cleaning up {len(self._sessions)} tracked sessions")
        
        closed_count = 0
        error_count = 0
        
        for session in list(self._sessions):
            try:
                if hasattr(session, 'closed') and not session.closed:
                    # Create a task to close the session
                    if self._loop and not self._loop.is_closed():
                        self._loop.create_task(session.close())
                        closed_count += 1
                        logger.debug(f"Created task to close session: {id(session)}")
            except Exception as e:
                error_count += 1
                logger.error(f"Error closing session: {e}")
        
        # Update active sessions tracking
        for session_id in list(self._active_sessions.keys()):
            self._active_sessions[session_id]['closed'] = True
        
        logger.info(f"Session cleanup: {closed_count} sessions closed, {error_count} errors")
        
        # Clear the sessions set
        self._sessions.clear()
        self._active_sessions.clear()

# Global instance for easy access
_event_loop_manager = None

def get_event_loop_manager() -> EventLoopManager:
    """
    Get the global event loop manager instance.
    
    Returns:
        The global event loop manager instance
    """
    global _event_loop_manager
    if _event_loop_manager is None:
        _event_loop_manager = EventLoopManager()
    return _event_loop_manager

def run_coroutine(coro, timeout=None):
    """
    Run a coroutine using the global event loop manager.
    
    Args:
        coro: The coroutine to run
        timeout: Optional timeout in seconds
        
    Returns:
        The result of the coroutine
    """
    return get_event_loop_manager().run_coroutine(coro, timeout)

def create_task(coro):
    """
    Create a task using the global event loop manager.
    
    Args:
        coro: The coroutine to create a task for
        
    Returns:
        The created task
    """
    return get_event_loop_manager().create_task(coro)

def get_event_loop():
    """
    Get the current event loop from the global event loop manager.
    
    Returns:
        The current event loop
    """
    return get_event_loop_manager().get_loop()

def register_session(session, provider_name=None):
    """
    Register a session with the global event loop manager.
    
    Args:
        session: The session to register
        provider_name: Optional provider name for better tracking
    """
    if provider_name and hasattr(session, '_provider_name'):
        session._provider_name = provider_name
    get_event_loop_manager().register_session(session)

def shutdown_event_loop():
    """Shutdown the global event loop manager."""
    global _event_loop_manager
    if _event_loop_manager is not None:
        _event_loop_manager.shutdown()
        _event_loop_manager = None