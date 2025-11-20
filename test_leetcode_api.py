#!/usr/bin/env python3
"""
Quick test script to diagnose LeetCode API connectivity issues.
Run this to see exactly what's happening with API requests.
"""
import sys
sys.path.insert(0, '/app')  # For Docker environment

from utils.leetcodeapi import fetch_user_data, fetch_daily_challenge
import requests

def test_basic_connection():
    """Test basic connection to leetcode.com"""
    print("\n" + "="*60)
    print("TEST 1: Basic HTTP Connection to leetcode.com")
    print("="*60)
    try:
        response = requests.get("https://leetcode.com", timeout=10)
        print(f"✅ Status Code: {response.status_code}")
        print(f"✅ Can reach leetcode.com")
        return True
    except Exception as e:
        print(f"❌ Failed to connect: {e}")
        return False

def test_graphql_endpoint():
    """Test GraphQL endpoint directly"""
    print("\n" + "="*60)
    print("TEST 2: GraphQL Endpoint Test")
    print("="*60)

    url = "https://leetcode.com/graphql"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Content-Type': 'application/json',
    }
    query = """
    query {
      activeDailyCodingChallengeQuestion {
        question {
          title
        }
      }
    }
    """

    try:
        response = requests.post(
            url,
            json={"query": query},
            headers=headers,
            timeout=15
        )
        print(f"Status Code: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ GraphQL endpoint is working")
            print(f"Response data: {data}")
            return True
        else:
            print(f"❌ GraphQL returned status {response.status_code}")
            print(f"Response: {response.text[:200]}")
            return False
    except Exception as e:
        print(f"❌ GraphQL test failed: {e}")
        return False

def test_fetch_user():
    """Test fetching a known user (LeetCode official account)"""
    print("\n" + "="*60)
    print("TEST 3: Fetch User Data (leetcode)")
    print("="*60)

    try:
        result = fetch_user_data("leetcode")
        if result:
            print(f"✅ Successfully fetched user data")
            print(f"   Username: {result.get('username')}")
            print(f"   Total Solved: {result.get('totalSolved')}")
            print(f"   Ranking: {result.get('ranking')}")
            return True
        else:
            print(f"❌ fetch_user_data returned None")
            return False
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_daily_challenge():
    """Test fetching daily challenge"""
    print("\n" + "="*60)
    print("TEST 4: Fetch Daily Challenge")
    print("="*60)

    try:
        result = fetch_daily_challenge()
        if result:
            print(f"✅ Successfully fetched daily challenge")
            print(f"   Title: {result.get('title')}")
            print(f"   Difficulty: {result.get('difficulty')}")
            return True
        else:
            print(f"❌ fetch_daily_challenge returned None")
            return False
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all tests"""
    print("\n" + "="*60)
    print("LeetCode API Connectivity Test")
    print("="*60)

    results = {
        "Basic Connection": test_basic_connection(),
        "GraphQL Endpoint": test_graphql_endpoint(),
        "Fetch User Data": test_fetch_user(),
        "Daily Challenge": test_daily_challenge(),
    }

    print("\n" + "="*60)
    print("TEST RESULTS SUMMARY")
    print("="*60)
    for test_name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{test_name:.<50} {status}")

    all_passed = all(results.values())
    print("="*60)
    if all_passed:
        print("🎉 All tests passed! API is working correctly.")
    else:
        print("⚠️  Some tests failed. Check the logs above for details.")
        print("\nPossible issues:")
        print("  - Network/firewall blocking leetcode.com")
        print("  - DNS resolution problems")
        print("  - LeetCode API is down or changed")
        print("\nTroubleshooting:")
        print("  1. Check Docker DNS: docker-compose.yml has dns: [8.8.8.8, 8.8.4.4]")
        print("  2. Check logs: docker-compose logs -f leetcode-dashboard")
        print("  3. See TROUBLESHOOTING.md for more solutions")

    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(main())
