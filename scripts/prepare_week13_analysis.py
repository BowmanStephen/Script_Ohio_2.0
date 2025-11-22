#!/usr/bin/env python3
"""
Week 13 Analysis Preparation Script (Convenience Wrapper)
Calls prepare_weekly_analysis.py with week=13
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from scripts.prepare_weekly_analysis import main as weekly_main

if __name__ == "__main__":
    # Override sys.argv to add --week 13
    original_argv = sys.argv.copy()
    if '--week' not in sys.argv:
        sys.argv.insert(1, '--week')
        sys.argv.insert(2, '13')
    
    sys.exit(weekly_main())
