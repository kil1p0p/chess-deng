#!/usr/bin/env python3
"""
fetch_games.py

Download all games for a given chess.com username and store them
as line-delimited JSON (NDJSON) files under data/raw/.

Directory structure:
  data/raw/
    games_YYYY_MM.ndjson

Each line in the file is a single game JSON object from chess.com API.
"""

import sys
import time
import json
from pathlib import Path
from typing import Optional, Dict, Any, List
from datetime import date

import requests


USERNAME = "AlekhSrivastava".lower()  # e.g. "audi0s1ave"

START_YEAR = 2025

BASE_URL = "https://api.chess.com/pub/player"

HEADERS = {
    "User-Agent": "chess-improvement-engine/0.1 (contact: nikhilundead@gmail.com)"
}


def fetch_month(username: str, year: int, month: int) -> Optional[Dict[str, Any]]:
    """
    Fetch games for a given user, year, and month from chess.com API.

    Returns:
        dict with games data if available, or None if no games / error that we skip.
    """
    url = f"{BASE_URL}/{username}/games/{year}/{month:02d}"
    print(f"[INFO] Fetching {url}")

    try:
        resp = requests.get(url, headers=HEADERS, timeout=15)
    except requests.RequestException as e:
        print(f"[ERROR] Request error for {year}-{month:02d}: {e}")
        return None

    if resp.status_code == 404:
        print(f"[INFO] No games or archive for {year}-{month:02d} (404).")
        return None

    if resp.status_code == 403:
        print(f"[WARN] 403 Forbidden for {year}-{month:02d}. "
              f"Check username and User-Agent, or try again later.")
        return None

    resp.raise_for_status()
    data = resp.json()
    games = data.get("games", [])
    if not games:
        print(f"[INFO] No games returned for {year}-{month:02d}.")
        return None

    return data


def month_file_path(raw_dir: Path, year: int, month: int) -> Path:
    """Return the NDJSON path for a given year-month."""
    return raw_dir / f"games_{year}_{month:02d}.ndjson"


def save_month_ndjson(raw_dir: Path, year: int, month: int, data: Dict[str, Any]) -> None:
    """
    Save games for a month as NDJSON: one JSON object per line.

    Each line is a single game (the object inside data["games"]).
    """
    raw_dir.mkdir(parents=True, exist_ok=True)
    path = month_file_path(raw_dir, year, month)

    games: List[Dict[str, Any]] = data.get("games", [])
    if not games:
        print(f"[INFO] No games to save for {year}-{month:02d}.")
        return

    with path.open("w", encoding="utf-8") as f:
        for g in games:
            f.write(json.dumps(g) + "\n")

    print(f"[INFO] Saved {len(games)} games to {path}")


def already_downloaded(raw_dir: Path, year: int, month: int) -> bool:
    """Check if NDJSON file for this month already exists and is non-empty."""
    path = month_file_path(raw_dir, year, month)
    return path.exists() and path.stat().st_size > 0


def fetch_games_for_user(username: str, start_year: int = START_YEAR, start_month: int = 1, end_year: Optional[int] = None, end_month: Optional[int] = None) -> None:
    """
    Fetch games for a given user from start_year/month to end_year/month.
    """
    project_root = Path(__file__).resolve().parent
    raw_dir = project_root / "data" / "raw" / username
    raw_dir.mkdir(parents=True, exist_ok=True)

    print(f"[INFO] Fetching games for user: {username}")
    print(f"[INFO] Saving NDJSON files under: {raw_dir}")

    today = date.today()
    if end_year is None:
        end_year = today.year
    if end_month is None:
        end_month = today.month if end_year == today.year else 12

    total_fetched = 0

    for year in range(start_year, end_year + 1):
        # Determine month range for this year
        first_m = start_month if year == start_year else 1
        last_m = end_month if year == end_year else 12
        
        # Cap at current month if we are in the current year
        if year == today.year:
            last_m = min(last_m, today.month)

        for month in range(first_m, last_m + 1):
            if already_downloaded(raw_dir, year, month):
                print(f"[SKIP] {year}-{month:02d} already downloaded.")
                continue

            data = fetch_month(username, year, month)
            if data is None:
                continue

            save_month_ndjson(raw_dir, year, month, data)
            total_fetched += len(data.get("games", []))

            # Be polite to the API
            time.sleep(0.5)

    print(f"[DONE] Finished. Total games fetched (approx): {total_fetched}")


def main():
    username = USERNAME
    if username == "your_chesscom_username":
        print(
            "[ERROR] Please edit fetch_games.py and set USERNAME to your "
            "actual chess.com username."
        )
        sys.exit(1)

    # Allow username override via CLI: python fetch_games.py someuser
    if len(sys.argv) >= 2:
        username = sys.argv[1].lower()
    
    fetch_games_for_user(username)


if __name__ == "__main__":
    main()
