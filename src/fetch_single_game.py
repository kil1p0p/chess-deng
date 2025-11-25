#!/usr/bin/env python3
"""
fetch_single_game.py

Fetch a single game from local games.parquet file given a game URL.
"""

import pandas as pd
from pathlib import Path


def fetch_game_from_url(game_url: str, username: str = "alekhsrivastava") -> dict:
    """
    Fetch a single game from local games.parquet file given a game URL.
    
    Args:
        game_url: Chess.com game URL (e.g., https://www.chess.com/game/live/145613797338)
        username: Username whose games to search (default: alekhsrivastava)
    
    Returns:
        dict: Game data including PGN
    """
    # Extract game ID from URL
    # URL format: https://www.chess.com/game/live/145613797338
    game_id = game_url.strip().split("/")[-1]
    
    # Construct full game URL to match against game_id column
    full_url = f"https://www.chess.com/game/live/{game_id}"
    
    # Load games from parquet file
    warehouse_path = Path(__file__).parent / "data" / "warehouse" / username.lower() / "games.parquet"
    
    if not warehouse_path.exists():
        raise FileNotFoundError(f"Games file not found at {warehouse_path}. Please fetch and process games first.")
    
    df_games = pd.read_parquet(warehouse_path)
    
    # Search for the game by game_id
    matching_games = df_games[df_games["game_id"] == full_url]
    
    if matching_games.empty:
        raise ValueError(f"Game {game_id} not found in local database. Make sure you've fetched this game's data.")
    
    # Get the first matching game
    game_row = matching_games.iloc[0]
    
    # Return game data in a format similar to Chess.com API
    return {
        "pgn": game_row["pgn"],
        "url": game_row["game_id"],
        "white": {"username": game_row["opponent_username"] if game_row["color"] == "black" else username},
        "black": {"username": game_row["opponent_username"] if game_row["color"] == "white" else username},
        "time_class": game_row["time_class"],
        "time_control": game_row["time_control"],
        "end_time": game_row["end_time"],
        "rated": game_row["rated"],
        "result_for_me": game_row["result_for_me"],
        "my_rating": game_row["my_rating"],
        "opponent_rating": game_row["opponent_rating"],
        "color": game_row["color"]
    }


if __name__ == "__main__":
    # Test
    url = "https://www.chess.com/game/live/145613797338"
    game = fetch_game_from_url(url)
    print("Game found!")
    print(f"White: {game['white']['username']}")
    print(f"Black: {game['black']['username']}")
    print(f"Time class: {game['time_class']}")
