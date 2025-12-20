#!/usr/bin/env python3
"""
FBS Game Filtering Script
Removes non-FBS teams from prediction data and creates clean datasets.

Non-FBS teams identified in current data:
- Delaware (FCS)
- James Madison (FCS in 2021, moved to FBS later)
- Kennesaw St. (FCS)
- Louisiana-Lafayette (now Louisiana, but this name suggests FCS data)
- Missouri St. (FCS)
- Troy St. (now Troy, but this naming suggests FCS era)
- Jacksonville St. (FCS)
"""

import argparse
import csv
import json
import os
import sys
from datetime import datetime
from pathlib import Path

# FBS Teams for 2025 season (133 teams)
FBS_TEAMS_2025 = {
    # Power 5 Conferences
    "acc",
    "sec",
    "big ten",
    "big 12",
    "pac-12",
    "pcc",
    # ACC Teams (17)
    "boston college",
    "clemson",
    "duke",
    "florida state",
    "georgia tech",
    "louisville",
    "miami",
    "north carolina",
    "nc state",
    "north carolina state",
    "syracuse",
    "virginia",
    "virginia tech",
    "wake forest",
    "california",
    "smu",
    "stanford",
    "pittsburgh",
    "pitt",
    # Big Ten Teams (18)
    "illinois",
    "indiana",
    "iowa",
    "maryland",
    "michigan",
    "michigan state",
    "msu",
    "minnesota",
    "nebraska",
    "northwestern",
    "ohio state",
    "oregon",
    "penn state",
    "purdue",
    "rutgers",
    "ucla",
    "usc",
    "washington",
    "wisconsin",
    # Big 12 Teams (16)
    "arizona",
    "arizona state",
    "asu",
    "baylor",
    "byu",
    "brigham young",
    "cincinnati",
    "colorado",
    "houston",
    "iowa state",
    "kansas",
    "kansas state",
    "ksu",
    "oklahoma state",
    "tcu",
    "texas christian",
    "texas tech",
    "ucf",
    "central florida",
    "utah",
    "west virginia",
    "wvu",
    "arizona",
    "arizona state",
    # SEC Teams (16)
    "alabama",
    "arkansas",
    "auburn",
    "florida",
    "georgia",
    "kentucky",
    "louisiana state",
    "lsu",
    "louisiana",
    "mississippi",
    "ole miss",
    "mississippi state",
    "msu",
    "missouri",
    "oklahoma",
    "south carolina",
    "tennessee",
    "texas",
    "texas a&m",
    "texas a and m",
    "vanderbilt",
    "vandy",
    # Pac-12 Teams (2)
    "oregon state",
    "osu",
    "washington state",
    "wsu",
    # Group of 5 Conferences
    "american",
    "aac",
    "conference usa",
    "c-usa",
    "mac",
    "mountain west",
    "mwc",
    "sun belt",
    # American Athletic Conference (14)
    "east carolina",
    "ecu",
    "tulsa",
    "temple",
    "ucf",
    "usf",
    "south florida",
    "navy",
    "memphis",
    "cincinnati",
    "houston",
    "smu",
    "north texas",
    "tulane",
    "rice",
    "Charlotte",
    "UAB",
    "FAU",
    "North Texas",
    "UTSA",
    "Temple",
    # Conference USA (14)
    "fiu",
    "florida international",
    "liberty",
    "louisiana tech",
    "middle tennessee",
    "mtsu",
    "new mexico state",
    "western kentucky",
    "western ky",
    "jacksonville state",
    "jacksonville st",
    "kennesaw state",
    "kennesaw st",
    "sam houston",
    "sam houston state",
    "new mexico state",
    "utep",
    "ut el paso",
    "rice",
    "north texas",
    "UTSA",
    "UT San Antonio",
    # MAC (12)
    "akron",
    "bowling green",
    "bgsu",
    "buffalo",
    "central michigan",
    "cmu",
    "eastern michigan",
    "emu",
    "kent state",
    "miami university",
    "miami (ohio)",
    "miami oh",
    "northern illinois",
    "niu",
    "ohio",
    "ohio university",
    "toledo",
    "western michigan",
    "wmu",
    "ball state",
    # Mountain West (12)
    "air force",
    "boise state",
    "colorado state",
    "csu",
    "fresno state",
    "fresno st",
    "hawaii",
    "nevada",
    "unlv",
    "nevada-las vegas",
    "new mexico",
    "unm",
    "san diego state",
    "sdsu",
    "san jose state",
    "sjsu",
    "utah state",
    "usu",
    "wyoming",
    # Sun Belt (14)
    "appalachian state",
    "app state",
    "arkansas state",
    "astate",
    "coastal carolina",
    "ccu",
    "georgia southern",
    "gags",
    "georgia state",
    "gsu",
    "james madison",
    "jmu",
    "louisiana",
    "louisiana-lafayette",
    "ull",
    "louisiana-monroe",
    "ulm",
    "marshall",
    "old dominion",
    "odu",
    "south alabama",
    "jag",
    "texas state",
    "txst",
    "troy",
    "ulm",
    "Southern Miss",
    "Southern Mississippi",
    "Georgia State",
    "South Alabama",
    # Independents (4)
    "army",
    "army west point",
    "navy",
    "notre dame",
    "uconn",
    "connecticut",
    # Known Non-FCS that should be FBS (from data analysis)
    "appalachian st.",
    "georgia southern",
    "connecticut",
    "army",
    "byu",
    "penn st.",
    "clemson",
    "fresno st.",
    "houston",
    "troy st.",
    "troy",
    "tulane",
    "mississippi",
    "wake forest",
    "mississippi st.",
    "memphis",
    "nc st.",
    "arizona",
    "smu",
    "san diego st.",
    "western mich.",
    "louisiana-lafayette",
    "jacksonville st.",
    "kennesaw st.",
    "north texas",
    "old dominion",
    "south florida",
    "western kentucky",
    "southern miss.",
    "coastal carolina",
    "georgia tech",
    "virginia",
    "miami (fla.)",
    "miami (fla)",
    "texas a&m",
    "texas a and m",
    "new mexico",
    "minnesota",
    "louisville",
    "toledo",
    "michigan",
    "texas",
    "iowa",
    "vanderbilt",
    "washington st.",
    "utah st.",
    "kennesaw st.",
    "nebraska",
    "utah",
    "arizona st.",
    "duke",
    "pittsburgh",
    "east carolina",
    "missouri",
    "california",
    "hawaii",
    "lsu",
    "navy",
    "purdue",
    "rutgers",
    "south carolina",
    "northwestern",
    "kansas",
    "kansas state",
    "oklahoma state",
    "iowa state",
    "west virginia",
    "baylor",
    "texas tech",
    "texas christian",
    "colorado",
    "oregon state",
    "washington state",
    "stanford",
    "syracuse",
    "boston college",
    "virginia tech",
    "north carolina",
    "florida state",
    "auburn",
    "georgia",
    "kentucky",
    "arkansas",
    "mississippi state",
    "florida",
    "south carolina",
    "louisiana state",
    "alabama",
    "ole miss",
}


