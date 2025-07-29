import os
from typing import Dict, Any, Optional

class Config:
    """Configuration management for the Reddit scraper"""
    
    @staticmethod
    def get_reddit_credentials() -> Dict[str, str]:
        """Get Reddit API credentials from environment variables"""
        return {
            'client_id': os.getenv('REDDIT_CLIENT_ID', ''),
            'client_secret': os.getenv('REDDIT_CLIENT_SECRET', ''),
            'user_agent': os.getenv('REDDIT_USER_AGENT', 'RedditScraper/1.0')
        }
    
    @staticmethod
    def validate_credentials(credentials: Dict[str, str]) -> bool:
        """Validate that all required credentials are present"""
        required_fields = ['client_id', 'client_secret', 'user_agent']
        return all(credentials.get(field) for field in required_fields)
    
    @staticmethod
    def get_default_scrape_config() -> Dict[str, Any]:
        """Get default scraping configuration"""
        return {
            'sources': [
                {
                    'type': 'subreddit',
                    'name': 'entrepreneur',
                    'limit': 20,
                    'sort': 'hot'
                }
            ]
        }
    
    @staticmethod
    def merge_configs(base_config: Dict[str, Any], override_config: Dict[str, Any]) -> Dict[str, Any]:
        """Merge two configuration dictionaries"""
        merged = base_config.copy()
        merged.update(override_config)
        return merged
