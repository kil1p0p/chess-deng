#!/usr/bin/env python3
"""
build_opening_winning_rates.py

Reads data/warehouse/games.parquet and produces:
  data/warehouse/opening_winning_rates.parquet

Columns:
  opening_name
  games
  wins
  win_percent
"""

import pandas as pd
from pathlib import Path

USERNAME = "AlekhSrivastava".lower()

def build_opening_stats(username: str) -> None:
    """
    Build opening winning rates for the given username.
    """
    project_root = Path(__file__).resolve().parent
    warehouse_dir = project_root / "data" / "warehouse" / username

    games_path = warehouse_dir / "games.parquet"
    out_path = warehouse_dir / "opening_winning_rates.parquet"

    if not games_path.exists():
        print(f"[ERROR] {games_path} not found. Run process_games.py first.")
        return

    df = pd.read_parquet(games_path)

    # Filter out rows with no opening data
    df_valid = df.dropna(subset=["opening_name"])

    # Group by opening
    agg = (
        df_valid.groupby("opening_name")
        .agg(
            games=("game_id", "count"),
            wins=("result_for_me", lambda s: (s == "win").sum()),
        )
        .reset_index()
    )

    # Compute win%
    agg["win_percent"] = agg["wins"] / agg["games"] * 100.0

    # Sort by number of games for consistency
    agg = agg.sort_values("games", ascending=False)

    # Save
    agg.to_parquet(out_path, index=False)

    print(f"[DONE] Wrote {len(agg)} rows to {out_path}")
    print(agg.to_string())


def main():
    build_opening_stats(USERNAME.lower())


if __name__ == "__main__":
    main()
