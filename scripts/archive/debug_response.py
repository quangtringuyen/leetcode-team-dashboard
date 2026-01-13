#!/usr/bin/env python3
"""Debug script to see what LeetCode is actually returning"""
import requests

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Content-Type': 'application/json',
    'Accept': 'application/json',
    'Accept-Language': 'en-US,en;q=0.9',
    'Accept-Encoding': 'gzip, deflate, br',
    'Origin': 'https://leetcode.com',
    'Referer': 'https://leetcode.com/',
    'Connection': 'keep-alive',
    'Sec-Fetch-Dest': 'empty',
    'Sec-Fetch-Mode': 'cors',
    'Sec-Fetch-Site': 'same-origin',
}

url = "https://leetcode.com/graphql"
query = """
query getUserProfile($username: String!) {
  matchedUser(username: $username) {
    username
    profile {
      ranking
    }
  }
}
"""

print("Sending request to:", url)
print("Headers:", HEADERS)
print()

response = requests.post(
    url,
    json={"query": query, "variables": {"username": "leetcode"}},
    headers=HEADERS,
    timeout=15
)

print("Status Code:", response.status_code)
print("Content-Type:", response.headers.get('Content-Type'))
print("Content-Length:", response.headers.get('Content-Length'))
print("\nResponse Headers:")
for key, value in response.headers.items():
    print(f"  {key}: {value}")

print("\n" + "="*60)
print("Response Body (first 500 chars):")
print("="*60)
print(response.text[:500])
print("="*60)

print("\nResponse Body (full):")
print(response.text)
