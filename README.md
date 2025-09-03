# Two-Phase Commit Implementation (Python)

This is an implementation of the Two-Phase Commit (2PC) protocol in Python, demonstrating advanced understanding of distributed systems, concurrency control, and transaction management.

## Overview

This project implements a distributed transaction coordinator that ensures ACID properties across multiple participant nodes using the Two-Phase Commit protocol. It showcases:

- **Distributed Systems Design**: Coordinating transactions across multiple nodes
- **Concurrency Control**: Handling concurrent transactions and deadlock prevention
- **Fault Tolerance**: Managing node failures and network partitions
- **Consistency Guarantees**: Ensuring data consistency in distributed environments
- **REST API Design**: Modern HTTP/JSON APIs for inter-node communication

## Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Coordinator   │    │   Participant   │    │   Participant   │
│                 │    │       A         │    │       B         │
│  - Transaction  │◄──►│  - Resource     │    │  - Resource     │
│    Manager      │    │    Manager      │    │    Manager      │
│  - State        │    │  - Lock Manager │    │  - Lock Manager │
│    Machine      │    │  - Recovery     │    │  - Recovery     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## Features

- **Phase 1 - Prepare**: Coordinator sends prepare requests to all participants
- **Phase 2 - Commit/Abort**: Coordinator decides final outcome based on participant responses
- **Timeout Handling**: Automatic abort on timeout to prevent indefinite blocking
- **Recovery Mechanism**: State persistence and recovery after failures
- **Concurrent Transaction Support**: Multiple transactions with proper isolation
- **Deadlock Detection**: Prevention and resolution of deadlock scenarios
- **REST APIs**: HTTP/JSON communication between nodes

## Technology Stack

- **Language**: Python 3.8
- **Protocol**: HTTP/JSON REST APIs for inter-node communication
- **Web Framework**: Flask for HTTP servers
- **Testing**: pytest for unit testing
- **Monitoring**: Structured logging with timestamps

## Getting Started

### Prerequisites
- Python 3.8+
- pip3

### Installation
```bash
git clone <repository-url>
cd two-phase-commit
./run.sh install-deps
```

### Running the Demo
```bash
# Start coordinator
./run.sh run-coordinator

# Start participants (in separate terminals)
./run.sh run-participant participant1 50051
./run.sh run-participant participant2 50052

# Run test client
./run.sh run-client
```

### Running Complete Demo
```bash
# Run the entire demo (coordinator + participants + client)
./run.sh run-demo
```

### Running Tests
```bash
./run.sh run-tests
```

## API Documentation

### Coordinator REST API (Port 50050)
- `POST /execute` - Execute a distributed transaction
- `GET /status/{id}` - Get transaction status
- `GET /transactions` - List all transactions
- `GET /participants` - List participants
- `GET /health` - Health check
- `POST /register` - Register participant

### Participant REST API (Ports 50051, 50052, etc.)
- `POST /begin` - Start a new local transaction
- `POST /prepare` - Prepare local resources for commit
- `POST /commit` - Commit local changes
- `POST /abort` - Rollback local changes
- `GET /status/{id}` - Get current transaction status
- `GET /resource/{key}` - Get resource value

## Project Structure

```
two-phase-commit/
├── internal/                    # Core business logic
│   ├── coordinator/            # Coordinator implementation
│   └── participant/            # Participant implementation
├── cmd/                        # Executable entry points
│   ├── coordinator/           # Coordinator server
│   ├── participant/           # Participant servers
│   └── client/                # Test client
├── pkg/                        # Shared utilities
│   └── lock/                  # Lock management
├── tests/                      # Unit tests
├── requirements-simple.txt     # Dependencies
├── run.sh                      # Build/run script
└── demo_simple.py             # Demo script
```

## Key Components

### Coordinator (`internal/coordinator/coordinator.py`)
- **Purpose**: Orchestrates the 2PC protocol
- **Key Functions**:
  - `execute_transaction()`: Main entry point
  - `_prepare_phase()`: Phase 1 - ask participants to prepare
  - `_commit_phase()`: Phase 2 - tell participants to commit
  - `_abort_transaction()`: Tell participants to abort

### Participant (`cmd/participant/simple_participant.py`)
- **Purpose**: Handles local data and participates in 2PC
- **Key Functions**:
  - `begin_transaction()`: Start local transaction
  - `prepare()`: Acquire locks and validate operations
  - `commit()`: Apply operations and release locks
  - `abort()`: Release locks without applying changes

### Lock Manager (`pkg/lock/manager.py`)
- **Purpose**: Prevents conflicts between transactions
- **Key Functions**:
  - `acquire_lock()`: Try to acquire lock on resource
  - `release_locks()`: Release all locks for transaction
  - `is_locked()`: Check if resource is locked

## Testing

The project includes comprehensive unit tests:

```bash
# Run all tests
./run.sh run-tests

# Run specific test file
python3 -m pytest tests/test_two_phase_commit.py -v
```

