#!/usr/bin/env python3
"""
Super League Kerala Calendar Sync

This script fetches match data from the Super League Kerala API
and syncs it with a Google Calendar.
"""

import logging
import sys
from typing import List, Dict, Any
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

from slk_api import SLKAPIClient
from calendar_service import GoogleCalendarService
from config import GOOGLE_SERVICE_ACCOUNT_FILE
from models import MatchData
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('slk_calendar_sync.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

# Suppress Google API client discovery cache warnings
logging.getLogger('googleapiclient.discovery_cache').setLevel(logging.WARNING)

logger = logging.getLogger(__name__)


class SLKCalendarSync:
    """Main class for syncing SLK matches with Google Calendar."""
    
    def __init__(self, max_workers: int = 5):
        self.api_client = SLKAPIClient()
        self.calendar_service = GoogleCalendarService(
            service_account_file=GOOGLE_SERVICE_ACCOUNT_FILE
        )
        self.max_workers = max_workers
    
    def _process_single_match(self, match: MatchData, sync_completed: bool = False) -> Dict[str, Any]:
        """
        Process a single match for calendar sync.
        
        Args:
            match: MatchData object to process
            sync_completed: Whether to sync completed matches
            
        Returns:
            Dictionary with result information
        """
        result = {
            'match_id': match.match_id,
            'title': '',
            'action': 'skipped',
            'success': False,
            'error': None
        }
        
        try:
            # Format match data
            formatted_match = self.api_client.format_match_for_calendar(match)
            result['title'] = formatted_match.get('title', 'Unknown')
            
            # Skip matches without datetime
            if not formatted_match.get('datetime'):
                logger.warning(f"Skipping match without datetime: {result['title']}")
                return result
            
            # Skip completed matches if not syncing them
            if formatted_match.get('completed', 0) == 1 and not sync_completed:
                logger.debug(f"Skipping completed match: {result['title']}")
                return result
            
            # Create a new calendar service instance for this thread
            # This prevents thread safety issues with shared service objects
            thread_calendar_service = GoogleCalendarService(
                service_account_file=GOOGLE_SERVICE_ACCOUNT_FILE
            )
            
            # Authenticate the thread-specific service
            if not thread_calendar_service.authenticate():
                result['action'] = 'error'
                result['error'] = 'Failed to authenticate calendar service'
                logger.error(f"Failed to authenticate calendar service for match: {result['title']}")
                return result
            
            # Check if event already exists
            match_id = formatted_match.get('match_id')
            existing_event_id = None
            
            if match_id:
                existing_event_id = thread_calendar_service.find_event_by_match_id(match_id)
            
            if existing_event_id:
                # Update existing event
                if thread_calendar_service.update_event(existing_event_id, formatted_match):
                    result['action'] = 'updated'
                    result['success'] = True
                    # logger.info(f"Updated event for match: {result['title']}")
                else:
                    result['action'] = 'error'
                    result['error'] = 'Failed to update event'
                    logger.error(f"Failed to update event for match: {result['title']}")
            else:
                # Create new event
                event_id = thread_calendar_service.create_event(formatted_match)
                if event_id:
                    result['action'] = 'created'
                    result['success'] = True
                    logger.info(f"Created event for match: {result['title']}")
                else:
                    result['action'] = 'error'
                    result['error'] = 'Failed to create event'
                    logger.error(f"Failed to create event for match: {result['title']}")
        
        except Exception as e:
            result['action'] = 'error'
            result['error'] = str(e)
            logger.error(f"Error processing match {match.match_id}: {e}")
        
        return result
    
    def sync_matches(self, sync_completed: bool = False) -> Dict[str, int]:
        """
        Sync matches with Google Calendar using parallel processing.
        
        Args:
            sync_completed: Whether to sync completed matches as well
            
        Returns:
            Dictionary with sync statistics
        """
        stats = {
            'created': 0,
            'updated': 0,
            'errors': 0,
            'skipped': 0
        }
        
        try:
            # Fetch matches from API based on sync requirements
            logger.info("Fetching matches from Super League Kerala API...")
            if sync_completed:
                matches = self.api_client.fetch_matches()
            else:
                matches = self.api_client.get_upcoming_matches()
            
            if not matches:
                logger.warning("No matches found in API response")
                return stats
            
            logger.info(f"Processing {len(matches)} matches using {self.max_workers} parallel workers...")
            
            # Process matches in parallel
            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                # Submit all tasks
                future_to_match = {
                    executor.submit(self._process_single_match, match, sync_completed): match 
                    for match in matches
                }
                
                # Process completed tasks
                for future in as_completed(future_to_match):
                    match = future_to_match[future]
                    try:
                        result = future.result()
                        
                        # Update statistics based on result
                        if result['action'] == 'created':
                            stats['created'] += 1
                        elif result['action'] == 'updated':
                            stats['updated'] += 1
                        elif result['action'] == 'skipped':
                            stats['skipped'] += 1
                        elif result['action'] == 'error':
                            stats['errors'] += 1
                            if result['error']:
                                logger.error(f"Error processing match {result['match_id']}: {result['error']}")
                    
                    except Exception as e:
                        stats['errors'] += 1
                        logger.error(f"Unexpected error processing match {match.match_id}: {e}")
            
            logger.info(f"Sync completed. Created: {stats['created']}, Updated: {stats['updated']}, "
                       f"Errors: {stats['errors']}, Skipped: {stats['skipped']}")
            
            return stats
            
        except Exception as e:
            logger.error(f"Sync failed: {e}")
            stats['errors'] += 1
            return stats
    
    def sync_upcoming_only(self) -> Dict[str, int]:
        """Sync only upcoming matches."""
        logger.info("Syncing upcoming matches only...")
        return self.sync_matches(sync_completed=False)
    
    def sync_all_matches(self) -> Dict[str, int]:
        """Sync all matches (upcoming and completed)."""
        logger.info("Syncing all matches...")
        return self.sync_matches(sync_completed=True)
    
    def full_refresh(self) -> Dict[str, int]:
        """
        Perform a full refresh: clear all events and sync all matches.
        
        Returns:
            Dictionary with sync statistics
        """
        logger.info("Starting full refresh - clearing all events and syncing all matches")
        
        # Authenticate first
        if not self.calendar_service.authenticate():
            logger.error("Failed to authenticate with Google Calendar")
            return {'error': 'Authentication failed'}
        
        # Clear all existing events
        logger.info("Step 1: Clearing all existing events...")
        if not self.calendar_service.clear_all_events():
            logger.error("Failed to clear existing events")
            return {'error': 'Failed to clear events'}
        
        logger.info("Step 2: Syncing all matches (upcoming + completed)...")
        # Sync all matches (upcoming and completed)
        stats = self.sync_matches(sync_completed=True)
        
        if 'error' in stats:
            return stats
        
        # Add refresh info to stats
        stats['refresh_type'] = 'full_refresh'
        stats['events_cleared'] = True
        
        logger.info("Full refresh completed successfully")
        return stats


def main():
    """Main entry point."""
    import argparse
    load_dotenv()
    
    parser = argparse.ArgumentParser(description='Sync Super League Kerala matches with Google Calendar')
    parser.add_argument('--all', action='store_true', 
                       help='Sync all matches (including completed ones)')
    parser.add_argument('--upcoming', action='store_true', 
                       help='Sync only upcoming matches (default)')
    parser.add_argument('--dry-run', action='store_true',
                       help='Show what would be synced without making changes')
    parser.add_argument('--full-refresh', action='store_true',
                       help='Clear all existing events and sync all matches (upcoming + completed)')
    parser.add_argument('--max-workers', type=int, default=5,
                       help='Maximum number of parallel workers for calendar updates (default: 5)')
    
    args = parser.parse_args()
    
    # Default to upcoming matches if no specific option is chosen
    if not args.all and not args.upcoming:
        args.upcoming = True
    
    try:
        sync = SLKCalendarSync(max_workers=args.max_workers)
        
        if args.dry_run:
            logger.info("DRY RUN MODE - No changes will be made")
            # In dry run, just fetch and display matches
            matches = sync.api_client.fetch_matches()
            upcoming = [m for m in matches if m.is_upcoming()]
            completed = [m for m in matches if m.is_completed()]
            cancelled = [m for m in matches if m.is_cancelled()]
            
            logger.info(f"Found {len(upcoming)} upcoming matches, {len(completed)} completed matches, and {len(cancelled)} cancelled matches")
            
            if args.full_refresh:
                logger.info("🔄 FULL REFRESH DRY RUN:")
                logger.info("  1. Would clear ALL existing events from calendar")
                logger.info("  2. Would sync ALL matches (upcoming + completed)")
                logger.info(f"     - {len(upcoming)} upcoming matches")
                logger.info(f"     - {len(completed)} completed matches")
                logger.info(f"     - {len(cancelled)} cancelled matches")
            else:
                for match in upcoming:
                    formatted = sync.api_client.format_match_for_calendar(match)
                    logger.info(f"Would sync upcoming: {formatted['title']} - {formatted['date']} {formatted['time']}")
                
                if args.all:
                    for match in completed:
                        formatted = sync.api_client.format_match_for_calendar(match)
                        logger.info(f"Would sync completed: {formatted['title']} - {formatted['date']} {formatted['time']}")
        else:
            if args.full_refresh:
                stats = sync.full_refresh()
            elif args.all:
                stats = sync.sync_all_matches()
            else:
                stats = sync.sync_upcoming_only()
            
            # Print summary
            print("\n" + "="*50)
            if args.full_refresh:
                print("FULL REFRESH SUMMARY")
            else:
                print("SYNC SUMMARY")
            print("="*50)
            
            if 'error' in stats:
                print(f"❌ Error: {stats['error']}")
            else:
                print(f"Events Created: {stats['created']}")
                print(f"Events Updated: {stats['updated']}")
                print(f"Events Skipped: {stats['skipped']}")
                print(f"Errors: {stats['errors']}")
                
                if args.full_refresh and stats.get('events_cleared'):
                    print("✅ All existing events cleared")
                    print("✅ Full refresh completed")
            
            print("="*50)
            
            if 'error' in stats or stats.get('errors', 0) > 0:
                sys.exit(1)
    
    except KeyboardInterrupt:
        logger.info("Sync interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()