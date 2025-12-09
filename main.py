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

from src.state_manager import StateManager
from datetime import timedelta

def job():
    print(f"\n[Job Start] {datetime.now()}")
    
    # 1. Initialize State Manager
    state_manager = StateManager()
    existing_links = {a['link'] for a in state_manager.get_articles()}
    
    # 2. Fetch News
    fetcher = NewsFetcher()
    try:
        raw_articles = fetcher.fetch_all_keywords()
    except Exception as e:
        print(f"Error fetching news: {e}")
        return

    # 3. Filter for Today & New Items
    # We want ONLY articles published Today (KST)
    # And we need to identify which are new to StateManager to translate them.
    
    today_str = datetime.now().strftime("%Y-%m-%d")
    new_candidates = []
    
    for article in raw_articles:
        # Convert struct_time to datetime
        try:
            # article['published_parsed'] is UTC usually.
            # We want to check if it matches "Today" in local time?
            # Or just check date string?
            # Feedparser converts to UTC struct_time.
            # Convert to local datetime (KST)
            dt_utc = datetime(*article['published_parsed'][:6])
            # Simple offset add for KST (UTC+9)
            dt_kst = dt_utc + timedelta(hours=9)
            article_date_str = dt_kst.strftime("%Y-%m-%d")
            
            # Save KST datetime object for sorting later
            article['dt_kst'] = dt_kst
            
            if article_date_str == today_str:
                if article['link'] not in existing_links:
                    new_candidates.append(article)
        except Exception as e:
            # If date parsing fails, skip or include? 
            # Skip to be safe
            continue
            
    print(f"Found {len(new_candidates)} new articles for today.")
    
    # 4. Process (Deduplicate & Translate) ONLY NEW items
    processor = NewsProcessor()
    
    # Deduplicate internal batch (just in case RSS has duplicates in same fetch)
    # processor.deduplicate is mainly for history check, we can use simple list dict
    unique_candidates = []
    seen_links = set()
    for a in new_candidates:
        if a['link'] not in seen_links:
            unique_candidates.append(a)
            seen_links.add(a['link'])
            
    if unique_candidates:
        # Translate
        processed_new = processor.process_and_translate(unique_candidates)
        # Add to State
        state_manager.add_articles(processed_new)
    
    # 5. Render & Send/Edit
    all_articles = state_manager.get_articles()
    # Need to restore 'dt_kst' for sorting if it's lost in JSON serialization
    # StateManager loads JSON, so we need to re-parse dates for sorting
    for a in all_articles:
        if 'dt_kst' not in a:
            # Reconstruct
            try:
                dt_utc = datetime(*a['published_parsed'][:6])
                a['dt_kst'] = dt_utc + timedelta(hours=9)
            except:
                a['dt_kst'] = datetime.now() # Fallback

    # Sort desc
    all_articles.sort(key=lambda x: x['dt_kst'], reverse=True)
    
    domestic_news = []
    overseas_news = []
    
    for article in all_articles:
        # Check language
        # We need to preserve the logic.
        title_for_check = article.get('original_title', article['title'])
        if processor._is_mostly_korean(title_for_check):
            domestic_news.append(article)
        else:
            overseas_news.append(article)

    notifier = TelegramNotifier()
    
    # Function to generate text and send/edit
    async def process_category(category_name, articles, category_key):
        if not articles:
            return

        msg_lines = [f"{category_name} ({datetime.now().strftime('%Y-%m-%d')})"]
        
        # Determine "Recent" threshold (e.g. 15 mins to be safe for overlap)
        now_ts = datetime.now().timestamp()
        
        for a in articles:
            # Format
            # Highlight if discovered recently (last 12 mins)
            # discovered_at might be missing from old history files, handle gracefully
            discovered_at = a.get('discovered_at', 0)
            is_new = (now_ts - discovered_at) < (12 * 60) # 12 mins
            
            icon = "🆕" if is_new else "•"
            bold_start = "**" if is_new else ""
            bold_end = "**" if is_new else ""
            
            # Fields
            try:
                time_str = a['dt_kst'].strftime("%H:%M")
            except:
                time_str = "??"
                
            source = escape_markdown(a.get('source', 'Unknown'))
            title = escape_markdown(a['title'])
            summary = escape_markdown(a.get('summary', ''))
            link = a['link']
            
            entry_text = (
                f"{icon} [{time_str}] [{source}] {bold_start}{title}{bold_end}\n"
                f"{summary}\n"
                f"-[Link]({link})\n"
            )
            msg_lines.append(entry_text)
            
        full_text = "\n".join(msg_lines)
        
        # Check existing message ID
        existing_id = state_manager.get_message_id(category_key)
        
        if existing_id:
            try:
                # Try Edit
                await notifier.edit_message(existing_id, full_text)
                # If content unchanged, it raises error but that's fine.
            except Exception as e:
                # If fail (e.g. too old 48h+ shouldn't happen for daily, or deleted), send new
                print(f"Edit failed, sending new: {e}")
                msg_obj = await notifier.send_message(full_text)
                if msg_obj:
                    state_manager.update_message_id(category_key, msg_obj.message_id)
        else:
            # Send New
            msg_obj = await notifier.send_message(full_text)
            if msg_obj:
                state_manager.update_message_id(category_key, msg_obj.message_id)

    # Run async wrapper
    import asyncio
    
    async def run_async():
        await process_category("🇰🇷 **Domestic News**", domestic_news, "domestic")
        await process_category("🌍 **Overseas News**", overseas_news, "overseas")
        
    # Helper to run async loop
    try:
        asyncio.run(run_async())
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(run_async())
        loop.close()

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
