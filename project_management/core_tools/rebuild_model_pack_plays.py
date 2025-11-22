"""Utilities to rebuild the model-pack plays file from starter-pack data."""

from __future__ import annotations

import argparse
import json
import sys
from ast import literal_eval
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Tuple

import pandas as pd


DEFAULT_STARTER_FILE = Path("starter_pack/data/2025_plays.csv")
DEFAULT_STARTER_DIR_TEMPLATE = Path("starter_pack/data/plays/{season}")
DEFAULT_OUTPUT = Path("model_pack/2025_plays.csv")

REQUIRED_SOURCE_COLUMNS = {
    "id",
    "gameId",
    "playNumber",
    "period",
    "clock",
    "yardline",
    "down",
    "distance",
    "playType",
    "playText",
    "scoring",
    "offense",
    "defense",
    "home",
    "away",
    "offenseScore",
    "defenseScore",
}


@dataclass
class TransformStats:
    plays: int
    games: int
    files: int


def _parse_clock(value) -> Tuple[str, float]:
    """Return a formatted mm:ss string and numeric seconds value for sorting."""
    if isinstance(value, dict):
        minutes = int(value.get("minutes", 0))
        seconds = int(value.get("seconds", 0))
    elif isinstance(value, str) and value.strip().startswith("{"):
        try:
            parsed = json.loads(value)
        except json.JSONDecodeError:
            try:
                parsed = literal_eval(value)
            except (ValueError, SyntaxError):
                parsed = {}
        minutes = int(parsed.get("minutes", 0))
        seconds = int(parsed.get("seconds", 0))
    else:
        # Already formatted (e.g. "14:55")
        try:
            minutes, seconds = value.split(":")
            minutes, seconds = int(minutes), int(seconds)
        except Exception:  # noqa: BLE001
            # Fallback to raw value
            return str(value), 0
    formatted = f"{minutes:02d}:{seconds:02d}"
    total_seconds = minutes * 60 + seconds
    return formatted, total_seconds


def _load_starter_pack_frames(path: Path, season: int) -> Tuple[pd.DataFrame, List[Path]]:
    """Load starter-pack plays data either from a single CSV or a directory of CSVs."""
    files: List[Path] = []
    if path.is_file():
        files = [path]
    elif path.is_dir():
        files = sorted(p for p in path.glob("*.csv") if p.is_file())
    else:
        fallback_dir = Path(f"starter_pack/data/plays/{season}")
        if fallback_dir.exists():
            files = sorted(p for p in fallback_dir.glob("*.csv") if p.is_file())
        else:
            raise FileNotFoundError(
                f"No starter-pack plays source found at {path} or {fallback_dir}"
            )

    if not files:
        raise FileNotFoundError(f"No CSV files located in {path}")

    frames = []
    for csv_path in files:
        df = pd.read_csv(csv_path)
        df["source_file"] = csv_path.name
        frames.append(df)

    combined = pd.concat(frames, ignore_index=True)
    return combined, files


def _validate_source_columns(df: pd.DataFrame) -> None:
    missing = REQUIRED_SOURCE_COLUMNS - set(df.columns)
    if missing:
        raise ValueError(
            "Starter-pack plays data is missing required columns: "
            + ", ".join(sorted(missing))
        )


def _derive_scores(row: pd.Series) -> Tuple[int, int]:
    """Return home_score, away_score for each play row."""
    home = row["home"]
    away = row["away"]
    offense = row["offense"]
    defense = row["defense"]
    offense_score = row.get("offenseScore")
    defense_score = row.get("defenseScore")

    if offense == home and defense == away:
        return offense_score, defense_score
    if offense == away and defense == home:
        return defense_score, offense_score
    # Fallback when offense/defense don't align with home/away (rare)
    return offense_score, defense_score


def transform_plays_to_model_pack(
    starter_pack_path: Path | str = DEFAULT_STARTER_FILE,
    output_path: Path | str = DEFAULT_OUTPUT,
    season: int = 2025,
) -> TransformStats:
    """Transform starter-pack play-by-play data into the model-pack schema."""
    starter_path = Path(starter_pack_path)
    output_path = Path(output_path)

    source_df, files = _load_starter_pack_frames(starter_path, season)
    _validate_source_columns(source_df)

    renamed = source_df.rename(
        columns={
            "id": "play_id",
            "gameId": "game_id",
            "yardline": "yard_line",
            "playType": "play_type",
            "playText": "text",
        }
    ).copy()

    # Parse clock columns for consistent formatting & sorting
    clock_results = renamed["clock"].apply(_parse_clock)
    renamed["clock"], renamed["clock_sort_seconds"] = zip(*clock_results)

    renamed["home_team"] = renamed["home"]
    renamed["away_team"] = renamed["away"]

    if "text" in renamed.columns:
        mask = renamed["text"].str.contains("Mock", case=False, na=False)
        removed = int(mask.sum())
        if removed:
            print(f"Filtered {removed} mock placeholder plays")
        renamed = renamed[~mask].copy()

    score_pairs = renamed.apply(_derive_scores, axis=1, result_type="expand")
    renamed["home_score"] = score_pairs[0]
    renamed["away_score"] = score_pairs[1]

    desired_columns = [
        "game_id",
        "play_id",
        "period",
        "clock",
        "yard_line",
        "down",
        "distance",
        "play_type",
        "scoring",
        "home_score",
        "away_score",
        "text",
        "home_team",
        "away_team",
    ]

    missing_output_cols = [col for col in desired_columns if col not in renamed.columns]
    if missing_output_cols:
        raise ValueError(f"Unable to construct columns: {missing_output_cols}")

    # Sort chronologically within each game
    sorted_df = renamed.sort_values(
        by=["game_id", "period", "clock_sort_seconds", "playNumber"],
        ascending=[True, True, False, True],
        kind="mergesort",
    )
    final_df = sorted_df[desired_columns].reset_index(drop=True)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    final_df.to_csv(output_path, index=False)

    stats = TransformStats(
        plays=len(final_df),
        games=final_df["game_id"].nunique(),
        files=len(files),
    )
    print(
        f"✓ Saved {stats.plays:,} plays "
        f"from {stats.games} games ({stats.files} source files) to {output_path}"
    )
    return stats


def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Rebuild model-pack plays CSV from starter-pack data."
    )
    parser.add_argument(
        "--starter-pack-path",
        default=str(DEFAULT_STARTER_FILE),
        help="Path to starter-pack plays CSV or directory (defaults to 2025 aggregated file or plays directory).",
    )
    parser.add_argument(
        "--season",
        type=int,
        default=2025,
        help="Season to use when falling back to the plays directory (default: 2025).",
    )
    parser.add_argument(
        "--output-path",
        default=str(DEFAULT_OUTPUT),
        help="Destination CSV for model-pack plays (default: model_pack/2025_plays.csv).",
    )
    return parser


def main(argv: Iterable[str] | None = None) -> int:
    parser = _build_arg_parser()
    args = parser.parse_args(list(argv) if argv is not None else None)
    try:
        transform_plays_to_model_pack(
            starter_pack_path=args.starter_pack_path,
            output_path=args.output_path,
            season=args.season,
        )
    except Exception as exc:  # noqa: BLE001
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

