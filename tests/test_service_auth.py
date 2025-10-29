#!/usr/bin/env python3
"""Simple Google Calendar authentication using service account (easier for personal use)."""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_service_account_auth():
    """Test Google Calendar authentication using service account."""
    print("🔐 Testing Google Calendar Authentication (Service Account)...")
    
    # Check service account file
    service_account_file = os.getenv('GOOGLE_SERVICE_ACCOUNT_FILE')
    if not service_account_file:
        print("❌ GOOGLE_SERVICE_ACCOUNT_FILE not set")
        print("   Set it with: export GOOGLE_SERVICE_ACCOUNT_FILE='/path/to/service-account.json'")
        print("\n💡 Service accounts are MUCH easier than OAuth for personal projects!")
        print("   They don't require browser authentication or verification.")
        return False
    
    if not os.path.exists(service_account_file):
        print(f"❌ Service account file not found: {service_account_file}")
        return False
    
    print(f"✅ Service account file: {service_account_file}")
    
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
        
        # Test calendar access
        calendar_list = service.calendarList().list().execute()
        calendars = calendar_list.get('items', [])
        
        print(f"✅ Found {len(calendars)} accessible calendars")
        print("✅ Service account authentication successful!")
        
        return True
        
    except Exception as e:
        print(f"❌ Service account error: {e}")
        return False

if __name__ == "__main__":
    if test_service_account_auth():
        print("\n🎉 Service account authentication working!")
        sys.exit(0)
    else:
        print("\n❌ Service account error")
        sys.exit(1)
