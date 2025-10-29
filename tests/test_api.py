#!/usr/bin/env python3
"""Test script to verify API connectivity and data format."""

import json
from slk_api import SLKAPIClient

def test_api():
    """Test the SLK API client."""
    print("Testing Super League Kerala API...")
    
    try:
        client = SLKAPIClient()
        
        # Test fetching all matches
        print("\n1. Fetching all matches...")
        matches = client.fetch_matches()
        print(f"   Found {len(matches)} matches")
        
        # Test upcoming matches
        print("\n2. Fetching upcoming matches...")
        upcoming = client.get_upcoming_matches()
        print(f"   Found {len(upcoming)} upcoming matches")
        
        # Test completed matches
        print("\n3. Fetching completed matches...")
        completed = [match for match in matches if match.is_completed()]
        print(f"   Found {len(completed)} completed matches")
        
        # Show sample match data
        if matches:
            print("\n4. Sample match data:")
            sample_match = matches[0]
            print(f"   Home Team: {sample_match.home_team}")
            print(f"   Away Team: {sample_match.away_team}")
            print(f"   Date: {sample_match.date}")
            print(f"   Time: {sample_match.time}")
            print(f"   Venue: {sample_match.venue or 'TBA'}")
            print(f"   Completed: {sample_match.completed}")
            print(f"   Result: {sample_match.result or 'N/A'}")
            
            # Test formatting
            print("\n5. Testing match formatting...")
            formatted = client.format_match_for_calendar(sample_match)
            print(f"   Formatted Title: {formatted.get('title', 'N/A')}")
            print(f"   Formatted DateTime: {formatted.get('datetime', 'N/A')}")
            print(f"   Broadcast Channels: {formatted.get('broadcast_channels', 'N/A')}")
            
            # Test scorer formatting
            if sample_match.is_completed():
                home_scorers = []
                away_scorers = []
                
                for scorer in sample_match.home_scorers:
                    if isinstance(scorer, dict):
                        home_scorers.append(f"{scorer.get('player', 'Unknown')} ({scorer.get('time', 'Unknown')})")
                    else:
                        home_scorers.append(str(scorer))
                
                for scorer in sample_match.away_scorers:
                    if isinstance(scorer, dict):
                        away_scorers.append(f"{scorer.get('player', 'Unknown')} ({scorer.get('time', 'Unknown')})")
                    else:
                        away_scorers.append(str(scorer))
                
                print(f"   Home Scorers: {home_scorers}")
                print(f"   Away Scorers: {away_scorers}")
        
        print("\n✅ API test completed successfully!")
        
    except Exception as e:
        print(f"\n❌ API test failed: {e}")
        return False
    
    return True

if __name__ == "__main__":
    test_api()
