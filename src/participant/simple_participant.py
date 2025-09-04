#!/usr/bin/env python3

import json
import logging
import os
import sqlite3
import threading
import time
from dataclasses import dataclass, asdict
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional
from flask import Flask, request, jsonify

# SQLite-based Participant Implementation

class TransactionStatus(Enum):
    INITIALIZED = "INITIALIZED"
    PREPARING = "PREPARING"
    PREPARED = "PREPARED"
    COMMITTING = "COMMITTING"
    COMMITTED = "COMMITTED"
    ABORTING = "ABORTING"
    ABORTED = "ABORTED"
    TIMEOUT = "TIMEOUT"

class OperationType(Enum):
    READ = "READ"
    WRITE = "WRITE"
    DELETE = "DELETE"

@dataclass
class Operation:
    key: str
    value: Optional[str] = None
    type: str = "READ"  # Change to string to match JSON input

@dataclass
class LocalTransaction:
    id: str
    status: TransactionStatus
    operations: List[Operation]
    created_at: datetime
    updated_at: datetime

class LockManager:
    def __init__(self, default_timeout: float = 30.0):
        self.locks: Dict[str, Dict] = {}
        self.default_timeout = default_timeout
        self._lock = threading.RLock()
    
    def acquire_lock(self, resource: str, transaction_id: str) -> bool:
        with self._lock:
            if resource in self.locks:
                existing_lock = self.locks[resource]
                if time.time() - existing_lock['acquired_at'] > existing_lock['timeout']:
                    self.locks[resource] = {
                        'transaction_id': transaction_id,
                        'acquired_at': time.time(),
                        'timeout': self.default_timeout
                    }
                    return True
                return False
            
            self.locks[resource] = {
                'transaction_id': transaction_id,
                'acquired_at': time.time(),
                'timeout': self.default_timeout
            }
            return True
    
    def release_locks(self, transaction_id: str) -> None:
        with self._lock:
            resources_to_remove = []
            for resource, lock in self.locks.items():
                if lock['transaction_id'] == transaction_id:
                    resources_to_remove.append(resource)
            
            for resource in resources_to_remove:
                del self.locks[resource]

