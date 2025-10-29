#!/usr/bin/env python3
"""
SLK Calendar Sync - Main entry point

This script fetches match data from the Super League Kerala API
and syncs it with a Google Calendar.
"""

import sys
from pathlib import Path

# Add src to Python path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

from main import main

if __name__ == "__main__":
    main()
