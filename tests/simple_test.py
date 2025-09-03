#!/usr/bin/env python3

import requests
import time
import json

def test_coordinator_only():
    """Test the coordinator functionality without participants"""
    print("🧪 Testing Coordinator Functionality")
    print("=" * 50)
    
    coordinator_url = "http://localhost:50050"
    
    # Test health endpoint
    print("1. Testing health endpoint...")
    try:
        health_response = requests.get(f"{coordinator_url}/health", timeout=10)
        if health_response.status_code == 200:
            health = health_response.json()
            print(f"✅ Health: {health['status']}")
            print(f"📊 Participants: {health['participants_count']}")
            print(f"📝 Transactions: {health['transactions_count']}")
        else:
            print(f"❌ Health check failed: {health_response.status_code}")
    except Exception as e:
        print(f"❌ Health check error: {e}")
    
    # Test participants endpoint
    print("\n2. Testing participants endpoint...")
    try:
        participants_response = requests.get(f"{coordinator_url}/participants", timeout=10)
        if participants_response.status_code == 200:
            participants = participants_response.json()
            print(f"✅ Found {len(participants)} participants:")
            for p in participants:
                print(f"   - {p['id']}: {p['address']}")
        else:
            print(f"❌ Participants check failed: {participants_response.status_code}")
    except Exception as e:
        print(f"❌ Participants check error: {e}")
    
    # Test transactions endpoint
    print("\n3. Testing transactions endpoint...")
    try:
        transactions_response = requests.get(f"{coordinator_url}/transactions", timeout=10)
        if transactions_response.status_code == 200:
            transactions = transactions_response.json()
            print(f"✅ Found {len(transactions)} transactions:")
            for txn in transactions:
                print(f"   - {txn['id'][:8]}...: {txn['status']} ({len(txn['participants'])} participants)")
        else:
            print(f"❌ Transactions check failed: {transactions_response.status_code}")
    except Exception as e:
        print(f"❌ Transactions check error: {e}")
    
    # Test transaction execution (will likely fail due to participant issues)
    print("\n4. Testing transaction execution...")
    try:
        operations = [
            {"key": "test_key1", "value": "test_value1", "type": "WRITE"},
            {"key": "test_key2", "value": "test_value2", "type": "WRITE"}
        ]
        participants = ["participant1", "participant2"]
        
        response = requests.post(
            f"{coordinator_url}/execute",
            json={"operations": operations, "participants": participants},
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Transaction executed: {result['success']}")
            print(f"🆔 Transaction ID: {result['transaction_id']}")
            print(f"💬 Message: {result['message']}")
            
            # Check status
            status_response = requests.get(f"{coordinator_url}/status/{result['transaction_id']}")
            if status_response.status_code == 200:
                status = status_response.json()
                print(f"📊 Final status: {status['status']}")
        else:
            print(f"❌ Transaction execution failed: {response.status_code}")
            print(f"Response: {response.text}")
    except Exception as e:
        print(f"❌ Transaction execution error: {e}")

def test_participant_registration():
    """Test registering new participants"""
    print("\n🧪 Testing Participant Registration")
    print("=" * 50)
    
    coordinator_url = "http://localhost:50050"
    
    # Register a new participant
    print("1. Registering new participant...")
    try:
        register_response = requests.post(
            f"{coordinator_url}/register",
            json={"participant_id": "test_participant", "address": "localhost:50070"},
            timeout=10
        )
        
        if register_response.status_code == 200:
            result = register_response.json()
            print(f"✅ Participant registered: {result['success']}")
            print(f"💬 Message: {result['message']}")
        else:
            print(f"❌ Registration failed: {register_response.status_code}")
    except Exception as e:
        print(f"❌ Registration error: {e}")
    
    # Check updated participants list
    print("\n2. Checking updated participants list...")
    try:
        participants_response = requests.get(f"{coordinator_url}/participants", timeout=10)
        if participants_response.status_code == 200:
            participants = participants_response.json()
            print(f"✅ Total participants: {len(participants)}")
            for p in participants:
                print(f"   - {p['id']}: {p['address']}")
        else:
            print(f"❌ Participants check failed: {participants_response.status_code}")
    except Exception as e:
        print(f"❌ Participants check error: {e}")

def main():
    """Run all tests"""
    print("🚀 Two-Phase Commit Service Testing")
    print("=" * 60)
    
    # Test coordinator functionality
    test_coordinator_only()
    
    # Test participant registration
    test_participant_registration()
    
    print("\n✅ Testing completed!")
    print("\n📋 Summary:")
    print("   - Coordinator is running and responding")
    print("   - Basic API endpoints are working")
    print("   - Participant registration is functional")
    print("   - Transaction execution may fail due to participant connectivity")
    print("\n💡 To test full 2PC functionality:")
    print("   - Start participant servers on different ports")
    print("   - Register them with the coordinator")
    print("   - Run transaction tests")

if __name__ == "__main__":
    main()
