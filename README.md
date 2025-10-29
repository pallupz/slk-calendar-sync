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
