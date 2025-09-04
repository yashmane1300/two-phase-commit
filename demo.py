#!/usr/bin/env python3

import subprocess
import time
import signal
import sys
import os
import requests
import sqlite3

def kill_existing_processes():
    """Kill any existing Python processes that might be using our ports"""
    print("🔧 Cleaning up existing processes...")
    try:
        # Try different methods to kill processes
        import psutil
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                cmdline = ' '.join(proc.info['cmdline']) if proc.info['cmdline'] else ''
                if 'coordinator_server.py' in cmdline or 'participant_server.py' in cmdline:
                    proc.terminate()
                    print(f"✅ Killed process {proc.info['pid']}")
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
        time.sleep(2)  # Give time for processes to terminate
        print("✅ Cleanup completed")
    except ImportError:
        # Fallback if psutil is not available
        print("⚠️  psutil not available, skipping process cleanup")
    except Exception as e:
        print(f"⚠️  Cleanup warning: {e}")

def check_port_available(port):
    """Check if a port is available"""
    try:
        import socket
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(('localhost', port))
            return True
    except:
        return False

def wait_for_service(url, timeout=30):
    """Wait for a service to be ready"""
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            response = requests.get(url, timeout=2)
            if response.status_code == 200:
                return True
        except:
            pass
        time.sleep(1)
    return False

def show_database_contents(participant_id):
    """Show current database contents for a participant"""
    db_file = f"participant_{participant_id}.db"
    if os.path.exists(db_file):
        try:
            conn = sqlite3.connect(db_file)
            cursor = conn.cursor()
            cursor.execute('SELECT key, value FROM resources ORDER BY key')
            results = cursor.fetchall()
            conn.close()
            
            print(f"📊 {participant_id} current data:")
            for key, value in results:
                print(f"   {key}: {value}")
            return results
        except Exception as e:
            print(f"❌ Error reading {db_file}: {e}")
    return []

