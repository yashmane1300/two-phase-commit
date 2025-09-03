#!/usr/bin/env python3

import requests
import time
import json

def test_successful_transaction():
    """Test a successful transaction"""
    print("🧪 Testing Successful Transaction")
    print("=" * 40)
    
    operations = [
        {"key": "test_key1", "value": "new_value1", "type": "WRITE"},
        {"key": "test_key2", "value": "new_value2", "type": "WRITE"},
        {"key": "key1", "type": "READ"}
    ]
    
    participants = ["participant1", "participant2"]
    
    response = requests.post(
        "http://localhost:50050/execute",
        json={"operations": operations, "participants": participants},
        timeout=30
    )
    
    if response.status_code == 200:
        result = response.json()
        print(f"✅ Transaction successful: {result['success']}")
        print(f"🆔 Transaction ID: {result['transaction_id']}")
        print(f"💬 Message: {result['message']}")
        
        # Check status
        status_response = requests.get(f"http://localhost:50050/status/{result['transaction_id']}")
        if status_response.status_code == 200:
            status = status_response.json()
            print(f"📊 Status: {status['status']}")
        
        return True
    else:
        print(f"❌ Transaction failed: {response.status_code}")
        return False

def test_read_only_transaction():
    """Test a read-only transaction"""
    print("\n🧪 Testing Read-Only Transaction")
    print("=" * 40)
    
    operations = [
        {"key": "key1", "type": "READ"},
        {"key": "key2", "type": "READ"},
        {"key": "key3", "type": "READ"}
    ]
    
    participants = ["participant1", "participant2"]
    
    response = requests.post(
        "http://localhost:50050/execute",
        json={"operations": operations, "participants": participants},
        timeout=30
    )
    
    if response.status_code == 200:
        result = response.json()
        print(f"✅ Read-only transaction successful: {result['success']}")
        print(f"🆔 Transaction ID: {result['transaction_id']}")
        return True
    else:
        print(f"❌ Read-only transaction failed: {response.status_code}")
        return False

def test_delete_operation():
    """Test a transaction with delete operations"""
    print("\n🧪 Testing Delete Operation")
    print("=" * 40)
    
    # First, create a key to delete
    create_operations = [
        {"key": "delete_test_key", "value": "to_be_deleted", "type": "WRITE"}
    ]
    
    create_response = requests.post(
        "http://localhost:50050/execute",
        json={"operations": create_operations, "participants": ["participant1"]},
        timeout=30
    )
    
    if create_response.status_code == 200:
        print("✅ Created key for deletion")
        
        # Now delete it
        delete_operations = [
            {"key": "delete_test_key", "type": "DELETE"}
        ]
        
        delete_response = requests.post(
            "http://localhost:50050/execute",
            json={"operations": delete_operations, "participants": ["participant1"]},
            timeout=30
        )
        
        if delete_response.status_code == 200:
            result = delete_response.json()
            print(f"✅ Delete transaction successful: {result['success']}")
            print(f"🆔 Transaction ID: {result['transaction_id']}")
            return True
        else:
            print(f"❌ Delete transaction failed: {delete_response.status_code}")
            return False
    else:
        print(f"❌ Failed to create key for deletion: {create_response.status_code}")
        return False

def test_health_endpoints():
    """Test health and status endpoints"""
    print("\n🧪 Testing Health Endpoints")
    print("=" * 40)
    
    # Health check
    health_response = requests.get("http://localhost:50050/health")
    if health_response.status_code == 200:
        health = health_response.json()
        print(f"🏥 Health: {health['status']}")
        print(f"📊 Participants: {health['participants_count']}")
        print(f"📝 Transactions: {health['transactions_count']}")
    
    # Get participants
    participants_response = requests.get("http://localhost:50050/participants")
    if participants_response.status_code == 200:
        participants = participants_response.json()
        print(f"👥 Participants: {len(participants)}")
        for p in participants:
            print(f"   - {p['id']}: {p['address']}")
    
    # Get all transactions
    transactions_response = requests.get("http://localhost:50050/transactions")
    if transactions_response.status_code == 200:
        transactions = transactions_response.json()
        print(f"📋 Transactions: {len(transactions)}")
        for txn in transactions:
            print(f"   - {txn['id'][:8]}...: {txn['status']}")

def test_participant_resources():
    """Test accessing resources on participants"""
    print("\n🧪 Testing Participant Resources")
    print("=" * 40)
    
    participants = ["participant1", "participant2"]
    ports = [50051, 50052]
    
    for i, participant_id in enumerate(participants):
        port = ports[i]
        print(f"\n🔍 Checking {participant_id} (port {port}):")
        
        # Check some resources
        resources = ["key1", "key2", "key3"]
        for resource in resources:
            try:
                response = requests.get(f"http://localhost:{port}/resource/{resource}")
                if response.status_code == 200:
                    result = response.json()
                    print(f"   {resource}: {result['value']} (exists: {result['exists']})")
                else:
                    print(f"   {resource}: Error {response.status_code}")
            except Exception as e:
                print(f"   {resource}: Connection error - {e}")

def main():
    """Run all tests"""
    print("🚀 Comprehensive Two-Phase Commit Testing")
    print("=" * 60)
    
    # Wait a moment for services to be ready
    time.sleep(2)
    
    try:
        # Test successful transaction
        test_successful_transaction()
        
        # Test read-only transaction
        test_read_only_transaction()
        
        # Test delete operation
        test_delete_operation()
        
        # Test health endpoints
        test_health_endpoints()
        
        # Test participant resources
        test_participant_resources()
        
        print("\n✅ All tests completed successfully!")
        
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to coordinator. Make sure it's running on port 50050")
    except Exception as e:
        print(f"❌ Test failed: {e}")

if __name__ == "__main__":
    main()
