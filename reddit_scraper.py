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
        client_id = os.getenv('REDDIT_CLIENT_ID')
        client_secret = os.getenv('REDDIT_CLIENT_SECRET')
        user_agent = os.getenv('REDDIT_USER_AGENT', 'RedditScraper/1.0')
        
        print(f"🔍 Credential check:")
        print(f"  Client ID: {'✅ Found' if client_id else '❌ Missing'}")
        print(f"  Client Secret: {'✅ Found' if client_secret else '❌ Missing'}")
        print(f"  User Agent: {user_agent}")
        
        if not client_id or not client_secret:
            raise ValueError("Missing Reddit API credentials in environment variables.")
        
        try:
            self.reddit = praw.Reddit(
                client_id=client_id,
                client_secret=client_secret,
                user_agent=user_agent,
                check_for_async=False
            )
            self.reddit.user.me()
            print("✅ Reddit API authentication successful")
        except Exception as e:
            print(f"❌ Reddit API authentication failed: {e}")
            raise

    def fetch_data(self) -> List[Dict[str, Any]]:
        """Fetch data from all configured sources"""
        data = []
        sources = self.config.get('sources', [])
        
        if not sources:
            raise ValueError("No sources configured.")
        
        print(f"🚀 Starting scrape with {len(sources)} sources")
        for i, source in enumerate(sources, 1):
            try:
                print(f"📊 Processing source {i}/{len(sources)}: {source.get('name')}")
                source_data = self._fetch_source(source)
                data.extend(source_data)
                print(f"✅ Source {i} completed: {len(source_data)} items")
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
        """Fetch posts and their comments from a subreddit"""
        subreddit_name = source.get('name')
        limit = source.get('limit', 20)
        sort_type = source.get('sort', 'hot')
        time_filter = source.get('time_filter', 'day')
        search_keywords = source.get('search_keywords', [])
        comment_depth = source.get('comment_depth', 0)

        if not subreddit_name:
            raise ValueError("Subreddit name is required")

        print(f"  -> Fetching r/{subreddit_name} (Limit: {limit}, Sort: {sort_type}, Comment Depth: {comment_depth})")

        subreddit = self.reddit.subreddit(subreddit_name)
        
        if search_keywords:
            search_query = ' OR '.join(f'"{keyword}"' for keyword in search_keywords)
            submissions = subreddit.search(search_query, limit=limit, sort='relevance', time_filter=time_filter)
        else:
            sort_func = getattr(subreddit, sort_type)
            if sort_type == 'top':
                submissions = sort_func(limit=limit, time_filter=time_filter)
            else:
                submissions = sort_func(limit=limit)
        
        data = []
        for submission in submissions:
            try:
                post_data = self._extract_post_data(submission, subreddit_name, comment_depth)
                data.append(post_data)
            except Exception as e:
                print(f"⚠️ Error processing post {submission.id}: {e}")
                continue
        return data

    def _fetch_comments(self, submission, max_depth: int) -> List[Dict[str, Any]]:
        """Recursively fetch comments for a submission up to a max depth."""
        if max_depth == 0:
            return []
            
        comments_data = []
        submission.comments.replace_more(limit=None)
        
        for top_level_comment in submission.comments:
            self._traverse_comments(top_level_comment, 1, max_depth, comments_data)
            
        return comments_data

    def _traverse_comments(self, comment, current_depth: int, max_depth: int, comments_data: List):
        """Helper function to traverse comment tree."""
        if not isinstance(comment, praw.models.Comment) or current_depth > max_depth:
            return

        comments_data.append({
            'comment_id': comment.id,
            'text': comment.body,
            'author': str(comment.author) if comment.author else '[deleted]',
            'upvotes': comment.score,
            'depth': current_depth,
            'created_utc': comment.created_utc,
            'created_datetime': datetime.fromtimestamp(comment.created_utc).isoformat(),
        })

        for reply in comment.replies:
            self._traverse_comments(reply, current_depth + 1, max_depth, comments_data)

    def _extract_post_data(self, submission, subreddit_name: str, comment_depth: int) -> Dict[str, Any]:
        """Extract data from a Reddit submission and fetch its comments."""
        comments = self._fetch_comments(submission, comment_depth) if comment_depth > 0 else []

        return {
            'platform': 'Reddit',
            'source_name': f'/r/{subreddit_name}',
            'thread_id': submission.id,
            'thread_title': submission.title,
            'text': submission.selftext if submission.is_self else '',
            'url': submission.url,
            'permalink': f"https://reddit.com{submission.permalink}",
            'upvotes': submission.score,
            'num_comments_reported': submission.num_comments,
            'author': str(submission.author) if submission.author else '[deleted]',
            'created_utc': submission.created_utc,
            'created_datetime': datetime.fromtimestamp(submission.created_utc).isoformat(),
            'comments': comments,
            'num_comments_scraped': len(comments)
        }
