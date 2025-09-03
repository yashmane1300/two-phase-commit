import pytest
import asyncio
from unittest.mock import Mock, AsyncMock
from datetime import datetime

# Import our modules
from src.coordinator.coordinator import Coordinator, Transaction, TransactionStatus
from src.core.manager import LockManager


class TestCoordinator:
    """Test cases for the Coordinator class"""
    
    def test_new_coordinator(self):
        """Test creating a new coordinator"""
        timeout = 30.0
        coordinator = Coordinator(timeout=timeout)
        
        assert coordinator.timeout == timeout
        assert coordinator.transactions == {}
        assert coordinator.participants == {}
    
    def test_register_participant(self):
        """Test registering a participant"""
        coordinator = Coordinator()
        coordinator.register_participant("test1", "localhost:50051")
        coordinator.register_participant("test2", "localhost:50052")
        
        assert coordinator.participants["test1"] == "localhost:50051"
        assert coordinator.participants["test2"] == "localhost:50052"
    
    def test_update_transaction_status(self):
        """Test updating transaction status"""
        coordinator = Coordinator()
        txn = Transaction(
            id="test-txn",
            status=TransactionStatus.INITIALIZED,
            participants=[],
            operations=[],
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        coordinator._update_transaction_status(txn, TransactionStatus.PREPARING)
        assert txn.status == TransactionStatus.PREPARING
        
        coordinator._update_transaction_status(txn, TransactionStatus.COMMITTED)
        assert txn.status == TransactionStatus.COMMITTED
    
    def test_execute_transaction(self):
        """Test executing a transaction"""
        coordinator = Coordinator()
        coordinator.register_participant("test1", "localhost:50051")
        
        operations = [
            {"key": "key1", "value": "value1", "type": "WRITE"}
        ]
        participants = ["test1"]
        
        # Mock the HTTP requests to avoid actual network calls
        with pytest.MonkeyPatch().context() as m:
            m.setattr('requests.post', Mock(return_value=Mock(
                status_code=200,
                json=Mock(return_value={"success": True, "prepared": True, "committed": True})
            )))
            
            result = coordinator.execute_transaction(operations, participants)
            
            assert result["success"] is True
            assert "transaction_id" in result


class TestLockManager:
    """Test cases for the LockManager class"""
    
    def test_new_lock_manager(self):
        """Test creating a new lock manager"""
        lock_manager = LockManager()
        
        assert lock_manager.locks == {}
    
    def test_acquire_lock(self):
        """Test acquiring a lock"""
        lock_manager = LockManager()
        
        # Should be able to acquire lock on free resource
        assert lock_manager.acquire_lock("resource1", "txn1") is True
        assert lock_manager.is_locked("resource1") is True
        
        # Should not be able to acquire lock on locked resource
        assert lock_manager.acquire_lock("resource1", "txn2") is False
    
    def test_release_locks(self):
        """Test releasing locks"""
        lock_manager = LockManager()
        
        # Acquire locks
        lock_manager.acquire_lock("resource1", "txn1")
        lock_manager.acquire_lock("resource2", "txn1")
        
        # Release all locks for transaction
        lock_manager.release_locks("txn1")
        
        assert lock_manager.is_locked("resource1") is False
        assert lock_manager.is_locked("resource2") is False
    
    def test_get_lock_owner(self):
        """Test getting lock owner"""
        lock_manager = LockManager()
        
        lock_manager.acquire_lock("resource1", "txn1")
        
        assert lock_manager.get_lock_owner("resource1") == "txn1"
        assert lock_manager.get_lock_owner("nonexistent") is None


if __name__ == "__main__":
    pytest.main([__file__])
