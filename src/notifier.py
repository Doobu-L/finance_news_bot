import asyncio
from telegram import Bot
from config import config

class TelegramNotifier:
    def __init__(self):
        self.token = config.TELEGRAM_BOT_TOKEN
        self.chat_id = config.TELEGRAM_CHAT_ID

    async def send_message(self, text):
        """
        Send a message to the configured Telegram chat.
        Splits long messages to avoid cancellation and parse errors.
        """
        if not self.token or not self.chat_id:
            print("Telegram configuration missing. Skipping notification.")
            return

        # Initialize Bot here to ensure it uses the current event loop's HTTP client
        bot = Bot(token=self.token)

        try:
            # defined limit is 4096, keep it safe at 4000
            MAX_LENGTH = 4000
            
            if len(text) <= MAX_LENGTH:
                await bot.send_message(chat_id=self.chat_id, text=text, parse_mode='Markdown')
            else:
                # Split by lines to maintain markdown safety (mostly)
                lines = text.split('\n')
                chunk = ""
                
                for line in lines:
                    if len(chunk) + len(line) + 1 > MAX_LENGTH:
                        # Send current chunk
                        await bot.send_message(chat_id=self.chat_id, text=chunk, parse_mode='Markdown')
                        chunk = ""
                    
                    chunk += line + "\n"
                
                # Send remaining
                if chunk:
                    await bot.send_message(chat_id=self.chat_id, text=chunk, parse_mode='Markdown')
                    
        except Exception as e:
            print(f"Failed to send Telegram message: {e}")
            # Fallback: Try sending without markdown if it fails (e.g. unclosed entities in a split, though line split minimizes this)
            try:
                print("Retrying without Markdown...")
                await bot.send_message(chat_id=self.chat_id, text=text[:4000], parse_mode=None)
            except Exception as e2:
                print(f"Fallback failed: {e2}")

    def send_message_sync(self, text):
        """
        Wrapper to run async send_message from synchronous code.
        """
        try:
            asyncio.run(self.send_message(text))
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(self.send_message(text))
            loop.close()
        try:
            asyncio.run(self.send_message(text))
        except RuntimeError:
            # Handle case where event loop is already running (e.g. jupyter)
            # But for a script, asyncio.run should work.
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(self.send_message(text))
            loop.close()
