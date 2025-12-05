import time
import schedule
from datetime import datetime
from src.markdown_utils import escape_markdown

def job():
    print(f"\n[Job Start] {datetime.now()}")
    
    # ... (fetching/processing omitted for brevity, logic remains same up to formatting) ...
    # We will just update the formatting block below.
    # Note: I'm not overwriting the whole file, just careful targeting.
    # But wait, I need to see the file first to match lines exactly or I can just rewrite the formatting section.
    # Let me read `main.py` first to be precise.

from src.fetcher import NewsFetcher
from src.processor import NewsProcessor
from src.notifier import TelegramNotifier
from src.utils import load_history, save_history
from config import config

def job():
    print(f"\n[Job Start] {datetime.now()}")
    
    # 1. Load History
    history = load_history()
    # Extract links for quick lookup
    history_links = {item['link'] for item in history} # Set for O(1) lookup
    
    # 2. Fetch News
    fetcher = NewsFetcher()
    try:
        raw_articles = fetcher.fetch_all_keywords()
        print(f"Fetched {len(raw_articles)} articles.")
    except Exception as e:
        print(f"Error fetching news: {e}")
        return

    # 3. Process (Deduplicate & Translate)
    processor = NewsProcessor()
    
    # Deduplicate against history AND internal batch
    new_articles = processor.deduplicate(raw_articles, history_links)
    print(f"New unique articles: {len(new_articles)}")
    
    if not new_articles:
        print("No new articles found.")
        return

    # Sort
    sorted_articles = processor.sort_articles(new_articles)
    
    # Translate
    # Translate only top N to avoid quota limits if massive? 
    # Or translate all. Let's translate all for now.
    processed_articles = processor.process_and_translate(sorted_articles)

    # 4. Format Message
    # Group by keyword or just list? User asked for "Domestic" and "Overseas".
    # We inferred region in fetcher. Not explicitly stored as "Domestic/Overseas" category in article dict,
    # but we can check if keyword was Korean or English.
    
    domestic_news = []
    overseas_news = []
    
    for article in processed_articles:
        # Re-check language content or use keyword logic
        if processor._is_mostly_korean(article['original_title' if 'original_title' in article else 'title']):
            domestic_news.append(article)
        else:
            overseas_news.append(article)
            
    # 4. Format and Send Messages
    
    def format_group_message(header, articles):
        if not articles:
            return None
            
        lines = [header]
        
        # Group by Date (YYYY-MM-DD)
        # articles are already sorted by date desc
        current_date_str = ""
        
        for article in articles:
            # Parse date
            try:
                dt = datetime(*article['published_parsed'][:6])
                date_str = dt.strftime("%Y - %m - %d")
                time_str = dt.strftime("%H:%M")
            except:
                date_str = "Unknown Date"
                time_str = "??"

            if date_str != current_date_str:
                lines.append(f"\n[{date_str}]")
                current_date_str = date_str
            
            # Escape fields
            title = escape_markdown(article['title'])
            source = escape_markdown(article.get('source', 'Unknown'))
            summary = escape_markdown(article.get('summary', ''))
            link = article['link'] # Link usually doesn't need escaping in Markdown link syntax if carefully placed, but () might break it. 
            # Actually standard Markdown link [text](url) handles url reasonably unless it has ) parenthesis.
            # safe enough usually.
            
            # Format: [Time] [Source] Title
            # Summary
            # - Link
            
            entry_text = (
                f"[{time_str}] [{source}] **{title}**\n"
                f"{summary}\n"
                f"-[Link]({link})\n"
            )
            lines.append(entry_text)
            
        return "\n".join(lines)

    notifier = TelegramNotifier()

    if domestic_news:
        msg = format_group_message("🇰🇷 **Domestic News**", domestic_news)
        if msg:
            notifier.send_message_sync(msg)
            
    if overseas_news:
        msg = format_group_message("🌍 **Overseas News**", overseas_news)
        if msg:
            notifier.send_message_sync(msg)
    
    # 6. Save History
    # We save simple dict of link/title/date
    new_history_entries = [{'link': a['link'], 'title': a['title'], 'published': a['published']} for a in processed_articles]
    
    # Append to existing history (list)
    # Re-load or just append? We loaded at start. 
    # ideally we append the new ones.
    # Note: 'history' variable from load_history() is a list.
    history.extend(new_history_entries)
    save_history(history)
    print("Job Complete.")

def main():
    print("Finance News Bot Started...")
    
    # Run once immediately for check
    job()
    
    # Schedule
    schedule.every(10).minutes.do(job)
    
    while True:
        schedule.run_pending()
        time.sleep(1)

if __name__ == "__main__":
    main()
