#!/usr/bin/env python3

import argparse
import logging
import signal
import sys
import os

# Add the current directory to Python path
sys.path.insert(0, os.getcwd())

# Import our modules
from internal.coordinator.coordinator import app

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="Two-Phase Commit Coordinator")
    parser.add_argument("--port", type=int, default=50050, help="Port to listen on")
    parser.add_argument("--timeout", type=float, default=30.0, help="Transaction timeout in seconds")
    
    args = parser.parse_args()
    
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Handle graceful shutdown
    def signal_handler(signum, frame):
        logging.info("Received shutdown signal, stopping server...")
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        logging.info(f"Starting Two-Phase Commit Coordinator on port {args.port}")
        app.run(host='0.0.0.0', port=args.port, debug=False)
    except KeyboardInterrupt:
        logging.info("Coordinator server stopped")

if __name__ == "__main__":
    main()
