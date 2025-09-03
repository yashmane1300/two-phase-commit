import threading
import time
from dataclasses import dataclass
from typing import Dict, Optional
from datetime import datetime


@dataclass
class Lock:
    """Represents a lock on a resource"""
    resource: str
    transaction_id: str
    acquired_at: datetime
    timeout: float


class LockManager:
    """Manages locks for resources"""
    
    def __init__(self, default_timeout: float = 30.0):
        self.locks: Dict[str, Lock] = {}  # resource -> lock
        self.default_timeout = default_timeout
        self._lock = threading.RLock()
    
    def acquire_lock(self, resource: str, transaction_id: str) -> bool:
        """Try to acquire a lock on a resource"""
        with self._lock:
            # Check if resource is already locked
            if resource in self.locks:
                existing_lock = self.locks[resource]
                
                # Check if lock has timed out
                if time.time() - existing_lock.acquired_at.timestamp() > existing_lock.timeout:
                    # Lock has timed out, we can acquire it
                    self.locks[resource] = Lock(
                        resource=resource,
                        transaction_id=transaction_id,
                        acquired_at=datetime.now(),
                        timeout=self.default_timeout
                    )
                    return True
                
                # Resource is locked by another transaction
                return False
            
            # Resource is available, acquire lock
            self.locks[resource] = Lock(
                resource=resource,
                transaction_id=transaction_id,
                acquired_at=datetime.now(),
                timeout=self.default_timeout
            )
            
            return True
    
    def release_locks(self, transaction_id: str) -> None:
        """Release all locks for a transaction"""
        with self._lock:
            # Find and release all locks for this transaction
            resources_to_remove = []
            for resource, lock in self.locks.items():
                if lock.transaction_id == transaction_id:
                    resources_to_remove.append(resource)
            
            for resource in resources_to_remove:
                del self.locks[resource]
    
    def is_locked(self, resource: str) -> bool:
        """Check if a resource is currently locked"""
        with self._lock:
            if resource not in self.locks:
                return False
            
            lock = self.locks[resource]
            
            # Check if lock has timed out
            if time.time() - lock.acquired_at.timestamp() > lock.timeout:
                return False
            
            return True
    
    def get_lock_owner(self, resource: str) -> Optional[str]:
        """Get the transaction ID that owns the lock on a resource"""
        with self._lock:
            if resource not in self.locks:
                return None
            
            lock = self.locks[resource]
            
            # Check if lock has timed out
            if time.time() - lock.acquired_at.timestamp() > lock.timeout:
                return None
            
            return lock.transaction_id
    
    def cleanup_expired_locks(self) -> None:
        """Remove all expired locks"""
        with self._lock:
            now = datetime.now()
            resources_to_remove = []
            
            for resource, lock in self.locks.items():
                if now.timestamp() - lock.acquired_at.timestamp() > lock.timeout:
                    resources_to_remove.append(resource)
            
            for resource in resources_to_remove:
                del self.locks[resource]
