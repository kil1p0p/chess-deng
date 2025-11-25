#!/usr/bin/env python3
"""
analyze_game_quality.py

Analyze your games like chess.com:
- Brilliant / Great / Good / Inaccuracy / Mistake / Blunder counts
- Per-move eval loss
- Accuracy score (0–100)
- Estimated game strength rating
"""

import io
from pathlib import Path
import chess
import chess.engine
import chess.pgn
import pandas as pd

# CONFIG — EDIT THESE
STOCKFISH = "/opt/homebrew/bin/stockfish"      # path to engine
USERNAME = "AlekhSrivastava".lower()                # your username
DEPTH = 18                                     # engine depth


def classify(eval_drop):
    """Classify move based on eval drop (pawns)."""
    # Positive = your move improved
    if eval_drop >= 0.30:
        return "brilliant"
    if eval_drop >= 0.10:
        return "great"
    if eval_drop >= -0.05:
        return "good"
    if eval_drop >= -0.15:
        return "inaccuracy"
    if eval_drop >= -0.30:
        return "mistake"
    return "blunder"


def analyze_single_game(pgn_str, me_white):
    engine = chess.engine.SimpleEngine.popen_uci(STOCKFISH)

    game = chess.pgn.read_game(io.StringIO(pgn_str))
    board = game.board()

    records = []

    for move in game.mainline_moves():
        side_to_move = board.turn
        is_my_move = (side_to_move == chess.WHITE and me_white) or (
            side_to_move == chess.BLACK and not me_white
        )

        # Eval BEFORE
        info_before = engine.analyse(board, chess.engine.Limit(depth=DEPTH))
        eval_before = info_before["score"].pov(chess.WHITE if me_white else chess.BLACK).score(mate_score=10000) / 100.0

        board.push(move)

        # Eval AFTER (only for your moves)
        info_after = engine.analyse(board, chess.engine.Limit(depth=DEPTH))
        eval_after = info_after["score"].pov(chess.WHITE if me_white else chess.BLACK).score(mate_score=10000) / 100.0

        if is_my_move:
            eval_drop = eval_after - eval_before
            category = classify(eval_drop)

            records.append({
                "eval_before": eval_before,
                "eval_after": eval_after,
                "eval_drop": eval_drop,
                "category": category,
            })

    engine.quit()
    return pd.DataFrame(records)


def compute_accuracy(df):
    """Compute accuracy score and estimated rating."""
    avg_loss = df[df["eval_drop"] < 0]["eval_drop"].abs().mean()
    if pd.isna(avg_loss):
        avg_loss = 0

    accuracy = max(0, 100 - (avg_loss * 15))
    rating_equiv = int(accuracy * 20 + 200)  # rough approximation

    return accuracy, rating_equiv


def main():
    # Load your processed games
    warehouse = Path("data/warehouse/AlekhSrivastava/games.parquet")
    games = pd.read_parquet(warehouse)

    # Pick ONE recent game to test
    g = games.sort_values("end_time_utc").iloc[-1]

    print("Analyzing game:", g["game_id"])

    df_moves = analyze_single_game(g["pgn"], me_white=(g["color"] == "white"))

    print("\nMove Classification:")
    print(df_moves["category"].value_counts())

    accuracy, rating_equiv = compute_accuracy(df_moves)

    print("\nAccuracy Score:", round(accuracy, 2))
    print("Estimated Game Strength Rating:", rating_equiv)


if __name__ == "__main__":
    main()
