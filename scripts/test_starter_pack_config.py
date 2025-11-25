#!/usr/bin/env python3
"""
Test starter pack configuration system.

Verifies that the configuration system works correctly and returns
expected types and values.
"""

import sys
from pathlib import Path


def test_config():
    """Test the starter pack configuration system."""
    # Add project root to path
    project_root = Path(__file__).resolve().parent.parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))
    
    try:
        from starter_pack.config.data_config import get_starter_pack_config
    except ImportError as e:
        print(f"❌ Failed to import config: {e}")
        return False
    
    try:
        config = get_starter_pack_config()
    except Exception as e:
        print(f"❌ Failed to get config: {e}")
        return False
    
    print("✅ Config loaded successfully")
    
    # Test current_year
    current_year = config.current_year
    print(f"   Current year: {current_year} (type: {type(current_year).__name__})")
    
    if not isinstance(current_year, int):
        print(f"   ❌ ERROR: current_year is {type(current_year)}, expected int")
        return False
    
    if current_year < 2020 or current_year > 2100:
        print(f"   ❌ ERROR: current_year value {current_year} seems invalid")
        return False
    
    print(f"   ✅ current_year is valid integer: {current_year}")
    
    # Test data_dir
    data_dir = config.data_dir
    print(f"   Data dir: {data_dir}")
    
    if not isinstance(data_dir, Path):
        print(f"   ❌ ERROR: data_dir is {type(data_dir)}, expected Path")
        return False
    
    if not data_dir.exists():
        print(f"   ⚠️  WARNING: data_dir does not exist: {data_dir}")
    else:
        print(f"   ✅ data_dir exists")
    
    # Test project_root
    project_root_config = config.project_root
    print(f"   Project root: {project_root_config}")
    
    if not isinstance(project_root_config, Path):
        print(f"   ❌ ERROR: project_root is {type(project_root_config)}, expected Path")
        return False
    
    # Test required data files
    required_files = [
        "games.csv",
        "teams.csv",
        "conferences.csv",
        f"game_stats/{current_year}.csv",
        f"season_stats/{current_year}.csv",
        f"advanced_season_stats/{current_year}.csv",
    ]
    
    print(f"\n   Checking required data files for {current_year}:")
    missing = []
    for file in required_files:
        path = config.get_data_path(file)
        if path.exists():
            print(f"   ✅ {file}")
        else:
            print(f"   ⚠️  {file} (not found)")
            missing.append(str(path))
    
    if missing:
        print(f"\n   ⚠️  WARNING: {len(missing)} required files not found")
        print("   (This may be expected if data hasn't been generated yet)")
    else:
        print(f"\n   ✅ All required data files exist")
    
    print("\n✅ Config validation passed")
    return True


def main():
    """Main entry point."""
    success = test_config()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()

