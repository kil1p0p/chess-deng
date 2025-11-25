#!/usr/bin/env python3
"""
process_games.py

Reads NDJSON chess.com game files from data/raw/ (created by fetch_games.py),
parses them into a clean tabular structure, and writes a single Parquet file:

  data/warehouse/games.parquet

Each row = one game, with fields like:
  - end_time, end_time_dt
  - color, result_for_me
  - my_rating, opponent_rating
  - time_control, time_class, rated
  - opening_eco, opening_name, opening_variation
  - moves_count
  - url, opponent_username, etc.
"""

import re
import json
import io
from pathlib import Path
from typing import Dict, Any, List, Optional

import pandas as pd
import chess.pgn


# 🔧 CONFIG: set this to your chess.com username (same as in fetch_games.py)
USERNAME = "AlekhSrivastava".lower()  # change if needed


def parse_result_tag(tag: Optional[str]) -> str:
    """
    Map chess.com 'result' tag for the player (win/lose/etc) into
    a simpler 'win' / 'loss' / 'draw' / 'other'.
    """
    if tag is None:
        return "other"

    tag = tag.lower()

    if tag == "win":
        return "win"

    # Loss-like outcomes
    loss_tags = {
        "checkmated",
        "timeout",
        "resigned",
        "lose",
        "abandoned",
        "stalling",
        "kingofthehill",
        "threecheck",
        "timevsinsufficient",
    }
    # Draw-like outcomes
    draw_tags = {
        "agreed",
        "repetition",
        "stalemate",
        "insufficient",
        "50move",
        "timevsinsufficient",  # sometimes classed as draw
    }

    if tag in loss_tags:
        return "loss"
    if tag in draw_tags:
        return "draw"

    return "other"


def parse_pgn(pgn_str: str) -> Dict[str, Any]:
    """
    Parse PGN with python-chess to extract:
      - ECO code
      - Opening name
      - Variation
      - Moves count
      - Termination (from PGN headers, if present)
    """
    if not pgn_str:
        return {
            "opening_eco": None,
            "opening_name": None,
            "opening_variation": None,
            "moves_count": None,
            "termination": None,
        }

    try:
        game = chess.pgn.read_game(io.StringIO(pgn_str))
        if game is None:
            return {
                "opening_eco": None,
                "opening_name": None,
                "opening_variation": None,
                "moves_count": None,
                "termination": None,
            }

        headers = game.headers
        eco = headers.get("ECO")
        opening = headers.get("Opening")
        variation = headers.get("Variation")
        termination = headers.get("Termination")

        # Count moves (full moves, not plies)
        moves_count = sum(1 for _ in game.mainline_moves())

        return {
            "opening_eco": eco,
            "opening_name": opening,
            "opening_variation": variation,
            "moves_count": moves_count,
            "termination": termination,
        }
    except Exception:
        # Fail gracefully; we don't want one bad PGN to kill the whole pipeline
        return {
            "opening_eco": None,
            "opening_name": None,
            "opening_variation": None,
            "moves_count": None,
            "termination": None,
        }


