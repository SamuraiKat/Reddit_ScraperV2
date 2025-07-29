import praw
import os
from typing import List, Dict, Any
from datetime import datetime
import time

class RedditScraper:
    """Reddit scraper using PRAW (Python Reddit API Wrapper)"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self._setup_reddit_client()
    
    def _setup_reddit_client(self):
        """Initialize Reddit API client with credentials"""
        # Get credentials from config or environment
        client_id = (
            self.config.get('client_id') or 
            self.config.get('clientId') or 
            os.getenv('REDDIT_CLIENT_ID')
        )
        client_secret = (
            self.config.get('client_secret') or 
            self.config.get('clientSecret') or 
            os.getenv('REDDIT_CLIENT_SECRET')
        )
        user_agent = (
            self.config.get('user_agent') or 
            self.config.get('userAgent') or 
            os.getenv('REDDIT_USER_AGENT', 'RedditScraper/1.0')
        )
        
        # Debug logging (mask sensitive data)
        print(f"🔍 Credential check:")
        print(f"  Client ID: {'✅ Found' if client_id else '❌ Missing'}")
        print(f"  Client Secret: {'✅ Found' if client_secret else '❌ Missing'}")
        print(f"  User Agent: {user_agent}")
        
        if not client_id or not client_secret:
            raise ValueError(
                "Missing Reddit API credentials. Please provide client_id and client_secret "
                "either in the config or as environment variables (REDDIT_CLIENT_ID, REDDIT_CLIENT_SECRET)"
            )
        
        # Initialize Reddit client
        try:
            self.reddit = praw.Reddit(
                client_id=client_id,
                client_secret=client_secret,
                user_agent=user_agent,
                check_for_async=False
            )
            
            # Test the connection
            self.reddit.user.me()  # This will raise an exception if auth fails
            print("✅ Reddit API authentication successful")
            
        except Exception as e:
            print(f"❌ Reddit API authentication failed: {e}")
            # For read-only access, we might still be able to proceed
            self.reddit = praw.Reddit(
                client_id=client_id,
                client_secret=client_secret,
                user_agent=user_agent,
                check_for_async=False
            )
    
    def fetch_data(self) -> List[Dict[str, Any]]:
        """Fetch data from all configured sources"""
        data = []
        sources = self.config.get('sources', [])
        
        if not sources:
            raise ValueError("No sources configured. Please provide at least one source.")
        
        print(f"🚀 Starting scrape with {len(sources)} sources")
        
        for i, source in enumerate(sources, 1):
            try:
                print(f"📊 Processing source {i}/{len(sources)}: {source}")
                source_data = self._fetch_source(source)
                data.extend(source_data)
                print(f"✅ Source {i} completed: {len(source_data)} items")
                
                # Add small delay between sources to be respectful
                if i < len(sources):
                    time.sleep(1)
                    
            except Exception as e:
                print(f"❌ Error processing source {i}: {e}")
                continue
        
        return data
    
    def _fetch_source(self, source: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Fetch data from a single source"""
        source_type = source.get('type', 'subreddit')
        
        if source_type == 'subreddit':
            return self._fetch_subreddit(source)
        else:
            raise ValueError(f"Unsupported source type: {source_type}")
    
    def _fetch_subreddit(self, source: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Fetch posts from a subreddit"""
        # Get configuration
        subreddit_name = source.get('name') or source.get('subreddit')
        limit = source.get('limit', 20)
        sort_type = source.get('sort', 'hot')
        search_keywords = source.get('search_keywords', [])
        time_filter = source.get('time_filter', 'day')
        
        if not subreddit_name:
            raise ValueError("Subreddit name is required")
        
        print(f"🔍 Fetching from r/{subreddit_name}")
        print(f"   Limit: {limit}, Sort: {sort_type}")
        if search_keywords:
            print(f"   Keywords: {search_keywords}")
        
        try:
            subreddit = self.reddit.subreddit(subreddit_name)
            
            # Get submissions based on configuration
            if search_keywords:
                # Search with keywords
                search_query = ' OR '.join(f'"{keyword}"' for keyword in search_keywords)
                submissions = subreddit.search(
                    search_query, 
                    limit=limit, 
                    sort='relevance',
                    time_filter=time_filter
                )
            else:
                # Regular browsing
                if sort_type == 'hot':
                    submissions = subreddit.hot(limit=limit)
                elif sort_type == 'new':
                    submissions = subreddit.new(limit=limit)
                elif sort_type == 'top':
                    submissions = subreddit.top(limit=limit, time_filter=time_filter)
                elif sort_type == 'rising':
                    submissions = subreddit.rising(limit=limit)
                else:
                    submissions = subreddit.hot(limit=limit)
            
            # Process submissions
            data = []
            for submission in submissions:
                try:
                    post_data = self._extract_post_data(submission, subreddit_name)
                    data.append(post_data)
                except Exception as e:
                    print(f"⚠️ Error processing post {submission.id}: {e}")
                    continue
            
            return data
            
        except Exception as e:
            print(f"❌ Error accessing r/{subreddit_name}: {e}")
            raise
    
    def _extract_post_data(self, submission, subreddit_name: str) -> Dict[str, Any]:
        """Extract data from a Reddit submission"""
        return {
            'platform': 'Reddit',
            'source_name': f'/r/{subreddit_name}',
            'thread_id': submission.id,
            'thread_title': submission.title,
            'text': submission.selftext if submission.is_self else '',
            'url': submission.url,
            'permalink': f"https://reddit.com{submission.permalink}",
            'upvotes': submission.score,
            'upvote_ratio': submission.upvote_ratio,
            'num_comments_reported': submission.num_comments,
            'author': str(submission.author) if submission.author else '[deleted]',
            'created_utc': submission.created_utc,
            'created_datetime': datetime.fromtimestamp(submission.created_utc).isoformat(),
            'is_self_post': submission.is_self,
            'domain': submission.domain,
            'over_18': submission.over_18,
            'spoiler': submission.spoiler,
            'stickied': submission.stickied,
            'locked': submission.locked,
            'awards': len(submission.all_awardings) if hasattr(submission, 'all_awardings') else 0,
            'signal_batch': [{
                'thread_id': submission.id,
                'thread_title': submission.title,
                'text': submission.selftext if submission.is_self else '',
                'url': submission.url,
                'upvotes': submission.score,
                'num_comments_reported': submission.num_comments
            }]
        }
