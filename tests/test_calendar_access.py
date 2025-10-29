#!/usr/bin/env python3
"""Test direct calendar access using the specific calendar ID."""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_direct_calendar_access():
    """Test direct access to the specific calendar."""
    print("🔐 Testing Direct Calendar Access...")
    
    service_account_file = os.getenv('GOOGLE_SERVICE_ACCOUNT_FILE')
    if not service_account_file:
        print("❌ GOOGLE_SERVICE_ACCOUNT_FILE not set")
        return False
    
    try:
        from google.oauth2 import service_account
        from googleapiclient.discovery import build
        
        # Load service account credentials
        credentials = service_account.Credentials.from_service_account_file(
            service_account_file,
            scopes=['https://www.googleapis.com/auth/calendar']
        )
        
        # Build the service
        service = build('calendar', 'v3', credentials=credentials)
        
        # Test direct access to the specific calendar
        calendar_id = os.getenv("GOOGLE_CALENDAR_ID")
        
        print(f"📅 Testing access to calendar: {calendar_id}")
        
        try:
            # Try to get calendar info
            calendar_info = service.calendars().get(calendarId=calendar_id).execute()
            print(f"✅ Calendar found: {calendar_info.get('summary', 'Unknown')}")
            
            # Try to list events
            events_result = service.events().list(
                calendarId=calendar_id,
                maxResults=5,
                singleEvents=True,
                orderBy='startTime'
            ).execute()
            
            events = events_result.get('items', [])
            print(f"✅ Found {len(events)} events in calendar")
            
            if events:
                print("   Recent events:")
                for event in events[:3]:
                    print(f"   - {event.get('summary', 'No title')} ({event.get('start', {}).get('dateTime', 'No date')})")
            
            print("✅ Direct calendar access working!")
            return True
            
        except Exception as e:
            print(f"❌ Direct calendar access failed: {e}")
            return False
        
    except Exception as e:
        print(f"❌ Service account error: {e}")
        return False

if __name__ == "__main__":
    if test_direct_calendar_access():
        print("\n🎉 Calendar access is working!")
        sys.exit(0)
    else:
        print("\n❌ Calendar access failed")
        print("💡 Make sure you shared the calendar")
        sys.exit(1)
