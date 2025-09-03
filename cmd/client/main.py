#!/usr/bin/env python3

import json
import requests
import time

def test_two_phase_commit():
    """Test the two-phase commit system"""
    
    coordinator_url = "http://localhost:50050"
    
    # Test data
    operations = [
        {
            "key": "key1",
            "value": "new_value1",
            "type": "WRITE"
        },
        {
            "key": "key2", 
            "value": "new_value2",
            "type": "WRITE"
        },
        {
            "key": "key3",
            "type": "READ"
        }
    ]
    
    participants = ["participant1", "participant2"]
    
    print("🚀 Testing Two-Phase Commit System (REST/JSON)")
    print("=" * 60)
    
    # Execute transaction
    print("📝 Executing distributed transaction...")
    try:
        response = requests.post(
            f"{coordinator_url}/execute",
            json={
                "operations": operations,
                "participants": participants
            },
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Transaction result: {result['message']}")
            print(f"🆔 Transaction ID: {result['transaction_id']}")
            print(f"✅ Success: {result['success']}")
            
            if result['success']:
                # Get transaction status
                status_response = requests.get(
                    f"{coordinator_url}/status/{result['transaction_id']}"
                )
                
                if status_response.status_code == 200:
                    status_result = status_response.json()
                    print(f"📊 Transaction status: {status_result['status']}")
                    print(f"💬 Status message: {status_result['message']}")
                
                # Check resources on participants
                print("\n🔍 Checking resources on participants:")
                for participant_id in participants:
                    port = 50051 if participant_id == "participant1" else 50052
                    participant_url = f"http://localhost:{port}"
                    
                    for op in operations:
                        if op['type'] == 'WRITE':
                            resource_response = requests.get(
                                f"{participant_url}/resource/{op['key']}"
                            )
                            if resource_response.status_code == 200:
                                resource_result = resource_response.json()
                                print(f"   {participant_id}: {op['key']} = {resource_result['value']}")
                
                # Get all transactions
                print("\n📋 All transactions:")
                transactions_response = requests.get(f"{coordinator_url}/transactions")
                if transactions_response.status_code == 200:
                    transactions = transactions_response.json()
                    for txn in transactions:
                        print(f"   {txn['id'][:8]}... - {txn['status']} - {len(txn['participants'])} participants")
                
                # Get participants
                print("\n👥 Registered participants:")
                participants_response = requests.get(f"{coordinator_url}/participants")
                if participants_response.status_code == 200:
                    participants_list = participants_response.json()
                    for p in participants_list:
                        print(f"   {p['id']} at {p['address']}")
            
        else:
            print(f"❌ Failed to execute transaction: {response.status_code}")
            
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to coordinator. Make sure it's running on port 50050")
    except requests.exceptions.Timeout:
        print("⏰ Transaction timed out")
    except Exception as e:
        print(f"❌ Error: {e}")

def test_api_endpoints():
    """Test individual API endpoints"""
    
    coordinator_url = "http://localhost:50050"
    
    print("\n🧪 Testing Individual API Endpoints")
    print("=" * 40)
    
    # Health check
    try:
        health_response = requests.get(f"{coordinator_url}/health")
        if health_response.status_code == 200:
            health = health_response.json()
            print(f"🏥 Health: {health['status']}")
            print(f"📊 Participants: {health['participants_count']}")
            print(f"📝 Transactions: {health['transactions_count']}")
    except Exception as e:
        print(f"❌ Health check failed: {e}")
    
    # Get participants
    try:
        participants_response = requests.get(f"{coordinator_url}/participants")
        if participants_response.status_code == 200:
            participants = participants_response.json()
            print(f"👥 Participants: {len(participants)} registered")
            for p in participants:
                print(f"   - {p['id']}: {p['address']}")
    except Exception as e:
        print(f"❌ Participants check failed: {e}")

if __name__ == "__main__":
    test_two_phase_commit()
    test_api_endpoints()
