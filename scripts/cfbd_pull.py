#!/usr/bin/env python3
"""Command-line pipeline for CFBD data ingestion and feature generation."""

from __future__ import annotations

import argparse
import json
import logging
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.append(str(SRC_DIR))
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

# CFBD imports moved to after argument parsing
# from cfbd_client.unified_client import UnifiedCFBDClient  # noqa: E402
# from features.cfbd_feature_engineering import (  # noqa: E402
#     CFBDFeatureEngineer,
#     FeatureEngineeringConfig,
# )
# from model_pack.utils.cfbd_advanced_metrics import (  # noqa: E402
#     AdvancedMetricsBuilder,
# )

# Set up logging with file handler
LOGGER = logging.getLogger("cfbd_pull")

# Create logs directory if it doesn't exist
logs_dir = Path(__file__).parent.parent / "logs"
logs_dir.mkdir(exist_ok=True)

# Configure logging with both file and console handlers
log_file = logs_dir / "cfbd_pull.log"
log_format = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")

# Create handlers
file_handler = logging.FileHandler(log_file, encoding="utf-8")
file_handler.setFormatter(log_format)

console_handler = logging.StreamHandler()
console_handler.setFormatter(log_format)

# Configure logging with formatted handlers
logging.basicConfig(level=logging.INFO, handlers=[file_handler, console_handler])