class SQLiteParticipant:
    def __init__(self, participant_id: str, db_path: str = None, timeout: float = 30.0):
        self.id = participant_id
        self.transactions: Dict[str, LocalTransaction] = {}
        self.lock_manager = LockManager()
        self.timeout = timeout
        self.logger = logging.getLogger(__name__)
        self._lock = threading.RLock()
        
        # Set up database path
        if db_path is None:
            db_path = f"participant_{participant_id}.db"
        self.db_path = db_path
        
        # Initialize database
        self._init_database()
        
        logging.basicConfig(level=logging.INFO)
    
    def _init_database(self):
        """Initialize SQLite database with tables"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Create resources table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS resources (
                    key TEXT PRIMARY KEY,
                    value TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Create transactions table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS transactions (
                    id TEXT PRIMARY KEY,
                    status TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Insert some initial data
            cursor.execute('''
                INSERT OR IGNORE INTO resources (key, value) VALUES 
                ('key1', 'value1'),
                ('key2', 'value2'),
                ('key3', 'value3')
            ''')
            
            conn.commit()
            self.logger.info(f"Database initialized: {self.db_path}")
    
    def _get_resource(self, key: str) -> Optional[str]:
        """Get a resource value from SQLite"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT value FROM resources WHERE key = ?', (key,))
            result = cursor.fetchone()
            return result[0] if result else None
    
    def _set_resource(self, key: str, value: str) -> bool:
        """Set a resource value in SQLite"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT OR REPLACE INTO resources (key, value, updated_at) 
                    VALUES (?, ?, CURRENT_TIMESTAMP)
                ''', (key, value))
                conn.commit()
                return True
        except Exception as e:
            self.logger.error(f"Failed to set resource {key}: {e}")
            return False
    
    def _delete_resource(self, key: str) -> bool:
        """Delete a resource from SQLite"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('DELETE FROM resources WHERE key = ?', (key,))
                conn.commit()
                return True
        except Exception as e:
            self.logger.error(f"Failed to delete resource {key}: {e}")
            return False
    
    def begin_transaction(self, transaction_id: str) -> Dict:
        with self._lock:
            if transaction_id in self.transactions:
                return {
                    "success": False,
                    "message": f"Transaction {transaction_id} already exists"
                }
            
            txn = LocalTransaction(
                id=transaction_id,
                status=TransactionStatus.INITIALIZED,
                operations=[],
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
            
            self.transactions[transaction_id] = txn
            self.logger.info(f"Started local transaction {transaction_id}")
            
            return {
                "success": True,
                "message": f"Transaction {transaction_id} started successfully"
            }
    
    def prepare(self, transaction_id: str, operations: List[Dict]) -> Dict:
        with self._lock:
            txn = self.transactions.get(transaction_id)
            if not txn:
                return {
                    "prepared": False,
                    "message": f"Transaction {transaction_id} not found",
                }
            
            # Update transaction with operations
            txn.operations = [Operation(**op) for op in operations]
            txn.status = TransactionStatus.PREPARING
            
            # Try to acquire locks for all operations
            if not self._acquire_locks(transaction_id, txn.operations):
                self._release_locks(transaction_id)
                return {
                    "prepared": False,
                    "message": f"Failed to acquire locks for transaction {transaction_id}",
                }
            
            # Validate operations
            if not self._validate_operations(txn.operations):
                self._release_locks(transaction_id)
                return {
                    "prepared": False,
                    "message": f"Validation failed for transaction {transaction_id}",
                }
            
            txn.status = TransactionStatus.PREPARED
            self.logger.info(f"Prepared transaction {transaction_id}")
            
            return {
                "prepared": True,
                "message": f"Transaction {transaction_id} prepared successfully",
            }
    
    def commit(self, transaction_id: str) -> Dict:
        with self._lock:
            txn = self.transactions.get(transaction_id)
            if not txn:
                return {
                    "committed": False,
                    "message": f"Transaction {transaction_id} not found"
                }
            
            if txn.status != TransactionStatus.PREPARED:
                return {
                    "committed": False,
                    "message": f"Transaction {transaction_id} is not prepared (status: {txn.status})"
                }
            
            # Apply operations to database
            if not self._apply_operations(txn.operations):
                self._release_locks(transaction_id)
                return {
                    "committed": False,
                    "message": f"Failed to apply operations for transaction {transaction_id}"
                }
            
            # Release locks
            self._release_locks(transaction_id)
            
            txn.status = TransactionStatus.COMMITTED
            self.logger.info(f"Committed transaction {transaction_id}")
            
            return {
                "committed": True,
                "message": f"Transaction {transaction_id} committed successfully"
            }
    
    def abort(self, transaction_id: str) -> Dict:
        with self._lock:
            txn = self.transactions.get(transaction_id)
            if not txn:
                return {
                    "aborted": False,
                    "message": f"Transaction {transaction_id} not found"
                }
            
            # Release locks
            self._release_locks(transaction_id)
            
            txn.status = TransactionStatus.ABORTED
            self.logger.info(f"Aborted transaction {transaction_id}")
            
            return {
                "aborted": True,
                "message": f"Transaction {transaction_id} aborted successfully"
            }
    
    def get_status(self, transaction_id: str) -> Dict:
        with self._lock:
            txn = self.transactions.get(transaction_id)
            if not txn:
                return {
                    "status": TransactionStatus.ABORTED.value,
                    "message": f"Transaction {transaction_id} not found"
                }
            
            return {
                "status": txn.status.value,
                "message": f"Transaction {transaction_id} status: {txn.status.value}"
            }
    
    def _acquire_locks(self, transaction_id: str, operations: List[Operation]) -> bool:
        """Acquire locks for all operations"""
        for operation in operations:
            if not self.lock_manager.acquire_lock(operation.key, transaction_id):
                return False
        return True
    
    def _release_locks(self, transaction_id: str) -> None:
        """Release all locks for a transaction"""
        self.lock_manager.release_locks(transaction_id)
    
    def _validate_operations(self, operations: List[Operation]) -> bool:
        """Validate that operations can be performed"""
        for operation in operations:
            if operation.type == "READ":
                # Check if resource exists
                if self._get_resource(operation.key) is None:
                    return False
        return True
    
    def _apply_operations(self, operations: List[Operation]) -> bool:
        """Apply operations to the database"""
        for operation in operations:
            if operation.type == "READ":
                # Read operations don't modify data
                continue
            elif operation.type == "WRITE":
                if not self._set_resource(operation.key, operation.value):
                    return False
            elif operation.type == "DELETE":
                if not self._delete_resource(operation.key):
                    return False
        return True
    
    def get_resource(self, key: str) -> Dict:
        """Get a resource value from the database"""
        value = self._get_resource(key)
        return {
            "key": key,
            "value": value,
            "exists": value is not None
        }

