#!/usr/bin/env python3
"""
Network connectivity test script for LeetCode API.
Run this script to diagnose network issues.
"""
import sys
import requests
import socket
from urllib.parse import urlparse

def test_dns_resolution(hostname):
    """Test if hostname can be resolved."""
    print(f"\n🔍 Testing DNS resolution for {hostname}...")
    try:
        ip = socket.gethostbyname(hostname)
        print(f"✅ DNS resolution successful: {hostname} → {ip}")
        return True
    except socket.gaierror as e:
        print(f"❌ DNS resolution failed: {e}")
        return False

def test_http_connection(url):
    """Test HTTP connection to URL."""
    print(f"\n🌐 Testing HTTP connection to {url}...")
    try:
        response = requests.get(url, timeout=10)
        print(f"✅ HTTP connection successful: Status {response.status_code}")
        return True
    except requests.exceptions.RequestException as e:
        print(f"❌ HTTP connection failed: {e}")
        return False

def test_leetcode_api():
    """Test LeetCode GraphQL API."""
    print("\n🎯 Testing LeetCode GraphQL API...")
    url = "https://leetcode.com/graphql"
    query = """
    query {
      matchedUser(username: "leetcode") {
        username
        profile {
          ranking
        }
      }
    }
    """
    try:
        response = requests.post(
            url,
            json={"query": query},
            timeout=15
        )
        if response.status_code == 200:
            data = response.json()
            if "data" in data and data["data"]:
                print(f"✅ LeetCode GraphQL API is accessible")
                print(f"   Response: {data}")
                return True
            else:
                print(f"⚠️  API responded but data format unexpected: {data}")
                return False
        else:
            print(f"❌ API returned status {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ LeetCode API test failed: {e}")
        return False

def test_environment():
    """Check Python environment."""
    print("\n🐍 Checking Python environment...")
    print(f"   Python version: {sys.version}")
    print(f"   Requests version: {requests.__version__}")

    # Check DNS servers (if possible)
    try:
        import dns.resolver
        resolver = dns.resolver.Resolver()
        print(f"   DNS servers: {resolver.nameservers}")
    except ImportError:
        print("   (dnspython not installed, skipping DNS server check)")

def main():
    """Run all network tests."""
    print("=" * 60)
    print("🔧 LeetCode Team Dashboard - Network Connectivity Test")
    print("=" * 60)

    test_environment()

    # Test DNS resolution
    dns_ok = test_dns_resolution("leetcode.com")

    # Test basic HTTP
    http_ok = test_http_connection("https://leetcode.com")

    # Test LeetCode API
    api_ok = test_leetcode_api()

    # Summary
    print("\n" + "=" * 60)
    print("📊 Test Summary:")
    print("=" * 60)
    print(f"DNS Resolution:    {'✅ PASS' if dns_ok else '❌ FAIL'}")
    print(f"HTTP Connection:   {'✅ PASS' if http_ok else '❌ FAIL'}")
    print(f"LeetCode API:      {'✅ PASS' if api_ok else '❌ FAIL'}")
    print("=" * 60)

    if all([dns_ok, http_ok, api_ok]):
        print("\n🎉 All tests passed! Network connectivity is working.")
        print("   If you're still experiencing issues, check application logs.")
        return 0
    else:
        print("\n⚠️  Some tests failed. Please check:")
        if not dns_ok:
            print("   • DNS configuration (try using 8.8.8.8, 1.1.1.1)")
        if not http_ok:
            print("   • Firewall or proxy settings")
        if not api_ok:
            print("   • LeetCode API availability")
        print("\n   See TROUBLESHOOTING.md for solutions.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
