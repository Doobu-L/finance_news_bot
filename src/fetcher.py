import feedparser
import urllib.parse
from config import config
from datetime import datetime
import time

class NewsFetcher:
    def __init__(self):
        self.base_url = config.RSS_URL_TEMPLATE

    def fetch_news(self, keyword, lang="ko", country="KR"):
        """
        Fetches news for a given keyword from Google News RSS.
        """
        encoded_query = urllib.parse.quote(keyword)
        url = self.base_url.format(query=encoded_query, lang=lang, country=country)
        
        print(f"Fetching news for: {keyword} from {url}")
        feed = feedparser.parse(url)
        
        articles = []
        if feed.entries:
            for entry in feed.entries:
                # Basic parsing
                article = {
                    "title": entry.title,
                    "link": entry.link,
                    "published": entry.published,
                    "published_parsed": entry.published_parsed, # struct_time
                    "source": entry.source.title if 'source' in entry else "Unknown",
                    "summary": entry.summary if 'summary' in entry else "",
                    "keyword": keyword
                }
                articles.append(article)
        
        return articles

    def fetch_all_keywords(self):
        """
        Fetches news for all configured keywords.
        """
        all_articles = []
        for keyword in config.KEYWORDS:
            # Determine region based on keyword language or specific rules
            # For simplicity, we search everything in KR region if it's Korean, US if English.
            # But specific requirements said "Domestic and Overseas".
            # We can infer: Korean chars -> KR, English -> US.
            
            if self._is_korean(keyword):
                lang, country = "ko", "KR"
            else:
                lang, country = "en", "US"
                
            articles = self.fetch_news(keyword.strip(), lang, country)
            all_articles.extend(articles)
            
        return all_articles

    def _is_korean(self, text):
        # A simple check if text contains Korean characters
        for char in text:
            if '가' <= char <= '힣':
                return True
        return False

# Quick test
if __name__ == "__main__":
    fetcher = NewsFetcher()
    news = fetcher.fetch_all_keywords()
    print(f"Fetched {len(news)} articles.")
    for n in news[:5]:
        print(f"- [{n['keyword']}] {n['title']} ({n['published']})")
