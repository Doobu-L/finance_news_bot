import json
import os
from datetime import datetime
from config import config

class StateManager:
    def __init__(self):
        self.state_file = os.path.join(config.DATA_DIR, "daily_state.json")
        self.state = self.load_state()

    def load_state(self):
        if not os.path.exists(self.state_file):
            return {"date": datetime.now().strftime("%Y-%m-%d"), "articles": [], "messages": {}}
        try:
            with open(self.state_file, 'r', encoding='utf-8') as f:
                state = json.load(f)
                # Check if date changed, if so, reset
                if state.get("date") != datetime.now().strftime("%Y-%m-%d"):
                    return {"date": datetime.now().strftime("%Y-%m-%d"), "articles": [], "messages": {}}
                return state
        except:
            return {"date": datetime.now().strftime("%Y-%m-%d"), "articles": [], "messages": {}}

    def save_state(self):
        os.makedirs(os.path.dirname(self.state_file), exist_ok=True)
        with open(self.state_file, 'w', encoding='utf-8') as f:
            json.dump(self.state, f, indent=2, ensure_ascii=False)

    def add_articles(self, articles):
        """Add new articles to state."""
        existing_links = {a['link'] for a in self.state['articles']}
        added_count = 0
        now_ts = datetime.now().timestamp()
        
        for article in articles:
            if article['link'] not in existing_links:
                # Add discovery timestamp
                article['discovered_at'] = now_ts
                self.state['articles'].append(article)
                added_count += 1
        
        if added_count > 0:
            self.save_state()
        return added_count

    def get_articles(self):
        return self.state['articles']

    def update_message_id(self, category, message_id):
        self.state['messages'][category] = message_id
        self.save_state()

    def get_message_id(self, category):
        return self.state['messages'].get(category)
