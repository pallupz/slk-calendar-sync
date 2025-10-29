"""Configuration settings for the Super League Kerala Calendar Sync."""

import os
from typing import Optional
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Google Calendar Configuration
GOOGLE_CALENDAR_ID = os.getenv("GOOGLE_CALENDAR_ID")

# Validate required environment variables
if not GOOGLE_CALENDAR_ID:
    raise ValueError("GOOGLE_CALENDAR_ID environment variable is required. Set it in your .env file.")

# API Configuration
SLK_API_URL = "https://www.superleaguekerala.com/api/match-tickets"

# Google API Credentials (set these as environment variables)
GOOGLE_SERVICE_ACCOUNT_FILE: Optional[str] = os.getenv("GOOGLE_SERVICE_ACCOUNT_FILE")

# Validate required service account file
if not GOOGLE_SERVICE_ACCOUNT_FILE:
    raise ValueError("GOOGLE_SERVICE_ACCOUNT_FILE environment variable is required. Set it in your .env file.")

# Calendar Event Settings
EVENT_DURATION_HOURS = 2  # Match duration in hours

# Timezone settings
TIMEZONE = "Asia/Kolkata"
