# Two-Phase Commit Implementation (Python)

A robust implementation of the Two-Phase Commit (2PC) protocol in Python, demonstrating advanced understanding of distributed systems, concurrency control, and transaction management.

## Overview

This project implements a distributed transaction coordinator that ensures ACID properties across multiple participant nodes using the Two-Phase Commit protocol. It showcases:

- **Distributed Systems Design**: Coordinating transactions across multiple nodes
- **Concurrency Control**: Handling concurrent transactions and deadlock prevention
- **Fault Tolerance**: Managing node failures and network partitions
- **Consistency Guarantees**: Ensuring data consistency in distributed environments
- **REST API Design**: Modern HTTP/JSON APIs for inter-node communication
- **Database Integration**: Each participant uses its own SQLite database for data persistence

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

- **Language**: Python 3.8+
- **Protocol**: HTTP/JSON REST APIs for inter-node communication
- **Web Framework**: Flask for HTTP servers
- **Database**: SQLite for data persistence
- **Testing**: pytest for unit testing
- **Monitoring**: Structured logging with timestamps

## Quick Start

### Prerequisites
- Python 3.8+
- pip3

### Installation
```bash
git clone <repository-url>
cd two-phase-commit
pip install flask requests pytest
```

### Run the Demo (Recommended)
```bash
# Run the complete demo - this starts everything automatically
python demo.py
```

This will:
- Start the coordinator server on port 50050
- Start participant servers on ports 50051 and 50052
- Execute a test transaction
- Show the results
- Clean up all services

## Testing

### Unit Tests
```bash
# Run all unit tests
python -m pytest tests/test_two_phase_commit.py -v
```

### Integration Tests
```bash
# Run basic integration tests
python tests/simple_test.py

# Run comprehensive scenario tests
python tests/test_scenarios.py
```

### Manual Testing
```bash
# Start coordinator
python servers/coordinator_server.py

# Start participants (in separate terminals)
python servers/participant_server.py participant1 50051
python servers/participant_server.py participant2 50052

# Run test client
python servers/client.py
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
├── src/                          # Main source code
│   ├── coordinator/              # Coordinator implementation
│   │   └── coordinator.py        # Core coordinator logic with Flask app
│   ├── participant/              # Participant implementation
│   │   ├── simple_participant.py # SQLite-based participant logic
│   │   └── app.py               # Flask app for participant
│   └── core/                     # Shared utilities
│       └── manager.py            # Lock manager for concurrency control
├── servers/                      # Server entry points
│   ├── coordinator_server.py     # Coordinator server
│   ├── participant_server.py     # Participant server
│   └── client.py                # Test client
├── tests/                        # All tests
│   ├── test_two_phase_commit.py  # Unit tests for coordinator and lock manager
│   ├── simple_test.py            # Basic integration tests
│   └── test_scenarios.py         # Comprehensive scenario tests
├── demo.py                       # End-to-end demo script
└── requirements-simple.txt       # Python dependencies
```

## Key Components

### Coordinator (`src/coordinator/coordinator.py`)
- **Purpose**: Orchestrates the 2PC protocol
- **Key Functions**:
  - `execute_transaction()`: Main entry point
  - `_prepare_phase()`: Phase 1 - ask participants to prepare
  - `_commit_phase()`: Phase 2 - tell participants to commit
  - `_abort_transaction()`: Tell participants to abort

### Participant (`src/participant/simple_participant.py`)
- **Purpose**: Handles local data and participates in 2PC
- **Database**: Uses SQLite database for data persistence
- **Key Functions**:
  - `begin_transaction()`: Start local transaction
  - `prepare()`: Acquire locks and validate operations
  - `commit()`: Apply operations to SQLite database and release locks
  - `abort()`: Release locks without applying changes
  - `_get_resource()`: Read from SQLite database
  - `_set_resource()`: Write to SQLite database

### Lock Manager (`src/core/manager.py`)
- **Purpose**: Prevents conflicts between transactions
- **Key Functions**:
  - `acquire_lock()`: Try to acquire lock on resource
  - `release_locks()`: Release all locks for transaction
  - `is_locked()`: Check if resource is locked

## Troubleshooting

### Common Issues

**Port already in use:**
```bash
# Kill existing processes
python -c "import subprocess; subprocess.run(['pkill', '-f', 'python'])"

# Or use different ports
python servers/coordinator_server.py --port 50060
```

**Shell command issues:**
```bash
# Use Python for file operations
python -c "import os; print(os.listdir('.'))"

# Check running processes
python -c "import subprocess; result = subprocess.run(['ps', 'aux'], capture_output=True, text=True); print(result.stdout)"
```

**Virtual Environment (Optional):**
```bash
# Create virtual environment
python -m venv venv

# Activate (macOS/Linux)
source venv/bin/activate

# Install dependencies
pip install flask requests pytest

# Run demo
python demo.py
```

### Health Checks

```bash
# Check coordinator health
curl http://localhost:50050/health

# Check participant resources
curl http://localhost:50051/resource/key1
```

## Development

### Adding New Features
1. Add business logic in `src/` directory
2. Add server entry points in `servers/` directory
3. Add tests in `tests/` directory

### Running Tests
```bash
# All unit tests
python -m pytest tests/test_two_phase_commit.py -v

# Integration tests
python tests/simple_test.py
python tests/test_scenarios.py
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## License

This project is licensed under the MIT License.

