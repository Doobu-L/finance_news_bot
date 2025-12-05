import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Config:
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
    TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
    TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
    
    # Defaults
    KEYWORDS = os.getenv("KEYWORDS", "주식,비트코인,경제 속보,Stock Market,Crypto").split(",")
    
    # Paths
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    DATA_DIR = os.path.join(BASE_DIR, "data")
    HISTORY_FILE = os.path.join(DATA_DIR, "history.json")

    # RSS Feeds - Google News
    # We can format the URL with the query
    RSS_URL_TEMPLATE = "https://news.google.com/rss/search?q={query}&hl={lang}-{country}&gl={country}&ceid={country}:{lang}"

config = Config()
