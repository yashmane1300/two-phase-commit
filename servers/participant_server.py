#!/usr/bin/env python3

import sys
import os

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from participant.simple_participant import SQLiteParticipant
from participant.app import app, set_participant

if __name__ == '__main__':
    if len(sys.argv) < 3:
        print("Usage: python3 participant_server.py <participant_id> <port>")
        sys.exit(1)
    
    participant_id = sys.argv[1]
    port = int(sys.argv[2])
    
    # Create participant with SQLite database
    participant = SQLiteParticipant(participant_id)
    
    # Set the participant instance in the app
    set_participant(participant)
    
    print(f"Starting Two-Phase Commit Participant {participant_id} on port {port}")
    print(f"Database: {participant.db_path}")
    app.run(host='0.0.0.0', port=port, debug=True)
