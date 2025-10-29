"""Google Calendar service for managing SLK match events."""

import os
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import pytz

from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from dotenv import load_dotenv

from config import (
    GOOGLE_CALENDAR_ID, 
    EVENT_DURATION_HOURS,
    TIMEZONE
)

logger = logging.getLogger(__name__)

# Scopes required for Google Calendar API
SCOPES = ['https://www.googleapis.com/auth/calendar']


class GoogleCalendarService:
    """Service for managing Google Calendar events using Service Account (easier than OAuth)."""
    
    def __init__(self, service_account_file: Optional[str] = None):
        self.service_account_file = service_account_file or os.getenv('GOOGLE_SERVICE_ACCOUNT_FILE')
        self.calendar_id = GOOGLE_CALENDAR_ID
        self.service = None
        self.timezone = pytz.timezone(TIMEZONE)
        
    def authenticate(self) -> bool:
        """
        Authenticate with Google Calendar API using Service Account.
        
        Returns:
            True if authentication successful, False otherwise
        """
        try:
            # Load environment variables
            load_dotenv()
            
            if not self.service_account_file:
                logger.error("GOOGLE_SERVICE_ACCOUNT_FILE not set")
                logger.error("Set it with: export GOOGLE_SERVICE_ACCOUNT_FILE='/path/to/service-account.json'")
                return False
            
            if not os.path.exists(self.service_account_file):
                logger.error(f"Service account file not found: {self.service_account_file}")
                return False
            
            # logger.info("Authenticating with service account...")
            
            # Load service account credentials
            credentials = service_account.Credentials.from_service_account_file(
                self.service_account_file,
                scopes=SCOPES
            )
            
            # Build the service
            self.service = build('calendar', 'v3', credentials=credentials)
            
            # logger.info("Successfully authenticated with Google Calendar API using service account")
            return True
            
        except Exception as e:
            logger.error(f"Service account authentication failed: {e}")
            return False
    
    def _format_event_description(self, match_data: Dict[str, Any]) -> str:
        """Format event description with team logos and broadcast information."""
        # Base URL for SLK assets
        base_url = "https://www.superleaguekerala.com"
        
        # Format broadcast channels as a simple list
        broadcast_channels = []
        for channel in match_data.get('broadcast', []):
            channel_name = channel.get('name', '')
            broadcast_channels.append(channel_name)
        
        
        # Format description with text at top, logos at bottom
        # Add score and video links at the top for completed matches
        completed_header = ""
        if match_data.get('completed', 0) == 1:
            result = match_data.get('result', '')
            highlight_video = match_data.get('highlight_video', '')
            full_video_url = match_data.get('full_video_url', '')
            match_id = match_data.get('match_id', '')
            home_team = match_data.get('home_team', '').lower().replace(' ', '-')
            away_team = match_data.get('away_team', '').lower().replace(' ', '-')
            
            completed_header = ""
            if result:
                completed_header += f"🏆 <strong>Final Score: {result}</strong>\n\n"
            
            # Add match center link for completed matches
            if match_id and home_team and away_team:
                match_center_url = f"https://www.superleaguekerala.com/matchcentre/{match_id}/{home_team}-vs-{away_team}"
                completed_header += f"📊 <strong>Match Center:</strong> <a href='{match_center_url}'>View Details & Stats</a>\n\n"
            
            if highlight_video:
                completed_header += f"🎥 <strong>Highlights:</strong> {highlight_video}\n\n"
            
            if full_video_url:
                completed_header += f"📺 <strong>Full Match:</strong> {full_video_url}\n\n"
        
        # Format broadcast channels as bullet points with links only for SPORTS.COM
        broadcast_bullets = ""
        if broadcast_channels:
            broadcast_items = []
            for channel in match_data.get('broadcast', []):
                channel_name = channel.get('name', '')
                channel_link = channel.get('link', '')
                
                if channel_name.upper() == 'SPORTS.COM' and channel_link:
                    broadcast_items.append(f"• <a href='{channel_link}'>{channel_name} (Online Streaming)</a>")
                else:
                    broadcast_items.append(f"• {channel_name}")
            
            broadcast_bullets = "📺 Broadcast:\n" + "\n".join(broadcast_items)
        else:
            broadcast_bullets = "📺 Broadcast: Not Available"
        
        # Format description - simple and compact, no logos
        description = f"""{completed_header}📍 Where: {match_data.get('venue', 'Not Available')}
📅 When: {match_data.get('date', 'Not Available')} at {match_data.get('time', 'Not Available')} IST"""
        
        # Add ticket link only for upcoming matches
        if match_data.get('completed', 0) == 0:
            description += f"""
🎫 Tickets: {match_data.get('ticket_link', 'Not Available')}
{broadcast_bullets}"""
        
        description += f"""

📺 <strong>TV Channel Numbers:</strong> <a href='https://www.instagram.com/super.league.kerala/p/DQHVs0Ak3qU/?hl=en'>View Channel Guide</a>

For more info: superleaguekerala.com"""
        
        return description
    
    def create_event(self, match_data: Dict[str, Any]) -> Optional[str]:
        """
        Create a calendar event for a match.
        
        Args:
            match_data: Formatted match data
            
        Returns:
            Event ID if successful, None otherwise
        """
        if not self.service:
            logger.error("Calendar service not authenticated")
            return None
        
        if not match_data.get('datetime'):
            logger.warning(f"No datetime for match: {match_data.get('title', 'Unknown')}")
            return None
        
        try:
            # Convert to timezone-aware datetime
            match_datetime = self.timezone.localize(match_data['datetime'])
            end_datetime = match_datetime + timedelta(hours=EVENT_DURATION_HOURS)
            
            # Format description with logos
            description = self._format_event_description(match_data)
            
            event = {
                'summary': match_data['title'],
                'description': description,
                'start': {
                    'dateTime': match_datetime.isoformat(),
                    'timeZone': TIMEZONE,
                },
                'end': {
                    'dateTime': end_datetime.isoformat(),
                    'timeZone': TIMEZONE,
                },
                'location': match_data.get('venue', 'Not Available'),
                'reminders': {
                    'useDefault': False,
                    'overrides': [
                        {'method': 'popup', 'minutes': 60}  # 1 hour before
                    ]
                },
                'source': {
                    'title': 'Super League Kerala',
                    'url': 'https://www.superleaguekerala.com'
                }
            }
            
            # Add match ID as extended property for tracking
            if match_data.get('match_id'):
                event['extendedProperties'] = {
                    'private': {
                        'slk_match_id': str(match_data['match_id'])
                    }
                }
            
            created_event = self.service.events().insert(
                calendarId=self.calendar_id, 
                body=event
            ).execute()
            
            event_id = created_event.get('id')
            logger.info(f"Created event: {match_data['title']} (ID: {event_id})")
            return event_id
            
        except HttpError as e:
            logger.error(f"Failed to create event: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error creating event: {e}")
            return None
    
    def clear_all_events(self) -> bool:
        """
        Clear all events from the calendar.
        
        Returns:
            True if successful, False otherwise
        """
        if not self.service:
            logger.error("Calendar service not authenticated")
            return False
        
        try:
            logger.info("Clearing all events from calendar...")
            
            # Get all events
            events_result = self.service.events().list(
                calendarId=self.calendar_id,
                maxResults=2500,  # Google Calendar API limit
                singleEvents=True,
                orderBy='startTime'
            ).execute()
            
            events = events_result.get('items', [])
            
            if not events:
                logger.info("No events found to clear")
                return True
            
            logger.info(f"Found {len(events)} events to delete")
            
            deleted_count = 0
            for event in events:
                try:
                    # Skip recurring events (they have 'recurringEventId')
                    if 'recurringEventId' in event:
                        logger.debug(f"Skipping recurring event: {event.get('summary', 'Unknown')}")
                        continue
                    
                    event_id = event['id']
                    event_title = event.get('summary', 'Unknown')
                    
                    self.service.events().delete(
                        calendarId=self.calendar_id,
                        eventId=event_id
                    ).execute()
                    
                    deleted_count += 1
                    logger.debug(f"Deleted event: {event_title}")
                    
                except HttpError as e:
                    logger.warning(f"Failed to delete event {event.get('summary', 'Unknown')}: {e}")
                    continue
            
            logger.info(f"Successfully deleted {deleted_count} events")
            return True
            
        except HttpError as e:
            logger.error(f"Failed to clear calendar events: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error while clearing events: {e}")
            return False
    
    def find_event_by_match_id(self, match_id: int) -> Optional[str]:
        """
        Find an existing event by SLK match ID.
        
        Args:
            match_id: SLK match ID
            
        Returns:
            Event ID if found, None otherwise
        """
        if not self.service:
            logger.error("Calendar service not authenticated")
            return None
        
        try:
            # Search for events with the match ID in extended properties
            events_result = self.service.events().list(
                calendarId=self.calendar_id,
                maxResults=1000,
                singleEvents=True,
                orderBy='startTime'
            ).execute()
            
            events = events_result.get('items', [])
            
            for event in events:
                extended_props = event.get('extendedProperties', {})
                private_props = extended_props.get('private', {})
                if private_props.get('slk_match_id') == str(match_id):
                    return event['id']
            
            return None
            
        except HttpError as e:
            logger.error(f"Failed to search for events: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error searching for events: {e}")
            return None
    
    def update_event(self, event_id: str, match_data: Dict[str, Any]) -> bool:
        """
        Update an existing calendar event.
        
        Args:
            event_id: ID of the event to update
            match_data: Updated match data
            
        Returns:
            True if successful, False otherwise
        """
        if not self.service:
            logger.error("Calendar service not authenticated")
            return False
        
        try:
            # Get existing event
            event = self.service.events().get(
                calendarId=self.calendar_id, 
                eventId=event_id
            ).execute()
            
            # Update event details
            event['summary'] = match_data['title']
            
            # Update description with logos
            description = self._format_event_description(match_data)
            
            event['description'] = description
            event['location'] = match_data.get('venue', 'Not Available')
            
            # Update datetime if provided
            if match_data.get('datetime'):
                match_datetime = self.timezone.localize(match_data['datetime'])
                end_datetime = match_datetime + timedelta(hours=EVENT_DURATION_HOURS)
                
                event['start'] = {
                    'dateTime': match_datetime.isoformat(),
                    'timeZone': TIMEZONE,
                }
                event['end'] = {
                    'dateTime': end_datetime.isoformat(),
                    'timeZone': TIMEZONE,
                }
            
            # Update the event
            updated_event = self.service.events().update(
                calendarId=self.calendar_id,
                eventId=event_id,
                body=event
            ).execute()
            
            logger.info(f"Updated event: {match_data['title']} (ID: {event_id})")
            return True
            
        except HttpError as e:
            logger.error(f"Failed to update event {event_id}: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error updating event: {e}")
            return False
    
