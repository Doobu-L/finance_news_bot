import json
import os
from datetime import datetime
from config import config

def load_history():
    """Load sent article IDs/links from history file."""
    if not os.path.exists(config.HISTORY_FILE):
        return []
    try:
        with open(config.HISTORY_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except json.JSONDecodeError:
        return []

def save_history(history):
    """Save sent article IDs/links to history file."""
    # Ensure directory exists
    os.makedirs(os.path.dirname(config.HISTORY_FILE), exist_ok=True)
    
    # Keep history size manageable (e.g., last 1000 items)
    if len(history) > 1000:
        history = history[-1000:]
        
    with open(config.HISTORY_FILE, 'w', encoding='utf-8') as f:
        json.dump(history, f, indent=2)

from bs4 import BeautifulSoup

def clean_html(text):
    """Remove HTML tags if present."""
    if not text:
        return ""
    soup = BeautifulSoup(text, "html.parser")
    return soup.get_text(separator=" ", strip=True)
