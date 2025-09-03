#!/usr/bin/env python3

import subprocess
import time
import signal
import sys
import os

def run_demo():
    """Run the complete two-phase commit demo with SQLite databases"""
    
    print("🚀 Starting Two-Phase Commit Demo (SQLite Version)")
    print("=" * 60)
    
    # Set PATH for subprocesses
    env = os.environ.copy()
    env['PATH'] = "/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin"
    
    processes = []
    
    try:
        # Start coordinator
        print("📡 Starting coordinator on port 50050...")
        coordinator_process = subprocess.Popen(
            ["python3", "cmd/coordinator/main.py"],
            env=env
        )
        processes.append(coordinator_process)
        time.sleep(3)  # Give coordinator time to start
        
        # Start participants in background
        print("🖥️  Starting participant1 on port 50051...")
        participant1_process = subprocess.Popen(
            ["python3", "cmd/participant/simple_participant.py", "participant1", "50051"],
            env=env
        )
        processes.append(participant1_process)
        time.sleep(2)
        
        print("🖥️  Starting participant2 on port 50052...")
        participant2_process = subprocess.Popen(
            ["python3", "cmd/participant/simple_participant.py", "participant2", "50052"],
            env=env
        )
        processes.append(participant2_process)
        time.sleep(2)
        
        # Run test client
        print("🧪 Running test transaction...")
        client_process = subprocess.run(
            ["python3", "cmd/client/main.py"],
            env=env,
            capture_output=True,
            text=True
        )
        
        print(client_process.stdout)
        if client_process.stderr:
            print("Errors:", client_process.stderr)
        
        print("\n✅ Demo completed successfully!")
        
        # Show database files
        print("\n🗄️  SQLite Database Files Created:")
        for i in range(1, 3):
            db_file = f"participant_participant{i}.db"
            if os.path.exists(db_file):
                size = os.path.getsize(db_file)
                print(f"   {db_file} ({size} bytes)")
        
        # Show API endpoints
        print("\n🔗 Available API Endpoints:")
        print("   POST http://localhost:50050/execute - Execute transaction")
        print("   GET  http://localhost:50050/status/{id} - Get transaction status")
        print("   GET  http://localhost:50050/transactions - List all transactions")
        print("   GET  http://localhost:50050/participants - List participants")
        print("   GET  http://localhost:50050/health - Health check")
        print("   POST http://localhost:50050/register - Register participant")
        
        print("\n💾 Each participant now uses its own SQLite database file!")
        print("   This makes the 2PC protocol more realistic with actual data persistence.")
        
    except KeyboardInterrupt:
        print("\n⏹️  Demo interrupted by user")
    except Exception as e:
        print(f"❌ Demo failed: {e}")
    finally:
        # Cleanup
        print("🧹 Stopping all services...")
        for process in processes:
            try:
                process.terminate()
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
            except:
                pass

if __name__ == '__main__':
    run_demo()
