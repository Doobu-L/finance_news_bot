import difflib
import google.generativeai as genai
from deep_translator import GoogleTranslator
from config import config

class NewsProcessor:
    def __init__(self):
        # Configure Gemini if key is present
        if config.GEMINI_API_KEY:
            genai.configure(api_key=config.GEMINI_API_KEY)
            self.model = genai.GenerativeModel('gemini-2.0-flash')
        else:
            self.model = None
        
        self.translator = GoogleTranslator(source='auto', target='ko')

    def deduplicate(self, articles, history_links):
        """
        Filter out articles that are already in history or duplicative within the current batch.
        """
        unique_articles = []
        seen_titles = [] # To check duplicates within the current batch
        
        for article in articles:
            link = article['link']
            title = article['title']
            
            # Check history
            if link in history_links:
                continue
            
            # Check within batch (fuzzy match)
            is_duplicate = False
            for seen_title in seen_titles:
                ratio = difflib.SequenceMatcher(None, title, seen_title).ratio()
                if ratio > 0.8: # 80% similarity threshold
                    is_duplicate = True
                    break
            
            if not is_duplicate:
                unique_articles.append(article)
                seen_titles.append(title)
        
        return unique_articles

    def translate_text(self, text):
        """
        Translate text to Korean. Prefer Gemini if key exists, else deep-translator.
        """
        # If text is already Korean, skip
        if self._is_mostly_korean(text):
            return text

        if self.model:
            try:
                response = self.model.generate_content(
                    f"Translate the following news title to Korean naturally: {text}"
                )
                return response.text.strip()
            except Exception as e:
                print(f"Gemini translation failed: {e}. Falling back to Googletrans.")
        
        try:
            return self.translator.translate(text)
        except Exception as e:
            print(f"Translation failed: {e}")
            return text

    def _is_mostly_korean(self, text):
        korean_count = 0
        for char in text:
            if '가' <= char <= '힣':
                korean_count += 1
        return korean_count > len(text) * 0.3 # 30% Korean chars

    # Add method to translate summary specifically or reuse
    def translate_summary(self, text):
        if not text:
            return ""
        if self._is_mostly_korean(text):
            return text
            
        if self.model:
            try:
                response = self.model.generate_content(
                    f"Summarize the following text in 1-2 Korean sentences: {text}"
                )
                return response.text.strip()
            except Exception as e:
                print(f"Gemini summary failed: {e}")
                return text # Fallback: return original summary if gemini fails (googletrans might be too slow for long text)
        
        return text

    def process_and_translate(self, articles):
        """
        Translate titles and summaries.
        """
        from src.utils import clean_html # Import here to avoid circular if any (though utils doesn't import processor)

        processed = []
        for article in articles:
            # Title
            original_title = article['title']
            translated_title = self.translate_text(original_title)
            article['title'] = translated_title
            
            if original_title != translated_title:
                article['original_title'] = original_title
            
            # Summary
            if 'summary' in article:
                clean_summary = clean_html(article['summary'])
                # Truncate if too long before translation to save tokens/time
                if len(clean_summary) > 500:
                    clean_summary = clean_summary[:500] + "..."
                
                translated_summary = self.translate_summary(clean_summary)
                article['summary'] = translated_summary
            
            processed.append(article)
        return processed

    def sort_articles(self, articles):
        """
        Sort by published date (descending).
        """
        # published_parsed is a struct_time, convert to datetime for easier comparison if needed,
        # but struct_time is comparable.
        # Reverse=True for descending (newest first)
        return sorted(articles, key=lambda x: x['published_parsed'], reverse=True)
