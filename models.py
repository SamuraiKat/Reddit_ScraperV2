from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional

class ScrapeRequest(BaseModel):
    """Request model for scraping endpoint"""
    config: Dict[str, Any] = Field(..., description="Scraping configuration")

class ScrapeResponse(BaseModel):
    """Response model for successful scraping"""
    status: str = Field(..., description="Response status")
    data: List[Dict[str, Any]] = Field(..., description="Scraped data")
    count: int = Field(..., description="Number of items scraped")
    message: str = Field(..., description="Success message")

class CredentialTestResponse(BaseModel):
    """Response model for credential testing"""
    config_keys: List[str] = Field(..., description="Keys present in config")
    has_config_credentials: Dict[str, bool] = Field(..., description="Credentials in config")
    has_env_credentials: Dict[str, bool] = Field(..., description="Credentials in environment")
    credentials_source: str = Field(..., description="Source of credentials")

class SubredditSource(BaseModel):
    """Model for subreddit source configuration"""
    type: str = Field(default="subreddit", description="Source type")
    name: str = Field(..., description="Subreddit name")
    limit: Optional[int] = Field(default=20, description="Number of posts to fetch")
    sort: Optional[str] = Field(default="hot", description="Sort order (hot, new, top, rising)")
    search_keywords: Optional[List[str]] = Field(default=[], description="Keywords to search for")
    time_filter: Optional[str] = Field(default="day", description="Time filter for top posts")

class RedditCredentials(BaseModel):
    """Model for Reddit API credentials"""
    client_id: str = Field(..., description="Reddit client ID")
    client_secret: str = Field(..., description="Reddit client secret")
    user_agent: str = Field(..., description="Reddit user agent")
