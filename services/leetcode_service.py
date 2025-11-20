# services/leetcode_service.py
from __future__ import annotations
from typing import List, Dict, Any
from datetime import datetime
import json
import requests
import pandas as pd
import streamlit as st

from utils.leetcodeapi import fetch_user_data


class LeetCodeService:
    @st.cache_data(show_spinner=False)
    def fetch_all(self, members: List[Dict[str, str]], cache_key: float = 0.0) -> List[Dict[str, Any]]:
        data = []
        for m in members:
            u = m["username"]
            d = fetch_user_data(u)
            if d:
                d["name"] = m.get("name", u)
                d["username"] = u
                data.append(d)
        return data

    @staticmethod
    def sum_accepted(submissions: Any) -> int:
        if not isinstance(submissions, list):
            return 0
        return sum(
            int(s.get("count", 0))
            for s in submissions
            if s.get("difficulty") in ("Easy", "Medium", "Hard")
        )

    @st.cache_data(show_spinner=False)
    def fetch_submission_calendar(self, username: str) -> Dict:
        import time
        url = f"https://leetcode.com/api/user_submission_calendar/?username={username}"

        # Headers to bypass filtering
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'application/json',
            'Accept-Language': 'en-US,en;q=0.9',
            'Referer': f'https://leetcode.com/{username}/',
            'Connection': 'keep-alive',
        }

        # Retry logic
        max_retries = 3
        for attempt in range(max_retries):
            try:
                r = requests.get(url, headers=headers, timeout=15)
                r.raise_for_status()
                payload = r.json()
                raw = payload.get("submission_calendar", "{}")
                data = json.loads(raw)
                out = {}
                for ts_str, cnt in data.items():
                    ts = int(ts_str)
                    day = datetime.utcfromtimestamp(ts).date()
                    out[day] = int(cnt)
                return out
            except requests.exceptions.RequestException as e:
                print(f"Error fetching calendar for {username} (attempt {attempt + 1}/{max_retries}): {e}")
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)
                    continue
            except Exception as e:
                print(f"Unexpected error fetching calendar for {username}: {e}")
                break
        return {}

    def calendars_to_frame(self, members: List[Dict[str, str]]) -> pd.DataFrame:
        rows = []
        min_d = max_d = None
        calendars = {}
        for m in members:
            uname = m["username"]
            name = m.get("name", uname)
            cal = self.fetch_submission_calendar(uname)
            calendars[uname] = {"name": name, "data": cal}
            for d in cal.keys():
                min_d = d if min_d is None or d < min_d else min_d
                max_d = d if max_d is None or d > max_d else max_d

        if min_d is None or max_d is None:
            return pd.DataFrame(columns=["name", "username", "date", "accepted"])

        full_days = pd.date_range(start=min_d, end=max_d, freq="D").date
        for m in members:
            uname = m["username"]
            name = m.get("name", uname)
            cal = calendars.get(uname, {}).get("data", {})
            for d in full_days:
                rows.append({
                    "name": name, "username": uname,
                    "date": pd.to_datetime(d),
                    "accepted": int(cal.get(d, 0)),
                })
        return pd.DataFrame(rows)