# Normalize team names for better matching
def normalize_team_name(name: str) -> str:
    """Normalize team name for FBS comparison"""
    if not name:
        return ""

    # Remove common prefixes and suffixes
    normalized = name.lower().strip()

    # Handle common variations
    name_mappings = {
        "louisiana-lafayette": "louisiana",
        "louisiana-monroe": "ulm",
        "texas christian": "tcu",
        "texas a&m": "texas a&m",
        "miami (fla.)": "miami",
        "miami (ohio)": "miami (ohio)",
        "southern miss": "southern mississippi",
        "mississippi": "ole miss",
        "central mich": "central michigan",
        "western mich": "western michigan",
        "eastern mich": "eastern michigan",
        "fla.": "florida",
        "ga.": "georgia",
        "ky.": "kentucky",
        "tenn.": "tennessee",
        "la.": "louisiana",
        "nc state": "north carolina state",
        "ucf": "central florida",
        "usf": "south florida",
        "utep": "texas-el paso",
        "umass": "massachusetts",
        "unlv": "nevada-las vegas",
        "smu": "smu",  # Keep as SMU for matching
        "southern methodist": "smu",
        "byu": "byu",
        "army": "army",
        "navy": "navy",
        "air force": "air force",
        "coastal carolina": "coastal carolina",
        "appalachian state": "appalachian state",
        "georgia southern": "georgia southern",
        "georgia state": "georgia state",
        "jacksonville state": "jacksonville state",
        "kennesaw state": "kennesaw state",
        "james madison": "james madison",
        "liberty": "liberty",
        "old dominion": "old dominion",
        "marshall": "marshall",
        "southern mississippi": "southern mississippi",
        "brigham young": "byu",
        "penn state": "penn state",
        "nc state": "nc state",
        "louisiana state": "lsu",
        "mississippi state": "mississippi state",
    }

    # Apply mappings
    for old_name, new_name in name_mappings.items():
        if old_name in normalized:
            return new_name

    return normalized