def parse_args(argv: Optional[Sequence[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Fetch CFBD data (REST) and build the 86-feature dataset."
    )
    parser.add_argument(
        "--season", type=int, required=True, help="Season year (e.g., 2025)"
    )
    parser.add_argument("--week", type=int, default=None, help="Optional week filter")
    parser.add_argument("--team", type=str, default=None, help="Optional team filter")
    parser.add_argument(
        "--with-plays",
        action="store_true",
        help="Fetch play-by-play for advanced metrics (slower, higher API usage).",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=PROJECT_ROOT / "outputs" / "cfbd_ingest",
        help="Directory for raw + processed outputs.",
    )
    parser.add_argument(
        "--use-snapshots",
        action="store_true",
        help="Read from local JSON snapshots first; don't hit network. Requires snapshots to exist.",
    )
    parser.add_argument(
        "--refresh",
        action="store_true",
        help="Force refresh snapshots first, then use them. Runs cfbd_refresh_snapshots.py before proceeding.",
    )
    return parser.parse_args(argv)


def load_snapshot(
    season: int, dataset_type: str, snapshot_dir: Path
) -> Optional[List[Dict[str, Any]]]:
    """
    Load snapshot data from local JSON file.

    Args:
        season: Season year
        dataset_type: Type of dataset (e.g., 'games_regular', 'games_postseason')
        snapshot_dir: Directory containing snapshots

    Returns:
        List of game records or None if snapshot doesn't exist
    """
    snapshot_file = snapshot_dir / f"{dataset_type}_{season}.json"
    if not snapshot_file.exists():
        return None

    try:
        with open(snapshot_file, "r") as f:
            data = json.load(f)
        LOGGER.info(f"📦 Loaded {len(data)} records from snapshot: {snapshot_file}")
        return data
    except Exception as e:
        LOGGER.warning(f"⚠️  Failed to load snapshot {snapshot_file}: {e}")
        return None


def fetch_games(
    *,
    client,  # UnifiedCFBDClient
    season: int,
    week: Optional[int],
    team: Optional[str],
    use_snapshots: bool = False,
    snapshot_dir: Optional[Path] = None,
) -> List[Dict[str, Any]]:
    """
    Fetch games data, optionally from snapshots.

    Args:
        client: UnifiedCFBDClient instance
        season: Season year
        week: Optional week filter
        team: Optional team filter
        use_snapshots: If True, prefer snapshots over API
        snapshot_dir: Directory containing snapshots

    Returns:
        List of game records
    """
    # Determine snapshot directory
    if snapshot_dir is None:
        snapshot_dir = PROJECT_ROOT / "data" / "raw" / "cfbd"

    # Try to load from snapshots if requested or if snapshots exist
    if use_snapshots or (snapshot_dir.exists() and not use_snapshots):
        # Determine which snapshot to load based on week
        # For simplicity, try regular season first, then postseason
        # In a real implementation, you might want to check week ranges
        dataset_types = ["games_regular", "games_postseason"]

        for dataset_type in dataset_types:
            snapshot_data = load_snapshot(season, dataset_type, snapshot_dir)
            if snapshot_data:
                # Apply filters if needed
                if week is not None:
                    snapshot_data = [g for g in snapshot_data if g.get("week") == week]
                if team is not None:
                    team_lower = team.lower()
                    snapshot_data = [
                        g
                        for g in snapshot_data
                        if (
                            g.get("home_team", "").lower() == team_lower
                            or g.get("away_team", "").lower() == team_lower
                        )
                    ]

                if snapshot_data:
                    LOGGER.info(f"✅ Using snapshot data: {len(snapshot_data)} games")
                    return snapshot_data

        # If use_snapshots is True and no snapshots found, error
        if use_snapshots:
            LOGGER.error("❌ --use-snapshots specified but snapshots not found")
            LOGGER.error(
                f"   Run: python scripts/cfbd_refresh_snapshots.py --season {season} --refresh-all"
            )
            raise SystemExit(
                "Snapshots not found. Run cfbd_refresh_snapshots.py first."
            )

    # Fall back to API
    LOGGER.info("🌐 Fetching games from CFBD API...")
    return client.get_games(year=season, week=week, team=team)


def fetch_lines(
    client,  # UnifiedCFBDClient
    *,
    season: int,
    weeks: Iterable[int],
) -> List[Dict[str, Any]]:
    snapshots: List[Dict[str, Any]] = []
    for wk in weeks:
        try:
            lines = client.get_lines(year=season, week=int(wk)) or []
            snapshots.extend(lines)
        except Exception as exc:  # pragma: no cover - network path
            LOGGER.warning("Unable to fetch lines for week %s: %s", wk, exc)
    return snapshots


def fetch_advanced_metrics(
    client,  # UnifiedCFBDClient
    games_df: pd.DataFrame,
    *,
    include_plays: bool,
) -> Dict[Any, Dict[str, Any]]:
    # Import here to make script resilient to dependency issues
    try:
        from model_pack.utils.cfbd_advanced_metrics import AdvancedMetricsBuilder
    except ImportError as e:
        LOGGER.error(f"Could not import AdvancedMetricsBuilder: {e}")
        return {}

    builder = AdvancedMetricsBuilder(
        api_client=client.api_client, season=int(games_df["season"].iloc[0])
    )
    plays_df = None
    if include_plays:
        records: List[Dict[str, Any]] = []
        for game_id in games_df["id"].dropna().unique():
            try:
                plays = client.plays_api.get_plays(game_id=int(game_id))
                for play in plays or []:
                    records.append(play.to_dict() if hasattr(play, "to_dict") else play)
            except Exception as exc:  # pragma: no cover - network path
                LOGGER.warning("Failed to fetch plays for %s: %s", game_id, exc)
        plays_df = pd.DataFrame(records) if records else None

    metrics = builder.build_metrics_for_games(games_df, plays_df)
    LOGGER.info("Advanced metrics collected for %d games", len(metrics))
    return metrics


def ensure_output_dir(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    return path


def main(argv: Optional[Sequence[str]] = None) -> None:
    try:
        args = parse_args(argv)

        LOGGER.info("=" * 70)
        LOGGER.info(f"CFBD Data Pull - Season {args.season}, Week {args.week}")
        LOGGER.info("=" * 70)
        LOGGER.info("START: Data pull initiated")

        # Handle --refresh flag: refresh snapshots first
        if args.refresh:
            LOGGER.info("🔄 Refreshing snapshots...")
            import subprocess

            refresh_script = PROJECT_ROOT / "scripts" / "cfbd_refresh_snapshots.py"
            if not refresh_script.exists():
                LOGGER.error(f"❌ Snapshot refresh script not found: {refresh_script}")
                raise SystemExit("Snapshot refresh script not found")

            result = subprocess.run(
                [
                    sys.executable,
                    str(refresh_script),
                    "--season",
                    str(args.season),
                    "--refresh-all",
                ],
                capture_output=True,
                text=True,
            )
            if result.returncode != 0:
                LOGGER.error(f"❌ Snapshot refresh failed: {result.stderr}")
                raise SystemExit("Snapshot refresh failed")
            LOGGER.info("✅ Snapshots refreshed")

        # Check API key only if not using snapshots exclusively
        if not args.use_snapshots:
            api_key = os.environ.get("CFBD_API_KEY")
            if not api_key:
                LOGGER.error("❌ CFBD_API_KEY environment variable is required")
                raise SystemExit("CFBD_API_KEY environment variable is required.")

        # Import CFBD dependencies only after argument parsing
        # Note: Still need client for feature engineering even if using snapshots
        try:
            from cfbd_client.unified_client import UnifiedCFBDClient
            from features.cfbd_feature_engineering import (
                CFBDFeatureEngineer,
                FeatureEngineeringConfig,
            )
        except ImportError as e:
            LOGGER.error(f"❌ CFBD dependencies not available: {e}")
            LOGGER.error(
                "Please ensure CFBD client and feature engineering modules are properly installed"
            )
            raise SystemExit("CFBD dependencies not available")

        # Initialize client (needed for feature engineering even if using snapshots)
        client = None
        if not args.use_snapshots:
            LOGGER.info("Initializing CFBD client...")
            client = UnifiedCFBDClient()
            LOGGER.info("✅ CFBD client initialized")
        else:
            # Still need client for feature engineering, but won't use it for fetching
            LOGGER.info(
                "Using snapshot mode - initializing minimal client for feature engineering..."
            )
            client = UnifiedCFBDClient()
            LOGGER.info("✅ Client initialized (snapshot mode)")

        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        run_dir = ensure_output_dir(args.output_dir / f"{args.season}_{timestamp}")

        snapshot_dir = PROJECT_ROOT / "data" / "raw" / "cfbd"
        LOGGER.info(f"Fetching games for season {args.season}, week {args.week}")
        raw_games = fetch_games(
            client=client,
            season=args.season,
            week=args.week,
            team=args.team,
            use_snapshots=args.use_snapshots,
            snapshot_dir=snapshot_dir,
        )
        LOGGER.info(f"✅ Fetched {len(raw_games)} games")

        LOGGER.info("Initializing feature engineer...")
        engineer = CFBDFeatureEngineer(
            FeatureEngineeringConfig(season=args.season, enforce_reference_schema=True)
        )

        LOGGER.info("Preparing games frame...")
        games_df = engineer.prepare_games_frame(
            raw_games,
            source="rest",
        )

        if games_df.empty:
            LOGGER.warning("No games available for requested filters.")
            return

        LOGGER.info("Fetching betting lines...")
        line_weeks = games_df["week"].dropna().unique().tolist()
        line_payload = fetch_lines(client, season=args.season, weeks=line_weeks)
        games_df = engineer.merge_spreads(games_df, line_payload)

        LOGGER.info("Building feature matrix...")
        metrics_by_game = fetch_advanced_metrics(
            client,
            games_df,
            include_plays=args.with_plays,
        )

        feature_frame = engineer.build_feature_frame(games_df, metrics_by_game)

        LOGGER.info("Saving outputs...")
        raw_path = run_dir / "games_rest.json"
        feature_path = run_dir / "feature_matrix.csv"
        metrics_path = run_dir / "advanced_metrics.json"

        with raw_path.open("w", encoding="utf-8") as handle:
            json.dump(raw_games, handle, indent=2, default=str)
        feature_frame.to_csv(feature_path, index=False)
        with metrics_path.open("w", encoding="utf-8") as handle:
            json.dump(metrics_by_game, handle, indent=2)

        LOGGER.info("Saved raw games -> %s", raw_path)
        LOGGER.info("Saved feature matrix -> %s", feature_path)
        LOGGER.info("Saved metrics snapshot -> %s", metrics_path)
        LOGGER.info("END: Data pull completed successfully")

    except Exception as e:
        LOGGER.error(f"❌ Data pull failed: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    main()
