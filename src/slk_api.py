"""API client for Super League Kerala match data."""

import requests
from typing import List, Dict, Any, Optional
from datetime import datetime
import logging
from pydantic import ValidationError

from config import SLK_API_URL
from models import MatchData, BroadcastChannel

logger = logging.getLogger(__name__)


class SLKAPIClient:
    """Client for fetching match data from Super League Kerala API."""
    
    def __init__(self, api_url: str = SLK_API_URL):
        self.api_url = api_url
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'SLK-Calendar-Sync/1.0',
            'Accept': 'application/json'
        })
    
    def fetch_matches(self) -> List[MatchData]:
        """
        Fetch all matches from the Super League Kerala API.
        
        Returns:
            List of validated MatchData objects
            
        Raises:
            ValidationError: If API response doesn't match expected schema
            requests.RequestException: If API request fails
        """
        try:
            logger.info(f"Fetching matches from {self.api_url}")
            response = self.session.get(self.api_url, timeout=30)
            response.raise_for_status()
            
            # Parse JSON response
            raw_matches = response.json()
            
            # Validate each match with Pydantic
            validated_matches = []
            for i, raw_match in enumerate(raw_matches):
                try:
                    match = MatchData.model_validate(raw_match)
                    validated_matches.append(match)
                except ValidationError as e:
                    logger.warning(f"Invalid match data at index {i}: {e}")
                    logger.warning(f"Skipping invalid match: {raw_match.get('home_team', 'Unknown')} vs {raw_match.get('away_team', 'Unknown')}")
                    continue
            
            logger.info(f"Successfully fetched and validated {len(validated_matches)} matches")
            return validated_matches
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to fetch matches: {e}")
            raise
        except ValueError as e:
            logger.error(f"Failed to parse JSON response: {e}")
            raise
        except ValidationError as e:
            logger.error(f"API response validation failed: {e}")
            raise
    
    def get_upcoming_matches(self) -> List[MatchData]:
        """
        Get only upcoming matches (not completed).
        
        Returns:
            List of upcoming MatchData objects
        """
        matches = self.fetch_matches()
        upcoming = [match for match in matches if match.is_upcoming()]
        logger.info(f"Found {len(upcoming)} upcoming matches")
        return upcoming
    
    def _fix_broadcast_urls(self, broadcast_channels: List[BroadcastChannel]) -> List[BroadcastChannel]:
        """
        Fix broadcast channel URLs to use SLK-specific URLs where applicable.
        
        Args:
            broadcast_channels: List of broadcast channels
            
        Returns:
            List of broadcast channels with corrected URLs
        """
        url_mappings = {
            'SPORTS.COM': 'https://sports.com/en/slk',
            'SONY SPORTS': 'https://www.sonysportsnetwork.com/',
            'DD MALAYALAM': 'https://prasarbharati.gov.in/dd-malayalam/',
            'ETISALAT': 'https://www.etisalat.ae'
        }
        
        fixed_channels = []
        for channel in broadcast_channels:
            # Create a new channel with potentially fixed URL
            fixed_url = url_mappings.get(channel.name, channel.link)
            fixed_channel = BroadcastChannel(
                name=channel.name,
                logo=channel.logo,
                link=fixed_url
            )
            fixed_channels.append(fixed_channel)
        
        return fixed_channels
    
    def format_match_for_calendar(self, match: MatchData) -> Dict[str, Any]:
        """
        Format a MatchData object for Google Calendar event creation.
        
        Args:
            match: MatchData object to format
            
        Returns:
            Dictionary with formatted match data for calendar
        """
        # Get match datetime
        match_datetime = match.get_datetime()
        
        # Fix broadcast channel URLs
        fixed_broadcast_channels = self._fix_broadcast_urls(match.broadcast)
        
        # Format broadcast channels
        broadcast_channels = [channel.name for channel in fixed_broadcast_channels]
        broadcast_text = ', '.join(broadcast_channels) if broadcast_channels else 'Not Available'
        
        # Format ticket link
        ticket_link = match.link if match.link else 'Not Available'
        
        # Create event title with score for completed matches
        if match.is_completed():
            result = match.result or ''
            if result:
                event_title = f"🏆 {match.home_team} vs {match.away_team} ({result}) | SLK '25"
            else:
                event_title = f"🏆 {match.home_team} vs {match.away_team} (Completed) | SLK '25"
        elif match.is_cancelled():
            event_title = f"❌ {match.home_team} vs {match.away_team} (Cancelled) | SLK '25"
        else:
            event_title = f"⚽ {match.home_team} vs {match.away_team} | SLK '25"
        
        return {
            'title': event_title,
            'datetime': match_datetime,
            'venue': match.venue or 'Not Available',
            'home_team': match.home_team,
            'away_team': match.away_team,
            'home_team_logo': match.home_team_logo,
            'away_team_logo': match.away_team_logo,
            'date': match.date,
            'time': match.time,
            'broadcast_channels': broadcast_text,
            'broadcast': [channel.model_dump() for channel in fixed_broadcast_channels],
            'ticket_link': ticket_link,
            'match_id': match.match_id,
            'completed': match.completed,
            'result': match.result,
            'home_scorers': match.home_scorers,
            'away_scorers': match.away_scorers,
            'highlight_video': match.highlight.video,
            'full_video_url': match.full_video_url
        }
