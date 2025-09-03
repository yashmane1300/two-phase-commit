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

## Getting Started

### Prerequisites
- Python 3.8+
- pip3

### Installation
```bash
git clone <repository-url>
cd two-phase-commit
pip install flask requests pytest
```

### Quick Start (Recommended)
```bash
# Run the complete demo
python3 demo_simple.py
```

This will start the coordinator, participants, and run a test transaction automatically.

### Manual Setup
```bash
# Start coordinator
python3 cmd/coordinator/main.py

# Start participants (in separate terminals)
python3 cmd/participant/simple_participant.py participant1 50051
python3 cmd/participant/simple_participant.py participant2 50052

# Run test client
python3 cmd/client/main.py
```

### Running Tests
```bash
python3 -m pytest tests/ -v
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
├── tests/                        # Unit tests
│   └── test_two_phase_commit.py  # Test cases for coordinator and lock manager
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

## Testing

The project includes comprehensive unit tests:

```bash
# Run all tests
python3 -m pytest tests/ -v

# Run specific test file
python3 -m pytest tests/test_two_phase_commit.py -v
```

## Development

### Adding New Features
1. Add business logic in `src/` directory
2. Add server entry points in `servers/` directory
3. Add tests in `tests/` directory

## Troubleshooting

### Common Issues

**Coordinator won't start:**
- Check if port 50050 is available
- Ensure Python dependencies are installed

**Participants can't connect:**
- Verify coordinator is running on port 50050
- Check participant addresses in coordinator registration

**Transactions failing:**
- Check participant logs for errors
- Verify network connectivity between nodes
- Check timeout settings

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## License

This project is licensed under the MIT License.

