# Super League Kerala Calendar Sync

This project automatically syncs Super League Kerala match data with Google Calendar.

## What it does

- Fetches match data from the official Super League Kerala API
- Creates and updates Google Calendar events for all matches
- Includes match details like venue, broadcast channels, and ticket links
- Shows final scores and highlights for completed matches
- Runs automatically to keep the calendar up-to-date

## Calendar Link

**Public Calendar:** https://calendar.google.com/calendar/u/0?cid=OGFjMWM1MjE4ODNkMDZjMjY5N2RjNjcyYWRlOThhYzA0YmMxZGQwNDE3ODQ0ZjU1YjgzNjI2ZDcwYTU2NzlhY0Bncm91cC5jYWxlbmRhci5nb29nbGUuY29t

### How to add to your calendar:
1. Click the link above
2. Select your Google account (if you have multiple)
3. Click "Add"
4. Done! It's now in your calendar

### How to customize notifications:
1. Go to Google Calendar Settings
2. Under "Default notifications" → "Add a notification"
3. Choose when you want to be notified (email, desktop, mobile)
4. Select timing (10 min, 1 hour, 1 day before, etc.)

### How to remove later:
1. Google Calendar Settings → "Super League Kerala 2025" → "Unsubscribe from calendar"
2. Confirm by clicking "Unsubscribe"

## Security & Privacy

- This is a read-only subscription to _this_ Google Calendar - I cannot who (or if, even) anyone is using this.
- You're only subscribing to view events, not granting any permissions to your account.

## Usage

```bash
# Sync only upcoming matches (default)
uv run slk_sync.py --upcoming

# Sync all matches (including completed ones)
uv run slk_sync.py --all

# Full refresh: clear all events and sync all matches
uv run slk_sync.py --full-refresh
```

## Data Source

Fetches data from: https://www.superleaguekerala.com/api/match-tickets
