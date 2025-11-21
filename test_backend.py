#!/usr/bin/env python3
"""
Quick backend test script
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_imports():
    """Test all imports work"""
    print("Testing imports...")
    try:
        from backend.core.config import settings
        print("✅ Config")

        from backend.core.security import get_password_hash, verify_password
        print("✅ Security")

        from backend.core.storage import read_json, write_json
        print("✅ Storage")

        from backend.api import auth, team, leetcode, analytics
        print("✅ API routers")

        from backend.main import app
        print("✅ FastAPI app")

        return True
    except Exception as e:
        print(f"❌ Import failed: {e}")
        return False

def test_password_hashing():
    """Test password hashing"""
    print("\nTesting password hashing...")
    try:
        from backend.core.security import get_password_hash, verify_password

        password = "testpassword123"
        hashed = get_password_hash(password)

        assert verify_password(password, hashed), "Password verification failed"
        assert not verify_password("wrongpassword", hashed), "Should reject wrong password"

        print("✅ Password hashing works correctly")
        return True
    except Exception as e:
        print(f"❌ Password hashing failed: {e}")
        return False

def test_storage():
    """Test storage functions"""
    print("\nTesting storage...")
    try:
        from backend.core.storage import read_json, write_json, use_s3

        print(f"   Storage mode: {'S3' if use_s3() else 'Local'}")

        # Test write
        test_data = {"test": "data", "number": 123}
        write_json("test_file.json", test_data)
        print("✅ Write successful")

        # Test read
        read_data = read_json("test_file.json", default={})
        assert read_data == test_data, "Read data doesn't match written data"
        print("✅ Read successful")

        # Cleanup
        if not use_s3():
            os.remove("data/test_file.json")

        return True
    except Exception as e:
        print(f"❌ Storage failed: {e}")
        return False

def test_api_creation():
    """Test FastAPI app creation"""
    print("\nTesting API creation...")
    try:
        from backend.main import app
        from fastapi.testclient import TestClient

        client = TestClient(app)

        # Test root endpoint
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        print("✅ Root endpoint works")

        # Test health check
        response = client.get("/api/health")
        assert response.status_code == 200
        print("✅ Health check works")

        return True
    except Exception as e:
        print(f"❌ API creation failed: {e}")
        return False

def test_daily_challenge():
    """Test LeetCode API integration"""
    print("\nTesting LeetCode API...")
    try:
        from utils.leetcodeapi import fetch_daily_challenge

        challenge = fetch_daily_challenge()
        if challenge:
            print(f"✅ Daily challenge: {challenge.get('title', 'Unknown')}")
            return True
        else:
            print("⚠️  No daily challenge available (API might be down)")
            return True  # Don't fail test if API is down
    except Exception as e:
        print(f"❌ LeetCode API failed: {e}")
        return False

def main():
    """Run all tests"""
    print("="*60)
    print("BACKEND TESTS")
    print("="*60)

    tests = [
        ("Imports", test_imports),
        ("Password Hashing", test_password_hashing),
        ("Storage", test_storage),
        ("API Creation", test_api_creation),
        ("LeetCode API", test_daily_challenge),
    ]

    results = []
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"\n❌ {name} crashed: {e}")
            results.append((name, False))

    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{name:.<40} {status}")

    print("="*60)
    print(f"Results: {passed}/{total} tests passed")

    if passed == total:
        print("🎉 All tests passed!")
        return 0
    else:
        print("⚠️  Some tests failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())
