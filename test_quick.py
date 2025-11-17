#!/usr/bin/env python
"""Quick test of Phase 3 endpoints."""

from fastapi.testclient import TestClient
import sys
from pathlib import Path

project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.api.main import app

client = TestClient(app)

print("="*70)
print("QUICK PHASE 3 TEST")
print("="*70)

# Test 1: Student registration
print("\n1. Testing student registration...")
response = client.post("/api/student/register", json={
    "user_id": "quicktest_user",
    "name": "Quick Test User",
    "email": "quick@test.com"
})
print(f"   Status: {response.status_code}")
if response.status_code == 200:
    print(f"   ✅ Student registered: {response.json()['user_id']}")
else:
    print(f"   ❌ Error: {response.json()}")
    sys.exit(1)

# Test 2: Get student
print("\n2. Testing get student...")
response = client.get("/api/student/quicktest_user")
print(f"   Status: {response.status_code}")
if response.status_code == 200:
    print(f"   ✅ Student retrieved: {response.json()['name']}")
else:
    print(f"   ❌ Error: {response.json()}")
    sys.exit(1)

# Test 3: Session creation
print("\n3. Testing session creation...")
response = client.post("/api/session/start", json={
    "user_id": "quicktest_user",
    "topic_id": "dynamic_programming",
    "session_type": "learning",
    "goal": "Learn DP basics"
})
print(f"   Status: {response.status_code}")
if response.status_code == 200:
    data = response.json()
    session_id = data['session_id']
    print(f"   ✅ Session created: {session_id}")
else:
    print(f"   ❌ Error: {response.json()}")
    sys.exit(1)

# Test 4: Get curriculum graph
print("\n4. Testing curriculum graph...")
response = client.get("/api/curriculum/graph")
print(f"   Status: {response.status_code}")
if response.status_code == 200:
    data = response.json()
    print(f"   ✅ Topics: {len(data['topics'])}, Prerequisites: {len(data['prerequisites'])}")
else:
    print(f"   ❌ Error: {response.json()}")
    sys.exit(1)

# Test 5: Get progress
print("\n5. Testing get progress...")
response = client.get("/api/student/quicktest_user/progress")
print(f"   Status: {response.status_code}")
if response.status_code == 200:
    data = response.json()
    print(f"   ✅ Progress: {data['total_topics']} topics studied")
else:
    print(f"   ❌ Error: {response.json()}")
    sys.exit(1)

print("\n" + "="*70)
print("ALL TESTS PASSED ✅")
print("="*70)
