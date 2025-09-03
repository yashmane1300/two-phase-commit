import asyncio
import json
import logging
import threading
import time
import uuid
from dataclasses import dataclass, asdict
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional

from flask import Flask, request, jsonify
import requests

# REST/JSON-based Two-Phase Commit Implementation

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
class Transaction:
    id: str
    status: TransactionStatus
    participants: List[str]
    operations: List[Operation]
    created_at: datetime
    updated_at: datetime

class Coordinator:
    def __init__(self, timeout: float = 30.0):
        self.transactions: Dict[str, Transaction] = {}
        self.participants: Dict[str, str] = {}  # participant_id -> address
        self.timeout = timeout
        self.logger = logging.getLogger(__name__)
        self._lock = threading.RLock()
        
        logging.basicConfig(level=logging.INFO)
    
    def register_participant(self, participant_id: str, address: str) -> None:
        """Register a participant node"""
        with self._lock:
            self.participants[participant_id] = address
            self.logger.info(f"Registered participant {participant_id} at {address}")
    
    def execute_transaction(self, operations: List[Dict], participants: List[str]) -> Dict:
        """Execute a distributed transaction using 2PC protocol"""
        transaction_id = str(uuid.uuid4())
        
        self.logger.info(f"Starting transaction {transaction_id} with {len(participants)} participants")
        
        # Create transaction
        txn = Transaction(
            id=transaction_id,
            status=TransactionStatus.INITIALIZED,
            participants=participants,
            operations=[Operation(**op) for op in operations],
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        with self._lock:
            self.transactions[transaction_id] = txn
        
        # Execute 2PC protocol
        success = self._execute_two_phase_commit(txn)
        
        if success:
            self.logger.info(f"Transaction {transaction_id} completed successfully")
            return {
                "success": True,
                "transaction_id": transaction_id,
                "message": "Transaction committed successfully"
            }
        else:
            self.logger.error(f"Transaction {transaction_id} failed")
            return {
                "success": False,
                "transaction_id": transaction_id,
                "message": "Transaction aborted"
            }
    
    def _execute_two_phase_commit(self, txn: Transaction) -> bool:
        """Execute the two-phase commit protocol"""
        # Phase 1: Prepare
        if not self._prepare_phase(txn):
            self._abort_transaction(txn)
            return False
        
        # Phase 2: Commit
        return self._commit_phase(txn)
    
    def _prepare_phase(self, txn: Transaction) -> bool:
        """Phase 1: Send prepare requests to all participants"""
        self._update_transaction_status(txn, TransactionStatus.PREPARING)
        
        all_prepared = True
        for participant_id in txn.participants:
            try:
                address = self.participants[participant_id]
                
                # First, begin the transaction
                begin_response = requests.post(
                    f"http://{address}/begin",
                    json={"transaction_id": txn.id},
                    timeout=self.timeout
                )
                
                if begin_response.status_code != 200 or not begin_response.json().get("success", False):
                    all_prepared = False
                    self.logger.error(f"Participant {participant_id} failed to begin transaction")
                    continue
                
                # Then prepare
                response = requests.post(
                    f"http://{address}/prepare",
                    json={
                        "transaction_id": txn.id,
                        "operations": [asdict(op) for op in txn.operations]
                    },
                    timeout=self.timeout
                )
                
                if response.status_code != 200 or not response.json().get("prepared", False):
                    all_prepared = False
                    self.logger.error(f"Participant {participant_id} failed to prepare")
                    
            except Exception as e:
                all_prepared = False
                self.logger.error(f"Prepare request failed for participant {participant_id}: {e}")
        
        if all_prepared:
            self._update_transaction_status(txn, TransactionStatus.PREPARED)
            self.logger.info(f"All participants prepared for transaction {txn.id}")
            return True
        else:
            self.logger.error(f"Some participants failed to prepare for transaction {txn.id}")
            return False
    
    def _commit_phase(self, txn: Transaction) -> bool:
        """Phase 2: Send commit requests to all participants"""
        self._update_transaction_status(txn, TransactionStatus.COMMITTING)
        
        all_committed = True
        for participant_id in txn.participants:
            try:
                address = self.participants[participant_id]
                response = requests.post(
                    f"http://{address}/commit",
                    json={"transaction_id": txn.id},
                    timeout=self.timeout
                )
                
                if response.status_code != 200 or not response.json().get("committed", False):
                    all_committed = False
                    self.logger.error(f"Participant {participant_id} failed to commit")
                    
            except Exception as e:
                all_committed = False
                self.logger.error(f"Commit request failed for participant {participant_id}: {e}")
        
        if all_committed:
            self._update_transaction_status(txn, TransactionStatus.COMMITTED)
            self.logger.info(f"All participants committed transaction {txn.id}")
            return True
        else:
            self.logger.error(f"Some participants failed to commit transaction {txn.id}")
            return False
    
    def _abort_transaction(self, txn: Transaction) -> None:
        """Send abort requests to all participants"""
        self._update_transaction_status(txn, TransactionStatus.ABORTING)
        
        for participant_id in txn.participants:
            try:
                address = self.participants[participant_id]
                requests.post(
                    f"http://{address}/abort",
                    json={"transaction_id": txn.id},
                    timeout=self.timeout
                )
            except Exception as e:
                self.logger.error(f"Abort request failed for participant {participant_id}: {e}")
        
        self._update_transaction_status(txn, TransactionStatus.ABORTED)
        self.logger.info(f"Transaction {txn.id} aborted")
    
    def _update_transaction_status(self, txn: Transaction, status: TransactionStatus) -> None:
        """Update the status of a transaction"""
        txn.status = status
        txn.updated_at = datetime.now()
    
    def get_transaction_status(self, transaction_id: str) -> Dict:
        """Get the status of a transaction"""
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
    
    def get_all_transactions(self) -> List[Dict]:
        """Get all transactions"""
        with self._lock:
            transactions = []
            for txn in self.transactions.values():
                transactions.append({
                    "id": txn.id,
                    "status": txn.status.value,
                    "participants": txn.participants,
                    "operations_count": len(txn.operations),
                    "created_at": txn.created_at.isoformat(),
                    "updated_at": txn.updated_at.isoformat()
                })
            return transactions
    
    def get_participants(self) -> List[Dict]:
        """Get all registered participants"""
        with self._lock:
            participants = []
            for participant_id, address in self.participants.items():
                participants.append({
                    "id": participant_id,
                    "address": address
                })
            return participants

# Flask app for coordinator
app = Flask(__name__)
coordinator = Coordinator()

# Register default participants
coordinator.register_participant("participant1", "localhost:50051")
coordinator.register_participant("participant2", "localhost:50052")
coordinator.register_participant("participant3", "localhost:50053")

@app.route('/execute', methods=['POST'])
def execute_transaction():
    """Execute a distributed transaction"""
    data = request.json
    result = coordinator.execute_transaction(
        operations=data.get('operations', []),
        participants=data.get('participants', [])
    )
    return jsonify(result)

@app.route('/status/<transaction_id>', methods=['GET'])
def get_transaction_status(transaction_id):
    """Get transaction status"""
    result = coordinator.get_transaction_status(transaction_id)
    return jsonify(result)

@app.route('/transactions', methods=['GET'])
def get_all_transactions():
    """Get all transactions"""
    transactions = coordinator.get_all_transactions()
    return jsonify(transactions)

@app.route('/participants', methods=['GET'])
def get_participants():
    """Get all participants"""
    participants = coordinator.get_participants()
    return jsonify(participants)

@app.route('/register', methods=['POST'])
def register_participant():
    """Register a new participant"""
    data = request.json
    coordinator.register_participant(
        participant_id=data['participant_id'],
        address=data['address']
    )
    return jsonify({"success": True, "message": "Participant registered"})

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "coordinator": "running",
        "participants_count": len(coordinator.participants),
        "transactions_count": len(coordinator.transactions)
    })

if __name__ == '__main__':
    print("Starting Two-Phase Commit Coordinator on port 50050")
    app.run(host='0.0.0.0', port=50050, debug=True)
