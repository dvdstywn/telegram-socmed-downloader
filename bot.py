import logging
import os
import re
import tempfile
import asyncio
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)
logger = logging.getLogger(__name__)

# Get the bot token from environment variable
TOKEN = "6818691732:AAF7QU1EtzO-R0VlWk2E4VBd1zmhS6QRImc"
if not TOKEN:
    raise ValueError("TELEGRAM_BOT_TOKEN environment variable is not set")

def extract_urls(text):
    """Extract all URLs from text"""
    url_pattern = r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
    return re.findall(url_pattern, text)

def download_media(url):
    """Download media using gallery-dl"""
    import subprocess
    import json

    # Create a temporary directory for downloads
    with tempfile.TemporaryDirectory() as tmpdir:
        # Run gallery-dl to get metadata first
        metadata_cmd = [
            'gallery-dl',
            '--dump-json',
            '--range', '1',  # Only get info for first image/video to create caption
            url
        ]

        try:
            metadata_result = subprocess.run(metadata_cmd, capture_output=True, text=True, timeout=30)
            if metadata_result.returncode != 0:
                logger.error(f"gallery-dl metadata failed: {metadata_result.stderr}")
                return None, None, None

            # Parse metadata to get post URL for caption
            metadata_lines = metadata_result.stdout.strip().split('\n')
            if not metadata_lines:
                return None, None, None

            metadata = json.loads(metadata_lines[0])
            post_url = metadata.get('_fallback', {}).get('webpage') or metadata.get('webpage_url') or url

        except (subprocess.TimeoutExpired, json.JSONDecodeError) as e:
            logger.error(f"Error getting metadata: {e}")
            post_url = url

        # Now download the media
        download_cmd = [
            'gallery-dl',
            '--directory', tmpdir,
            '--limit', '5',  # Limit to 5 files to prevent spam
            url
        ]

        try:
            result = subprocess.run(download_cmd, capture_output=True, text=True, timeout=120)
            if result.returncode != 0:
                logger.error(f"gallery-dl download failed: {result.stderr}")
                return None, None, None

            # Get downloaded files
            downloaded_files = []
            for root, dirs, files in os.walk(tmpdir):
                for file in files:
                    # Skip JSON files and other non-media files
                    if not file.endswith(('.json', '.tmp', '.part')):
                        downloaded_files.append(os.path.join(root, file))

            # Sort files to ensure consistent ordering
            downloaded_files.sort()

            return downloaded_files[:10], post_url, None  # Limit to 10 files

        except subprocess.TimeoutExpired:
            logger.error("gallery-dl download timed out")
            return None, None, "Download timed out"
        except Exception as e:
            logger.error(f"Error downloading media: {e}")
            return None, None, str(e)

async def send_media(update: Update, context: ContextTypes.DEFAULT_TYPE, file_paths, caption):
    """Send media files to user"""
    chat_id = update.effective_chat.id

    for i, file_path in enumerate(file_paths):
        try:
            # Create caption only for the first file
            file_caption = caption if i == 0 else None

            if file_path.lower().endswith(('.mp4', '.avi', '.mov', '.mkv', '.webm')):
                with open(file_path, 'rb') as video:
                    await context.bot.send_video(chat_id=chat_id, video=video, caption=file_caption)
            elif file_path.lower().endswith(('.jpg', '.jpeg', '.png', '.gif', '.webp')):
                with open(file_path, 'rb') as photo:
                    await context.bot.send_photo(chat_id=chat_id, photo=photo, caption=file_caption)
            else:
                with open(file_path, 'rb') as document:
                    await context.bot.send_document(chat_id=chat_id, document=document, caption=file_caption)

        except Exception as e:
            logger.error(f"Error sending file {file_path}: {e}")
            if i == 0:  # Send error message only for the first file
                await context.bot.send_message(chat_id=chat_id, text=f"Error sending media: {str(e)}")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle incoming messages"""
    if not update.message or not update.message.text:
        return

    text = update.message.text
    urls = extract_urls(text)

    if not urls:
        return  # No URLs found in message

    # Process only the first URL
    url = urls[0]

    # Notify user that download is starting
    sent_message = await update.message.reply_text("Downloading media, please wait...")

    # Download media
    file_paths, post_url, error = download_media(url)

    if error:
        await sent_message.edit_text(f"Error: {error}")
        return

    if not file_paths:
        await sent_message.edit_text("No media found at that URL.")
        return

    # Create caption with post URL
    caption = f"[media] [caption] {post_url}"

    # Delete the "Downloading" message
    await sent_message.delete()

    # Send media
    await send_media(update, context, file_paths, caption)

def main():
    """Start the bot"""
    # Create the Application and pass it your bot's token
    application = Application.builder().token(TOKEN).build()

    # Register message handler
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # Start the Bot
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()
