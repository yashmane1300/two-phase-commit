#!/usr/bin/env python3

import json
import logging
import threading
import time
from dataclasses import dataclass, asdict
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional
from flask import Flask, request, jsonify

# Simple HTTP-based Participant Implementation

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
    type: OperationType = OperationType.READ

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
    
    def acquire_lock(self, transaction_id: str, resource: str) -> bool:
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

class Participant:
    def __init__(self, participant_id: str, timeout: float = 30.0):
        self.id = participant_id
        self.transactions: Dict[str, LocalTransaction] = {}
        self.resources: Dict[str, str] = {}
        self.lock_manager = LockManager()
        self.timeout = timeout
        self.logger = logging.getLogger(__name__)
        self._lock = threading.RLock()
        
        logging.basicConfig(level=logging.INFO)
    
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
                "participant_id": self.id
            }
        
        # Update transaction with operations
        txn.operations = [Operation(**op) for op in operations]
        txn.status = TransactionStatus.PREPARING
        txn.updated_at = datetime.now()
        
        # Try to acquire locks for all operations
        if not self._acquire_locks(transaction_id, txn.operations):
            self._update_transaction_status(txn, TransactionStatus.ABORTED)
            return {
                "prepared": False,
                "message": f"Failed to acquire locks for transaction {transaction_id}",
                "participant_id": self.id
            }
        
        # Validate operations
        if not self._validate_operations(txn.operations):
            self._release_locks(transaction_id)
            self._update_transaction_status(txn, TransactionStatus.ABORTED)
            return {
                "prepared": False,
                "message": f"Validation failed for transaction {transaction_id}",
                "participant_id": self.id
            }
        
        # Mark as prepared
        self._update_transaction_status(txn, TransactionStatus.PREPARED)
        self.logger.info(f"Prepared transaction {transaction_id}")
        
        return {
            "prepared": True,
            "message": f"Transaction {transaction_id} prepared successfully",
            "participant_id": self.id
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
        
        # Apply operations to local resources
        if not self._apply_operations(txn.operations):
            self._release_locks(transaction_id)
            self._update_transaction_status(txn, TransactionStatus.ABORTED)
            return {
                "committed": False,
                "message": f"Failed to apply operations for transaction {transaction_id}"
            }
        
        # Release locks
        self._release_locks(transaction_id)
        
        # Mark as committed
        self._update_transaction_status(txn, TransactionStatus.COMMITTED)
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
        
        # Mark as aborted
        self._update_transaction_status(txn, TransactionStatus.ABORTED)
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
        for operation in operations:
            if not self.lock_manager.acquire_lock(transaction_id, operation.key):
                self._release_locks(transaction_id)
                return False
        return True
    
    def _release_locks(self, transaction_id: str) -> None:
        self.lock_manager.release_locks(transaction_id)
    
    def _validate_operations(self, operations: List[Operation]) -> bool:
        for operation in operations:
            if operation.type == OperationType.READ:
                if operation.key not in self.resources:
                    self.logger.warning(f"Read operation failed: key {operation.key} does not exist")
                    return False
            elif operation.type == OperationType.WRITE:
                pass  # Write operations are always valid
            elif operation.type == OperationType.DELETE:
                if operation.key not in self.resources:
                    self.logger.warning(f"Delete operation failed: key {operation.key} does not exist")
                    return False
        return True
    
    def _apply_operations(self, operations: List[Operation]) -> bool:
        try:
            for operation in operations:
                if operation.type == OperationType.READ:
                    pass  # Read operations don't modify state
                elif operation.type == OperationType.WRITE:
                    self.resources[operation.key] = operation.value
                elif operation.type == OperationType.DELETE:
                    del self.resources[operation.key]
            return True
        except Exception as e:
            self.logger.error(f"Failed to apply operations: {e}")
            return False
    
    def _update_transaction_status(self, txn: LocalTransaction, status: TransactionStatus) -> None:
        txn.status = status
        txn.updated_at = datetime.now()
    
    def set_resource(self, key: str, value: str) -> None:
        with self._lock:
            self.resources[key] = value
    
    def get_resource(self, key: str) -> Optional[str]:
        with self._lock:
            return self.resources.get(key)

# Flask app for participant
app = Flask(__name__)
participant = None

@app.route('/begin', methods=['POST'])
def begin_transaction():
    data = request.json
    result = participant.begin_transaction(data['transaction_id'])
    return jsonify(result)

@app.route('/prepare', methods=['POST'])
def prepare():
    data = request.json
    result = participant.prepare(
        transaction_id=data['transaction_id'],
        operations=data['operations']
    )
    return jsonify(result)

@app.route('/commit', methods=['POST'])
def commit():
    data = request.json
    result = participant.commit(data['transaction_id'])
    return jsonify(result)

@app.route('/abort', methods=['POST'])
def abort():
    data = request.json
    result = participant.abort(data['transaction_id'])
    return jsonify(result)

@app.route('/status/<transaction_id>', methods=['GET'])
def get_status(transaction_id):
    result = participant.get_status(transaction_id)
    return jsonify(result)

@app.route('/resource/<key>', methods=['GET'])
def get_resource(key):
    value = participant.get_resource(key)
    return jsonify({"key": key, "value": value})

if __name__ == '__main__':
    import sys
    
    if len(sys.argv) < 3:
        print("Usage: python simple_participant.py <participant_id> <port>")
        sys.exit(1)
    
    participant_id = sys.argv[1]
    port = int(sys.argv[2])
    
    participant = Participant(participant_id)
    
    # Initialize some test data
    participant.set_resource("key1", "value1")
    participant.set_resource("key2", "value2")
    participant.set_resource("key3", "value3")
    
    print(f"Starting Two-Phase Commit Participant {participant_id} on port {port}")
    app.run(host='0.0.0.0', port=port, debug=True)

