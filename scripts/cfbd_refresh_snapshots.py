#!/usr/bin/env python3
"""
Command-line tool for refreshing CFBD data snapshots.

Fetches CFBD data and saves it as JSON snapshots to data/raw/cfbd/ for
deterministic pipeline runs. Snapshots include metadata (fetched_at, season,
endpoint_name, record_count, git_sha, cfbd_sdk_version).
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.append(str(SRC_DIR))
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

# Set up logging
LOGGER = logging.getLogger("cfbd_refresh_snapshots")
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

# CFBD imports
try:
    from cfbd_client.unified_client import UnifiedCFBDClient
except ImportError:
    LOGGER.error("Failed to import UnifiedCFBDClient. Falling back to direct cfbd import.")
    import cfbd
    UnifiedCFBDClient = None


def get_git_sha() -> Optional[str]:
    """Get current git SHA if available."""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
            check=True,
        )
        return result.stdout.strip()[:7]  # Short SHA
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None


def get_cfbd_sdk_version() -> Optional[str]:
    """Get CFBD SDK version if available."""
    try:
        import cfbd
        return getattr(cfbd, "__version__", None)
    except ImportError:
        return None


def create_metadata(
    season: int,
    endpoint_name: str,
    record_count: int,
    git_sha: Optional[str] = None,
    cfbd_sdk_version: Optional[str] = None,
) -> Dict[str, Any]:
    """Create metadata dictionary for snapshot."""
    return {
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "season": season,
        "endpoint_name": endpoint_name,
        "record_count": record_count,
        "git_sha": git_sha,
        "cfbd_sdk_version": cfbd_sdk_version,
    }


def save_snapshot(
    data: List[Dict[str, Any]],
    season: int,
    dataset_type: str,
    metadata: Dict[str, Any],
    output_dir: Path,
) -> None:
    """Save snapshot data and metadata to JSON files."""
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Save data
    data_file = output_dir / f"{dataset_type}_{season}.json"
    with open(data_file, "w") as f:
        json.dump(data, f, indent=2, default=str)
    LOGGER.info(f"✅ Saved {len(data)} records to {data_file}")
    
    # Save metadata
    metadata_file = output_dir / f"{dataset_type}_{season}.metadata.json"
    with open(metadata_file, "w") as f:
        json.dump(metadata, f, indent=2, default=str)
    LOGGER.info(f"✅ Saved metadata to {metadata_file}")


def fetch_games_snapshot(
    client: UnifiedCFBDClient,
    season: int,
    season_type: str,
    output_dir: Path,
) -> None:
    """Fetch and save games snapshot."""
    LOGGER.info(f"📡 Fetching {season_type} games for season {season}...")
    
    try:
        games = client.get_games(year=season, season_type=season_type)
        dataset_type = f"games_{season}_{season_type}"
        
        git_sha = get_git_sha()
        cfbd_version = get_cfbd_sdk_version()
        metadata = create_metadata(
            season=season,
            endpoint_name=f"games/{season_type}",
            record_count=len(games),
            git_sha=git_sha,
            cfbd_sdk_version=cfbd_version,
        )
        
        save_snapshot(games, season, dataset_type, metadata, output_dir)
    except Exception as e:
        LOGGER.error(f"❌ Failed to fetch {season_type} games: {e}")
        raise


def fetch_teams_snapshot(
    client: UnifiedCFBDClient,
    season: int,
    output_dir: Path,
) -> None:
    """Fetch and save teams snapshot."""
    LOGGER.info(f"📡 Fetching teams for season {season}...")
    
    try:
        # Use teams_api directly since get_teams() doesn't exist
        # Call API and convert response to dict list
        teams_response = client.teams_api.get_teams()
        teams = client._to_dict_list(teams_response)
        dataset_type = f"teams_{season}"
        
        git_sha = get_git_sha()
        cfbd_version = get_cfbd_sdk_version()
        metadata = create_metadata(
            season=season,
            endpoint_name="teams",
            record_count=len(teams),
            git_sha=git_sha,
            cfbd_sdk_version=cfbd_version,
        )
        
        save_snapshot(teams, season, dataset_type, metadata, output_dir)
    except Exception as e:
        LOGGER.error(f"❌ Failed to fetch teams: {e}")
        raise


def fetch_talent_snapshot(
    client: UnifiedCFBDClient,
    season: int,
    output_dir: Path,
) -> None:
    """Fetch and save team talent snapshot."""
    LOGGER.info(f"📡 Fetching team talent for season {season}...")
    
    try:
        talent = client.get_team_talent(year=season)
        dataset_type = f"talent_{season}"
        
        git_sha = get_git_sha()
        cfbd_version = get_cfbd_sdk_version()
        metadata = create_metadata(
            season=season,
            endpoint_name="team_talent",
            record_count=len(talent),
            git_sha=git_sha,
            cfbd_sdk_version=cfbd_version,
        )
        
        save_snapshot(talent, season, dataset_type, metadata, output_dir)
    except Exception as e:
        LOGGER.error(f"❌ Failed to fetch team talent: {e}")
        raise


def parse_args(argv: Optional[Sequence[str]] = None) -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Refresh CFBD data snapshots for deterministic pipeline runs."
    )
    parser.add_argument(
        "--season",
        type=int,
        required=True,
        help="Season year (e.g., 2025)",
    )
    parser.add_argument(
        "--refresh-all",
        action="store_true",
        help="Refresh all available datasets (games regular, games postseason, teams, talent)",
    )
    parser.add_argument(
        "--only",
        type=str,
        choices=["games_regular", "games_postseason", "teams", "talent"],
        help="Refresh only the specified dataset",
    )
    parser.add_argument(
        "--check-freshness",
        action="store_true",
        help="Check freshness of existing snapshots (stub - not implemented yet)",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=PROJECT_ROOT / "data" / "raw" / "cfbd",
        help="Directory for snapshot outputs (default: data/raw/cfbd)",
    )
    return parser.parse_args(argv)


def main(argv: Optional[Sequence[str]] = None) -> int:
    """Main entry point."""
    args = parse_args(argv)
    
    # Check for API key
    api_key = os.environ.get("CFBD_API_KEY")
    if not api_key:
        LOGGER.error("❌ CFBD_API_KEY environment variable not set")
        return 1
    
    # Initialize client
    try:
        client = UnifiedCFBDClient()
    except Exception as e:
        LOGGER.error(f"❌ Failed to initialize CFBD client: {e}")
        return 1
    
    # Handle check-freshness stub
    if args.check_freshness:
        LOGGER.warning("⚠️  --check-freshness is not yet implemented")
        return 0
    
    # Determine what to fetch
    datasets_to_fetch = []
    if args.refresh_all:
        datasets_to_fetch = ["games_regular", "games_postseason", "teams", "talent"]
    elif args.only:
        datasets_to_fetch = [args.only]
    else:
        LOGGER.error("❌ Must specify either --refresh-all or --only <dataset>")
        return 1
    
    # Fetch datasets
    try:
        for dataset in datasets_to_fetch:
            if dataset == "games_regular":
                fetch_games_snapshot(client, args.season, "regular", args.output_dir)
            elif dataset == "games_postseason":
                fetch_games_snapshot(client, args.season, "postseason", args.output_dir)
            elif dataset == "teams":
                fetch_teams_snapshot(client, args.season, args.output_dir)
            elif dataset == "talent":
                fetch_talent_snapshot(client, args.season, args.output_dir)
        
        LOGGER.info("✅ All snapshots refreshed successfully")
        return 0
    except Exception as e:
        LOGGER.error(f"❌ Failed to refresh snapshots: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())



