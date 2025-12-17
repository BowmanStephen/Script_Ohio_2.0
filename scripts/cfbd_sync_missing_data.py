#!/usr/bin/env python3
"""
Sync missing CFBD data based on a previously generated manifest.

- Fetches missing weeks 13+ (or any missing weeks) for:
  - game team stats
  - advanced boxscore stats
  - plays
- Fetches postseason games and appends them to games.csv (optional)
- Fetches missing gameId rows for game_stats and advanced_game_stats

Prefers src/cfbd_client/unified_client.py (UnifiedCFBDClient) if importable;
otherwise uses direct HTTP via requests.

This script is intentionally defensive because endpoint payload shapes can differ
between CFBD API versions and between your existing CSV schemas.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

import pandas as pd

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.append(str(SRC_DIR))
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def token_from_env() -> str | None:
    return (
        os.getenv("CFBD_API_TOKEN")
        or os.getenv("CFBD_API_KEY")
        or os.getenv("CFBD_TOKEN")
    )


@dataclass
class CFBDTransport:
    get_json: Callable[[str, dict[str, Any] | None], Any]


def build_transport(base_url: str) -> CFBDTransport:
    """
    Returns a transport with signature get_json(path, params) -> JSON.
    Tries UnifiedCFBDClient first, then falls back to requests.
    """
    # 1) UnifiedCFBDClient (best: respects your caching/rate limiting)
    try:
        from src.cfbd_client.unified_client import UnifiedCFBDClient

        client = UnifiedCFBDClient()

        # UnifiedCFBDClient has specific methods, so we create a wrapper
        def _get_json(path: str, params: dict[str, Any] | None = None) -> Any:
            if params is None:
                params = {}

            # Map common endpoints to UnifiedCFBDClient methods
            if path == "/games" or path == "games":
                season_type = params.get("seasonType", params.get("season_type", "regular"))
                return client.get_games(
                    year=params.get("year", params.get("season", 2025)),
                    week=params.get("week"),
                    season_type=season_type,
                    team=params.get("team"),
                )
            elif path == "/plays" or path == "plays":
                # Use plays_api directly
                game_id = params.get("gameId") or params.get("game_id")
                if game_id:
                    try:
                        plays = client.plays_api.get_plays(game_id=int(game_id))
                        return client._to_dict_list(plays)
                    except Exception as e:
                        print(f"Warning: get_plays failed for gameId {game_id}: {e}")
                        return []
                # For week-based plays, we need to use the API directly
                # Fall through to requests fallback
                pass
            elif path == "/games/teams" or path == "games/teams":
                # This endpoint isn't directly exposed, fall through to requests
                pass
            elif path == "/game/box/advanced" or path == "game/box/advanced":
                # This endpoint isn't directly exposed, fall through to requests
                pass

            # For endpoints not directly supported, fall through to requests
            raise NotImplementedError(f"Endpoint {path} not directly supported by UnifiedCFBDClient")

        # Try to use it, but fall back if methods don't match
        try:
            # Test with a simple call
            _get_json("/games", {"year": 2025, "seasonType": "regular"})
            return CFBDTransport(get_json=_get_json)
        except Exception:
            # Fall through to requests
            pass
    except ImportError:
        pass
    except Exception as e:
        print(f"UnifiedCFBDClient available but test failed: {e}, falling back to requests")

    # 2) requests fallback
    tok = token_from_env()
    if not tok:
        raise RuntimeError(
            "No CFBD token found. Set CFBD_API_TOKEN or CFBD_API_KEY in your environment."
        )

    import requests

    def _get_requests(path: str, params: dict[str, Any] | None = None) -> Any:
        url = base_url.rstrip("/") + "/" + path.lstrip("/")
        headers = {"Authorization": f"Bearer {tok}"}
        resp = requests.get(url, headers=headers, params=params, timeout=120)
        resp.raise_for_status()
        return resp.json()

    return CFBDTransport(get_json=_get_requests)


def append_preserving_schema(csv_path: Path, new_df: pd.DataFrame) -> None:
    """
    Append rows to an existing CSV, preserving its column set/order.
    If the file doesn't exist, writes the new_df as-is.
    """
    csv_path.parent.mkdir(parents=True, exist_ok=True)

    if not csv_path.exists():
        new_df.to_csv(csv_path, index=False)
        return

    existing = pd.read_csv(csv_path, nrows=0)
    cols = list(existing.columns)

    # Keep only existing cols; fill missing columns with NA
    aligned = new_df.copy()
    for c in cols:
        if c not in aligned.columns:
            aligned[c] = pd.NA
    aligned = aligned[cols]

    # Append without header
    aligned.to_csv(csv_path, mode="a", header=False, index=False)


def df_from_games_teams_payload(payload: Any) -> pd.DataFrame:
    """
    Normalizes CFBD /games/teams response into a row-per-team table.

    Payload shapes observed historically:
    - list[ { id/gameId, teams: [ {school,...,stats: [...] } ] } ]
    - list[ { ...flat... } ]  (rare)
    """
    if payload is None:
        return pd.DataFrame()

    if isinstance(payload, list) and payload and isinstance(payload[0], dict):
        # If entries have "teams", flatten that list and carry gameId/id fields
        rows: list[dict[str, Any]] = []
        for item in payload:
            game_id = item.get("id") or item.get("gameId") or item.get("game_id")
            teams = item.get("teams")
            if isinstance(teams, list):
                for t in teams:
                    r = {"game_id": game_id}  # Use game_id to match your CSV schema
                    if isinstance(t, dict):
                        # flatten basic fields
                        for k, v in t.items():
                            if k == "stats" and isinstance(v, list):
                                # stats list often: [{category, stat}, ...]
                                # Convert to columns like stat_<category>
                                for s in v:
                                    if (
                                        isinstance(s, dict)
                                        and "category" in s
                                        and "stat" in s
                                    ):
                                        col = f"stat_{s['category']}"
                                        r[col] = s["stat"]
                            else:
                                r[k] = v
                    rows.append(r)
            else:
                # fallback: just keep item as a row
                rows.append(item)
        return pd.json_normalize(rows)

    return pd.json_normalize(payload)


def df_from_advanced_box_payload(game_id: int, payload: Any) -> pd.DataFrame:
    """
    Normalizes CFBD /game/box/advanced response into a row-per-team table.
    Typical payload includes a "teams" array.
    """
    if payload is None:
        return pd.DataFrame()

    if isinstance(payload, dict) and isinstance(payload.get("teams"), list):
        rows: list[dict[str, Any]] = []
        for t in payload["teams"]:
            if not isinstance(t, dict):
                continue
            r = {"gameId": game_id}  # Use gameId to match your CSV schema
            # Flatten deeply; keep team.school if present
            flat = pd.json_normalize(t).to_dict(orient="records")[0]
            r.update(flat)
            rows.append(r)
        return pd.DataFrame(rows)

    # Fallback: store the whole payload as a single row
    df = pd.json_normalize(payload)
    if not df.empty and "gameId" not in df.columns:
        df.insert(0, "gameId", game_id)
    return df


def sync_postseason_games(
    t: CFBDTransport,
    season: int,
    games_csv_path: Path,
    dry_run: bool,
) -> int:
    try:
        payload = t.get_json("/games", {"year": season, "seasonType": "postseason"})
    except NotImplementedError:
        # Fall back to direct HTTP
        import requests
        tok = token_from_env()
        if not tok:
            return 0
        base_url = os.getenv("CFBD_BASE_URL") or os.getenv("CFBD_HOST", "production")
        if base_url == "next":
            base_url = "https://apinext.collegefootballdata.com"
        elif base_url == "production":
            base_url = "https://api.collegefootballdata.com"
        url = base_url.rstrip("/") + "/games"
        headers = {"Authorization": f"Bearer {tok}"}
        resp = requests.get(
            url, headers=headers, params={"year": season, "seasonType": "postseason"}, timeout=120
        )
        resp.raise_for_status()
        payload = resp.json()

    df = pd.json_normalize(payload)
    if df.empty:
        return 0

    if games_csv_path.exists():
        existing = pd.read_csv(games_csv_path)
        # Best-effort id col detection
        id_col = "id" if "id" in existing.columns else ("gameId" if "gameId" in existing.columns else "game_id")

        if id_col in existing.columns:
            existing_ids = set(
                pd.to_numeric(existing[id_col], errors="coerce").dropna().astype(int).tolist()
            )
        else:
            existing_ids = set()

        # Figure out id column in df
        df_id_col = "id" if "id" in df.columns else ("gameId" if "gameId" in df.columns else None)
        if not df_id_col:
            return 0

        df[df_id_col] = pd.to_numeric(df[df_id_col], errors="coerce")
        df_new = df[df[df_id_col].notna()].copy()
        df_new[df_id_col] = df_new[df_id_col].astype(int)
        df_new = df_new[~df_new[df_id_col].isin(existing_ids)]
    else:
        df_new = df

    if df_new.empty:
        return 0

    if dry_run:
        return len(df_new)

    # Preserve existing schema if games.csv exists
    append_preserving_schema(games_csv_path, df_new)
    return len(df_new)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--manifest",
        type=Path,
        default=Path("data/cfbd/2025/manifest.json"),
    )
    parser.add_argument("--season", type=int, default=2025)
    parser.add_argument(
        "--base-url",
        type=str,
        default=None,
        help="CFBD API base URL. Auto-detected from CFBD_HOST env var if not set.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Compute what would be fetched/written without modifying files.",
    )
    parser.add_argument(
        "--update-games-csv",
        action="store_true",
        help="If set, will append postseason games into starter_pack/data/games.csv.",
    )
    parser.add_argument(
        "--sleep-seconds",
        type=float,
        default=0.17,  # Match your 6 req/sec rate limit
        help="Polite delay between API calls if using requests fallback.",
    )
    args = parser.parse_args()

    # Determine base URL
    if args.base_url is None:
        host_env = os.getenv("CFBD_HOST", "production").lower()
        if host_env == "next":
            args.base_url = "https://apinext.collegefootballdata.com"
        else:
            args.base_url = "https://api.collegefootballdata.com"

    manifest = load_json(args.manifest)
    starter_dir = Path(manifest["starter_data_dir"])

    t = build_transport(args.base_url)

    # Paths (existing)
    games_csv = starter_dir / "games.csv"
    game_stats_csv = starter_dir / "game_stats" / f"{args.season}.csv"
    adv_game_stats_csv = starter_dir / "advanced_game_stats" / f"{args.season}.csv"
    plays_dir = starter_dir / "plays" / str(args.season)

    datasets = {d["name"]: d for d in manifest["datasets"]}

    # 1) Optionally bring in postseason games
    if args.update_games_csv:
        n = sync_postseason_games(
            t=t,
            season=args.season,
            games_csv_path=games_csv,
            dry_run=args.dry_run,
        )
        print(f"✅ Postseason games appended to games.csv: {n} (dry_run={args.dry_run})")

    # Reload games index (so missing weeks/postseason can be derived downstream)
    if games_csv.exists():
        games_df = pd.read_csv(games_csv)
        gid_col = "id" if "id" in games_df.columns else ("gameId" if "gameId" in games_df.columns else "game_id")
        if gid_col not in games_df.columns:
            raise RuntimeError("Could not find a gameId column in games.csv after reload.")
        all_game_ids = set(
            pd.to_numeric(games_df[gid_col], errors="coerce").dropna().astype(int).tolist()
        )
    else:
        all_game_ids = set()

    # 2) Sync missing game team stats by missing gameId
    missing_game_stats_ids = set(datasets.get("game_stats", {}).get("missing_game_ids", []))
    if missing_game_stats_ids:
        rows_written = 0
        for game_id in sorted(missing_game_stats_ids):
            try:
                # Try UnifiedCFBDClient first, then fall back to direct HTTP
                try:
                    payload = t.get_json("/games/teams", {"year": args.season, "gameId": game_id})
                except (NotImplementedError, AttributeError):
                    # Fall back to direct HTTP
                    import requests
                    tok = token_from_env()
                    if not tok:
                        continue
                    url = args.base_url.rstrip("/") + "/games/teams"
                    headers = {"Authorization": f"Bearer {tok}"}
                    resp = requests.get(url, headers=headers, params={"year": args.season, "gameId": game_id}, timeout=120)
                    resp.raise_for_status()
                    payload = resp.json()

                df = df_from_games_teams_payload(payload)
                if df.empty:
                    continue

                # Ensure a game_id column exists (to match your CSV schema)
                if "game_id" not in df.columns:
                    if "gameId" in df.columns:
                        df = df.rename(columns={"gameId": "game_id"})
                    elif "id" in df.columns:
                        df = df.rename(columns={"id": "game_id"})
                    else:
                        df.insert(0, "game_id", game_id)

                if args.dry_run:
                    rows_written += len(df)
                else:
                    append_preserving_schema(game_stats_csv, df)
                    rows_written += len(df)

                time.sleep(args.sleep_seconds)
            except Exception as e:
                print(f"⚠️  Failed to fetch game_stats for gameId {game_id}: {e}")
                continue

        print(
            f"✅ game_stats: fetched missing gameIds={len(missing_game_stats_ids)}, "
            f"appended rows={rows_written} (dry_run={args.dry_run})"
        )
    else:
        print("ℹ️  game_stats: no missing gameIds in manifest.")

    # 3) Sync missing advanced game stats by missing gameId
    missing_adv_ids = set(datasets.get("advanced_game_stats", {}).get("missing_game_ids", []))
    if missing_adv_ids:
        rows_written = 0
        for game_id in sorted(missing_adv_ids):
            try:
                # Try UnifiedCFBDClient first, then fall back to direct HTTP
                try:
                    payload = t.get_json("/game/box/advanced", {"year": args.season, "gameId": game_id})
                except (NotImplementedError, AttributeError):
                    # Fall back to direct HTTP
                    import requests
                    tok = token_from_env()
                    if not tok:
                        continue
                    url = args.base_url.rstrip("/") + "/game/box/advanced"
                    headers = {"Authorization": f"Bearer {tok}"}
                    resp = requests.get(url, headers=headers, params={"year": args.season, "gameId": game_id}, timeout=120)
                    resp.raise_for_status()
                    payload = resp.json()

                df = df_from_advanced_box_payload(game_id, payload)
                if df.empty:
                    continue

                if args.dry_run:
                    rows_written += len(df)
                else:
                    append_preserving_schema(adv_game_stats_csv, df)
                    rows_written += len(df)

                time.sleep(args.sleep_seconds)
            except Exception as e:
                print(f"⚠️  Failed to fetch advanced_game_stats for gameId {game_id}: {e}")
                continue

        print(
            f"✅ advanced_game_stats: fetched missing gameIds={len(missing_adv_ids)}, "
            f"appended rows={rows_written} (dry_run={args.dry_run})"
        )
    else:
        print("ℹ️  advanced_game_stats: no missing gameIds in manifest.")

    # 4) Sync missing plays weeks (regular + postseason if desired)
    plays_missing_weeks = datasets.get("plays", {}).get("missing_weeks", [])
    if plays_missing_weeks:
        plays_dir.mkdir(parents=True, exist_ok=True)
        written_files = 0
        for week in plays_missing_weeks:
            try:
                # For plays by week, use direct HTTP (UnifiedCFBDClient doesn't expose this easily)
                import requests
                tok = token_from_env()
                if not tok:
                    continue
                url = args.base_url.rstrip("/") + "/plays"
                headers = {"Authorization": f"Bearer {tok}"}
                resp = requests.get(
                    url,
                    headers=headers,
                    params={"year": args.season, "week": int(week), "seasonType": "regular"},
                    timeout=120,
                )
                resp.raise_for_status()
                payload = resp.json()
                df = pd.json_normalize(payload)
                if df.empty:
                    continue

                out = plays_dir / f"regular_{int(week):02d}_plays.csv"
                if args.dry_run:
                    written_files += 1
                else:
                    df.to_csv(out, index=False)
                    written_files += 1

                time.sleep(args.sleep_seconds)
            except Exception as e:
                print(f"⚠️  Failed to fetch plays for week {week}: {e}")
                continue

        print(
            f"✅ plays: fetched missing weeks={len(plays_missing_weeks)}, "
            f"wrote files={written_files} (dry_run={args.dry_run})"
        )
    else:
        print("ℹ️  plays: no missing weeks in manifest.")

    print("\n✅ Done. Re-run the audit script to regenerate manifest/report.")


if __name__ == "__main__":
    main()