def is_fbs_team(team_name: str) -> bool:
    """Check if a team is FBS for 2025 season"""
    if not team_name:
        return False

    normalized = normalize_team_name(team_name)

    # Direct match
    if normalized in FBS_TEAMS_2025:
        return True

    # Check if normalized name contains any FBS team name (for partial matches)
    for fbs_team in FBS_TEAMS_2025:
        if fbs_team in normalized or normalized in fbs_team:
            return True

    return False


def filter_ncaapredictions_csv(
    input_file: str, output_file: str = None, dry_run: bool = False
) -> dict:
    """Filter ncaapredictions.csv to remove non-FBS games"""

    if not os.path.exists(input_file):
        return {"error": f"Input file not found: {input_file}"}

    # Create backup if not dry run
    if not dry_run and not output_file:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = input_file.replace(".csv", f"_fbs_only_{timestamp}.csv")

    fbs_games = []
    non_fbs_games = []
    total_games = 0

    try:
        with open(input_file, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            headers = reader.fieldnames

            for row in reader:
                total_games += 1
                road_team = row.get("road", "").strip()
                home_team = row.get("home", "").strip()

                road_is_fbs = is_fbs_team(road_team)
                home_is_fbs = is_fbs_team(home_team)

                if road_is_fbs and home_is_fbs:
                    fbs_games.append(row)
                else:
                    non_fbs_games.append(
                        {
                            "road": road_team,
                            "home": home_team,
                            "road_fbs": road_is_fbs,
                            "home_fbs": home_is_fbs,
                            "reason": f"Road: {'FBS' if road_is_fbs else 'Non-FBS'}, Home: {'FBS' if home_is_fbs else 'Non-FBS'}",
                        }
                    )

    except Exception as e:
        return {"error": f"Error reading CSV: {str(e)}"}

    # Write filtered data if not dry run
    if not dry_run:
        try:
            with open(output_file, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=headers)
                writer.writeheader()
                writer.writerows(fbs_games)
        except Exception as e:
            return {"error": f"Error writing filtered CSV: {str(e)}"}

    return {
        "success": True,
        "input_file": input_file,
        "output_file": output_file if not dry_run else None,
        "total_games": total_games,
        "fbs_games": len(fbs_games),
        "non_fbs_games": len(non_fbs_games),
        "games_removed": len(non_fbs_games),
        "non_fbs_details": non_fbs_games,
        "removal_rate": (
            round(len(non_fbs_games) / total_games * 100, 1) if total_games > 0 else 0
        ),
    }


def main():
    parser = argparse.ArgumentParser(
        description="Filter non-FBS games from prediction data"
    )
    parser.add_argument(
        "--input",
        default="predictions/ncaapredictions.csv",
        help="Input CSV file to filter (default: predictions/ncaapredictions.csv)",
    )
    parser.add_argument("--output", help="Output file for filtered data")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be removed without making changes",
    )
    parser.add_argument("--verbose", action="store_true", help="Verbose output")

    args = parser.parse_args()

    print("🏈 FBS Game Filtering Tool")
    print("=" * 50)

    if args.dry_run:
        print("🔍 DRY RUN MODE - No files will be modified")
        print()

    result = filter_ncaapredictions_csv(args.input, args.output, args.dry_run)

    if "error" in result:
        print(f"❌ Error: {result['error']}")
        sys.exit(1)

    print(f"📊 Analysis Results:")
    print(f"   Total games: {result['total_games']}")
    print(f"   FBS games kept: {result['fbs_games']}")
    print(f"   Non-FBS games removed: {result['games_removed']}")
    print(f"   Removal rate: {result['removal_rate']}%")
    print()

    if result["non_fbs_details"]:
        print("🚫 Non-FBS games to be removed:")
        for game in result["non_fbs_details"]:
            print(f"   {game['road']} vs {game['home']} ({game['reason']})")
        print()

    if not args.dry_run:
        print(f"✅ FBS-only data saved to: {result['output_file']}")
        print(f"   Games reduced from {result['total_games']} → {result['fbs_games']}")
        print(
            f"   Data quality improved: {result['removal_rate']}% non-FBS contamination removed"
        )
    else:
        print("💡 Use --apply to actually filter the file")
        print(
            "   Example: python3 scripts/filter_fbs_games.py --input predictions/ncaapredictions.csv --output predictions/ncaapredictions_fbs.csv"
        )


if __name__ == "__main__":
    main()