def run_demo():
    """Run the complete two-phase commit demo with SQLite databases"""
    
    print("🚀 Starting Two-Phase Commit Demo (SQLite Version)")
    print("=" * 60)
    
    # Clean up existing processes
    kill_existing_processes()
    
    # Use different ports to avoid conflicts
    COORDINATOR_PORT = 50100
    PARTICIPANT1_PORT = 50101
    PARTICIPANT2_PORT = 50102
    
    # Set PATH for subprocesses
    env = os.environ.copy()
    env['PATH'] = "/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin"
    
    processes = []
    
    try:
        # Show initial data
        print("\n📋 Initial Database State:")
        print("-" * 30)
        data1 = show_database_contents("participant1")
        data2 = show_database_contents("participant2")
        
        # Start coordinator
        print(f"\n📡 Starting coordinator on port {COORDINATOR_PORT}...")
        if not check_port_available(COORDINATOR_PORT):
            print(f"❌ Port {COORDINATOR_PORT} is not available")
            return
            
        coordinator_process = subprocess.Popen(
            [sys.executable, "servers/coordinator_server.py", "--port", str(COORDINATOR_PORT)],
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        processes.append(coordinator_process)
        
        # Wait for coordinator to start
        if not wait_for_service(f"http://localhost:{COORDINATOR_PORT}/health"):
            print("❌ Coordinator failed to start")
            return
        print("✅ Coordinator started successfully")
        
        # Start participants
        print(f"\n🖥️  Starting participant1 on port {PARTICIPANT1_PORT}...")
        if not check_port_available(PARTICIPANT1_PORT):
            print(f"❌ Port {PARTICIPANT1_PORT} is not available")
            return
            
        participant1_process = subprocess.Popen(
            [sys.executable, "servers/participant_server.py", "participant1", str(PARTICIPANT1_PORT)],
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        processes.append(participant1_process)
        
        if not wait_for_service(f"http://localhost:{PARTICIPANT1_PORT}/resource/key1"):
            print("❌ Participant1 failed to start")
            return
        print("✅ Participant1 started successfully")
        
        print(f"🖥️  Starting participant2 on port {PARTICIPANT2_PORT}...")
        if not check_port_available(PARTICIPANT2_PORT):
            print(f"❌ Port {PARTICIPANT2_PORT} is not available")
            return
            
        participant2_process = subprocess.Popen(
            [sys.executable, "servers/participant_server.py", "participant2", str(PARTICIPANT2_PORT)],
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        processes.append(participant2_process)
        
        if not wait_for_service(f"http://localhost:{PARTICIPANT2_PORT}/resource/key1"):
            print("❌ Participant2 failed to start")
            return
        print("✅ Participant2 started successfully")
        
        # Register participants with coordinator
        print("\n📝 Registering participants with coordinator...")
        try:
            requests.post(f"http://localhost:{COORDINATOR_PORT}/register", 
                         json={"participant_id": "participant1", "address": f"localhost:{PARTICIPANT1_PORT}"})
            requests.post(f"http://localhost:{COORDINATOR_PORT}/register", 
                         json={"participant_id": "participant2", "address": f"localhost:{PARTICIPANT2_PORT}"})
            print("✅ Participants registered")
        except Exception as e:
            print(f"⚠️  Registration warning: {e}")
        
        # Execute 2PC transaction
        print("\n🧪 Executing Two-Phase Commit Transaction...")
        print("-" * 50)
        
        # Define the transaction
        operations = [
            {"key": "key1", "value": "updated_value1", "type": "WRITE"},
            {"key": "key2", "value": "updated_value2", "type": "WRITE"},
            {"key": "new_key", "value": "new_value", "type": "WRITE"}
        ]
        participants = ["participant1", "participant2"]
        
        print("📝 Transaction Operations:")
        for op in operations:
            print(f"   {op['type']}: {op['key']} = {op['value']}")
        
        print(f"👥 Participants: {', '.join(participants)}")
        
        # Execute the transaction
        try:
            response = requests.post(
                f"http://localhost:{COORDINATOR_PORT}/execute",
                json={"operations": operations, "participants": participants},
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                print(f"\n✅ Transaction Result: {result['message']}")
                print(f"🆔 Transaction ID: {result['transaction_id']}")
                
                # Get transaction status
                status_response = requests.get(f"http://localhost:{COORDINATOR_PORT}/status/{result['transaction_id']}")
                if status_response.status_code == 200:
                    status = status_response.json()
                    print(f"📊 Final Status: {status['status']}")
                
                # Show updated data
                print("\n📋 Updated Database State:")
                print("-" * 30)
                show_database_contents("participant1")
                show_database_contents("participant2")
                
                # Verify consistency
                print("\n🔍 Consistency Check:")
                print("-" * 20)
                
                # Check if both participants have the same data
                conn1 = sqlite3.connect("participant_participant1.db")
                conn2 = sqlite3.connect("participant_participant2.db")
                
                cursor1 = conn1.cursor()
                cursor2 = conn2.cursor()
                
                cursor1.execute('SELECT key, value FROM resources ORDER BY key')
                cursor2.execute('SELECT key, value FROM resources ORDER BY key')
                
                data1 = cursor1.fetchall()
                data2 = cursor2.fetchall()
                
                conn1.close()
                conn2.close()
                
                if data1 == data2:
                    print("✅ Data consistency verified - both participants have identical data")
                    print(f"📊 Total records: {len(data1)}")
                else:
                    print("❌ Data inconsistency detected!")
                    print("Participant1:", data1)
                    print("Participant2:", data2)
                
            else:
                print(f"❌ Transaction failed: {response.status_code}")
                print(f"Response: {response.text}")
                
        except Exception as e:
            print(f"❌ Transaction execution error: {e}")
        
        print("\n✅ Demo completed successfully!")
        
        # Show API endpoints
        print("\n🔗 Available API Endpoints:")
        print(f"   POST http://localhost:{COORDINATOR_PORT}/execute - Execute transaction")
        print(f"   GET  http://localhost:{COORDINATOR_PORT}/status/{{id}} - Get transaction status")
        print(f"   GET  http://localhost:{COORDINATOR_PORT}/transactions - List all transactions")
        print(f"   GET  http://localhost:{COORDINATOR_PORT}/participants - List participants")
        print(f"   GET  http://localhost:{COORDINATOR_PORT}/health - Health check")
        print(f"   GET  http://localhost:{PARTICIPANT1_PORT}/resource/{{key}} - Get participant1 resource")
        print(f"   GET  http://localhost:{PARTICIPANT2_PORT}/resource/{{key}} - Get participant2 resource")
        
        print("\n💾 Each participant uses its own SQLite database file!")
        print("   This demonstrates true distributed data consistency.")
        
    except KeyboardInterrupt:
        print("\n⏹️  Demo interrupted by user")
    except Exception as e:
        print(f"❌ Demo failed: {e}")
    finally:
        # Cleanup
        print("\n🧹 Stopping all services...")
        for process in processes:
            try:
                process.terminate()
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
            except:
                pass
        print("✅ All services stopped")

if __name__ == '__main__':
    run_demo()