def parse_single_game(game: Dict[str, Any], username: str) -> Optional[Dict[str, Any]]:
    """
    Flatten a single chess.com game JSON into a dict of columns.

    Returns:
        dict with flattened fields, or None if it doesn't look like our game.
    """
    username = username.lower()

    # Determine which side is us
    white = game.get("white", {})
    black = game.get("black", {})

    white_name = str(white.get("username", "")).lower()
    black_name = str(black.get("username", "")).lower()

    if white_name == username:
        color = "white"
        me = white
        opp = black
    elif black_name == username:
        color = "black"
        me = black
        opp = white
    else:
        # This shouldn't happen when using the user's games API, but be defensive.
        # You could either skip or still record; we'll skip.
        return None

    my_result_raw = me.get("result")
    result_for_me = parse_result_tag(my_result_raw)

    # Chess.com core fields
    end_time = game.get("end_time")  # unix seconds
    time_control = game.get("time_control")  # e.g. "600" or "600+0"
    time_class = game.get("time_class")  # e.g. "rapid", "blitz"
    rated = game.get("rated", False)
    rules = game.get("rules")  # "chess", "chess960" etc
    url = game.get("url")
    pgn = game.get("pgn", "")

    # Ratings & usernames
    my_rating = me.get("rating")
    opp_rating = opp.get("rating")
    opp_username = opp.get("username")

    # PGN-based info
    pgn_info = parse_pgn(pgn)

    flat = {
        "game_id": url,  # unique enough for most use-cases
        "end_time": end_time,
        "time_control": time_control,
        "time_class": time_class,
        "rated": rated,
        "rules": rules,
        "color": color,
        "result_for_me": result_for_me,
        "my_rating": my_rating,
        "opponent_rating": opp_rating,
        "opponent_username": opp_username,
        "pgn": pgn,
        # PGN-derived
        "opening_eco": game.get("eco"),
        "opening_name": game.get("eco", "").split("/")[-1],
        "opening_variation": pgn_info["opening_variation"],
        "moves_count": pgn_info["moves_count"],
        "termination": pgn_info["termination"],
    }

    # opening is equal to the substring from start till the occurence of first digit.
    for i in range(len(flat.get("opening_name"))):
        if flat.get("opening_name")[i].isdigit():
            flat["opening_name"] = flat.get("opening_name")[0:i-1]
            break
    print(flat.get("opening_name"))

    return flat


def load_all_raw_games(raw_dir: Path, username: str) -> List[Dict[str, Any]]:
    """
    Iterate over all NDJSON files in raw_dir and parse games.
    """
    rows: List[Dict[str, Any]] = []

    ndjson_files = sorted(raw_dir.glob("games_*.ndjson"))
    if not ndjson_files:
        print(f"[WARN] No NDJSON files found in {raw_dir}. Did you run fetch_games.py?")
        return rows

    for path in ndjson_files:
        print(f"[INFO] Processing {path}")
        with path.open("r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    game_json = json.loads(line)
                except json.JSONDecodeError as e:
                    print(f"[WARN] Skipping corrupt JSON line in {path}: {e}")
                    continue

                flat = parse_single_game(game_json, username)
                if flat is not None:
                    rows.append(flat)

    print(f"[INFO] Parsed {len(rows)} games in total.")
    return rows


def process_all_games(username: str) -> None:
    """
    Process all raw games for the given username and save to Parquet.
    """
    project_root = Path(__file__).resolve().parent
    raw_dir = project_root / "data" / "raw" / username
    warehouse_dir = project_root / "data" / "warehouse" / username
    warehouse_dir.mkdir(parents=True, exist_ok=True)
    out_path = warehouse_dir / "games.parquet"

    rows = load_all_raw_games(raw_dir, username)
    if not rows:
        print("[WARN] No games parsed. Exiting.")
        return

    df = pd.DataFrame(rows)

    # Convert end_time (unix seconds) -> datetime in your local timezone (Asia/Kolkata)
    # Keep both UTC and localized forms for convenience.
    df["end_time_utc"] = pd.to_datetime(df["end_time"], unit="s", utc=True)
    df["end_time_local"] = df["end_time_utc"].dt.tz_convert("Asia/Kolkata")
    df["end_date"] = df["end_time_local"].dt.date
    df["end_hour"] = df["end_time_local"].dt.hour

    # Sort by time for convenience
    df = df.sort_values("end_time_utc").reset_index(drop=True)

    # Save to Parquet
    df.to_parquet(out_path, index=False)
    print(f"[DONE] Wrote {len(df)} games to {out_path}")


def main():
    if USERNAME == "your_chesscom_username":
        print("[ERROR] Please set USERNAME at the top of process_games.py.")
        return

    process_all_games(USERNAME.lower())


if __name__ == "__main__":
    main()
