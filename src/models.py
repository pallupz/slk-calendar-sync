"""Pydantic models for SLK API responses."""

from datetime import datetime
from typing import List, Optional, Union, Dict, Any
from pydantic import BaseModel, Field, validator, field_validator
import re


class Scorer(BaseModel):
    """Model for scorer information."""
    player: str = Field(..., description="Player name")
    time: str = Field(..., description="Goal time")


class BroadcastChannel(BaseModel):
    """Model for broadcast channel information."""
    name: str = Field(..., description="Channel name")
    logo: str = Field(..., description="Channel logo path")
    link: str = Field(..., description="Channel website URL")
    
    @field_validator('link')
    @classmethod
    def validate_url(cls, v):
        """Validate URL format."""
        if v and not v.startswith(('http://', 'https://')):
            raise ValueError('Link must be a valid URL')
        return v


class Highlight(BaseModel):
    """Model for match highlight information."""
    thumbnail: Optional[str] = Field(None, description="Thumbnail image URL")
    video: Optional[str] = Field(None, description="Video URL")


class MatchData(BaseModel):
    """Model for SLK match data."""
    
    # Team information
    home_team: str = Field(..., description="Home team name")
    home_team_short_name: str = Field(..., description="Home team short name")
    home_team_logo: str = Field(..., description="Home team logo path")
    away_team: str = Field(..., description="Away team name")
    away_team_logo: str = Field(..., description="Away team logo path")
    away_team_short_name: str = Field(..., description="Away team short name")
    
    # Match timing
    match_date: str = Field(..., description="Match date and time")
    date: str = Field(..., description="Formatted date")
    time: str = Field(..., description="Formatted time")
    day: str = Field(..., description="Day of week")
    match_time: Optional[str] = Field(None, description="Match time (legacy)")
    
    # Venue and tickets
    venue: Optional[str] = Field(None, description="Match venue")
    link: Optional[str] = Field(None, description="Ticket purchase link")
    
    # Match status
    completed: int = Field(..., ge=0, le=1, description="Match completion status (0=upcoming, 1=completed)")
    is_cancel: int = Field(..., ge=0, le=1, description="Match cancellation status")
    is_started: int = Field(..., ge=0, le=1, description="Match start status")
    result: Optional[str] = Field(None, description="Match result")
    
    # IDs
    match_id: int = Field(..., gt=0, description="Unique match ID")
    stat_match_id: int = Field(..., gt=0, description="Statistics match ID")
    
    # Scoring - handle both string and dict formats
    home_scorers: List[Union[str, Dict[str, str]]] = Field(default_factory=list, description="Home team scorers")
    away_scorers: List[Union[str, Dict[str, str]]] = Field(default_factory=list, description="Away team scorers")
    
    # Media
    full_video_url: Optional[str] = Field(None, description="Full match video URL")
    broadcast: List[BroadcastChannel] = Field(default_factory=list, description="Broadcast channels")
    highlight: Highlight = Field(default_factory=Highlight, description="Match highlights")
    
    @field_validator('match_date')
    @classmethod
    def validate_match_date(cls, v):
        """Validate match date format."""
        try:
            datetime.strptime(v, '%Y-%m-%d %H:%M:%S')
            return v
        except ValueError:
            raise ValueError('match_date must be in format YYYY-MM-DD HH:MM:SS')
    
    @field_validator('link')
    @classmethod
    def validate_ticket_link(cls, v):
        """Validate ticket link format."""
        if v and not v.startswith(('http://', 'https://')):
            raise ValueError('Ticket link must be a valid URL')
        return v
    
    @field_validator('full_video_url')
    @classmethod
    def validate_video_url(cls, v):
        """Validate video URL format."""
        if v and not v.startswith(('http://', 'https://')):
            raise ValueError('Video URL must be a valid URL')
        return v
    
    @field_validator('result')
    @classmethod
    def validate_result(cls, v):
        """Validate result format."""
        if v and not re.match(r'^\d+\s*-\s*\d+$', v.strip()):
            raise ValueError('Result must be in format "X - Y"')
        return v
    
    def is_upcoming(self) -> bool:
        """Check if match is upcoming."""
        return self.completed == 0 and self.is_cancel == 0
    
    def is_completed(self) -> bool:
        """Check if match is completed."""
        return self.completed == 1
    
    def is_cancelled(self) -> bool:
        """Check if match is cancelled."""
        return self.is_cancel == 1
    
    def get_datetime(self) -> Optional[datetime]:
        """Get match datetime as datetime object."""
        try:
            return datetime.strptime(self.match_date, '%Y-%m-%d %H:%M:%S')
        except ValueError:
            return None
    
