#!/bin/bash

# Two-Phase Commit Python Project - REST/JSON Version

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Default values
PYTHON=python3
PIP=pip3

# Function to print colored output
print_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if Python 3 is available
check_python() {
    if ! command -v $PYTHON &> /dev/null; then
        print_error "Python 3 is not installed or not in PATH"
        exit 1
    fi
    print_info "Using Python: $(which $PYTHON)"
}

# Install dependencies
install_deps() {
    print_info "Installing dependencies..."
    $PIP install -r requirements-simple.txt
}

# Run coordinator (Flask REST server)
run_coordinator() {
    print_info "Starting coordinator (Flask REST server)..."
    print_info "Coordinator will be available at: http://localhost:50050"
    print_info "Available endpoints:"
    print_info "  POST /execute - Execute transaction"
    print_info "  GET  /status/{id} - Get transaction status"
    print_info "  GET  /transactions - List all transactions"
    print_info "  GET  /participants - List participants"
    print_info "  GET  /health - Health check"
    $PYTHON cmd/coordinator/main.py "$@"
}

# Run participant (Flask REST server)
run_participant() {
    if [ -z "$1" ] || [ -z "$2" ]; then
        print_error "Usage: $0 run-participant <id> <port>"
        print_error "Example: $0 run-participant participant1 50051"
        exit 1
    fi
    print_info "Starting participant $1 (Flask REST server) on port $2..."
    print_info "Participant will be available at: http://localhost:$2"
    $PYTHON cmd/participant/simple_participant.py "$1" "$2"
}

# Run client (HTTP client)
run_client() {
    print_info "Running test client (HTTP client)..."
    $PYTHON cmd/client/main.py "$@"
}

# Run complete demo
run_demo() {
    print_info "Starting Two-Phase Commit Demo (REST/JSON)..."
    
    # Start coordinator in background
    print_info "Starting coordinator on port 50050..."
    $PYTHON cmd/coordinator/main.py &
    COORDINATOR_PID=$!
    sleep 3
    
    # Start participants in background
    print_info "Starting participant1 on port 50051..."
    $PYTHON cmd/participant/simple_participant.py participant1 50051 &
    PARTICIPANT1_PID=$!
    sleep 2
    
    print_info "Starting participant2 on port 50052..."
    $PYTHON cmd/participant/simple_participant.py participant2 50052 &
    PARTICIPANT2_PID=$!
    sleep 2
    
    # Run test transaction
    print_info "Running test transaction..."
    $PYTHON cmd/client/main.py
    
    # Cleanup
    print_info "Demo completed. Stopping services..."
    kill $COORDINATOR_PID 2>/dev/null || true
    kill $PARTICIPANT1_PID 2>/dev/null || true
    kill $PARTICIPANT2_PID 2>/dev/null || true
}

# Run tests
run_tests() {
    print_info "Running tests..."
    $PYTHON -m pytest tests/ -v
}

# Clean build artifacts
clean() {
    print_info "Cleaning build artifacts..."
    find . -type f -name "*.pyc" -delete
    find . -type d -name "__pycache__" -delete
    find . -type d -name "*.egg-info" -exec rm -rf {} +
    print_info "Clean completed"
}

# Show help
show_help() {
    echo "Two-Phase Commit Python Project (REST/JSON Version)"
    echo ""
    echo "Available commands:"
    echo "  install-deps      - Install Flask/REST dependencies"
    echo "  run-coordinator   - Run coordinator (Flask REST server on port 50050)"
    echo "  run-participant   - Run participant (Flask REST server, usage: <id> <port>)"
    echo "  run-client        - Run test client (HTTP client)"
    echo "  run-demo          - Run complete demo with coordinator and participants"
    echo "  run-tests         - Run tests"
    echo "  clean            - Clean build artifacts"
    echo "  help             - Show this help"
    echo ""
    echo "Examples:"
    echo "  $0 run-participant participant1 50051"
    echo "  $0 run-coordinator --port 50050"
    echo "  $0 run-demo"
    echo ""
    echo "Flask REST API Endpoints:"
    echo "  Coordinator (port 50050):"
    echo "    POST /execute - Execute transaction"
    echo "    GET  /status/{id} - Get transaction status"
    echo "    GET  /transactions - List all transactions"
    echo "    GET  /participants - List participants"
    echo "    GET  /health - Health check"
    echo ""
    echo "  Participant (ports 50051, 50052, etc.):"
    echo "    POST /begin - Start a new local transaction"
    echo "    POST /prepare - Prepare local resources for commit"
    echo "    POST /commit - Commit local changes"
    echo "    POST /abort - Rollback local changes"
    echo "    GET  /status/{id} - Get current transaction status"
    echo "    GET  /resource/{key} - Get resource value"
}

# Main script
main() {
    check_python
    
    case "${1:-help}" in
        "install-deps")
            install_deps
            ;;
        "run-coordinator")
            shift
            run_coordinator "$@"
            ;;
        "run-participant")
            shift
            run_participant "$@"
            ;;
        "run-client")
            shift
            run_client "$@"
            ;;
        "run-demo")
            run_demo
            ;;
        "run-tests")
            run_tests
            ;;
        "clean")
            clean
            ;;
        "help"|*)
            show_help
            ;;
    esac
}

# Run main function with all arguments
main "$@"
