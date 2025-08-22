import logging
import os
import re
import json
from urllib.parse import urlparse, parse_qs, urlunparse
from telegram import Update, InputMediaPhoto, InputMediaVideo
from telegram.ext import Application, MessageHandler, filters, ContextTypes
from dotenv import load_dotenv

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)
logger = logging.getLogger(__name__)


load_dotenv()
TOKEN = os.getenv('telegram_token')
if not TOKEN:
    raise ValueError("TELEGRAM_BOT_TOKEN environment variable is not set")

def clean_url(url):
    """Remove tracking parameters from URLs"""
    parsed = urlparse(url)
    query_params = parse_qs(parsed.query)

    # Common tracking parameters to remove
    tracking_params = {
        'utm_source', 'utm_medium', 'utm_campaign', 'utm_term', 'utm_content',
        'igsh', 'igshid', 'fbclid', 'gclid', 'msclkid', 'mc_cid', 'mc_eid',
        'ref', 'referral', 'source', 'share_id', 'share_token'
    }

    # Remove tracking parameters
    cleaned_params = {k: v for k, v in query_params.items() if k not in tracking_params}

    # Reconstruct URL without tracking parameters
    cleaned_query = '&'.join([f"{k}={v[0]}" for k, v in cleaned_params.items()])
    cleaned_parsed = parsed._replace(query=cleaned_query)

    return urlunparse(cleaned_parsed)

def extract_urls(text):
    """Extract all URLs from text"""
    url_pattern = r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
    return re.findall(url_pattern, text)

def download_media(url):
    """Download media using gallery-dl"""
    import subprocess

    # Create a temporary directory for downloads
    # dont use tempfile, use `./tmp` folder instead
    tmpdir = './tmp'
    os.makedirs(tmpdir, exist_ok=True)

    # change this to download the media and metadata together instead do it seperately
    # use gallery-dl --write-info-json --directory . [url]
    # Run gallery-dl to download media and metadata together
    download_cmd = [
        'gallery-dl',
        '--write-info-json',
        '--directory', tmpdir,
        url
    ]

    try:
        result = subprocess.run(download_cmd, capture_output=True, text=True)
        if result.returncode != 0:
            logger.error(f"gallery-dl download failed: {result.stderr}")
            return None, None, None, None, None

        # Look for info.json file for metadata
        info_file_path = None
        for root, dirs, files in os.walk(tmpdir):
            for file in files:
                if file == 'info.json':
                    info_file_path = os.path.join(root, file)
                    break
            if info_file_path:
                break

        # Parse metadata from info.json to get post URL for caption
        post_url = url  # Default to original URL
        description = ""
        username = ""
        fullname = ""
        if info_file_path and os.path.exists(info_file_path):
            try:
                with open(info_file_path, 'r') as f:
                    metadata = json.load(f)
                post_url = metadata.get('post_url') or url
                description = metadata.get('description') or metadata.get('content') or metadata.get('desc') or ""
                author_data = metadata.get('author', {})
                username = metadata.get('username') or author_data.get('name') or ""
                fullname = metadata.get('fullname') or author_data.get('nick') or ""

            except (json.JSONDecodeError, IOError) as e:
                logger.error(f"Error reading info.json: {e}")
        else:
            logger.warning("info.json file not found")

        # Get downloaded files (excluding JSON and temp files)
        downloaded_files = []
        for root, dirs, files in os.walk(tmpdir):
            for file in files:
                # Skip JSON files and other non-media files
                if not file.endswith(('.json', '.tmp', '.part')):
                    downloaded_files.append(os.path.join(root, file))

        # Sort files to ensure consistent ordering
        downloaded_files.sort()

        return downloaded_files, post_url, description, username, fullname

    except Exception as e:
        logger.error(f"Error downloading media: {e}")
        return None, None, None, None, None

def delete_file(file_path):
    """Delete a file safely"""
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
    except Exception as e:
        logger.error(f"Error deleting file {file_path}: {e}")

async def send_media(update: Update, context: ContextTypes.DEFAULT_TYPE, file_paths, post_url, description, fullname, username):
    """Send media files to user"""
    chat_id = update.effective_chat.id

    file_caption = f"{description}\n\nBy: {fullname} ({username})\n{post_url}"

    # If there's more than one file, send as media group
    if len(file_paths) > 1:
        media_items = []
        files_to_delete = []

        # Create all media items first
        # Optimized version: Properly manage file handles and simplify logic
        file_handles = []  # Keep track of open file handles for proper cleanup
        for i, file_path in enumerate(file_paths):
            # Create caption only for the first file of each group
            caption = file_caption if i == 0 else None

            try:
                if file_path.lower().endswith(('.jpg', '.jpeg', '.png', '.webp')):
                    file_handle = open(file_path, 'rb')
                    file_handles.append(file_handle)
                    media_items.append((InputMediaPhoto(media=file_handle, caption=caption), file_path))
                elif file_path.lower().endswith(('.mp4', '.avi', '.mov', '.mkv', '.webm')):
                    file_handle = open(file_path, 'rb')
                    file_handles.append(file_handle)
                    media_items.append((InputMediaVideo(media=file_handle, caption=caption), file_path))
                else:
                    # For unsupported media group types, log error and delete file
                    logger.warning(f"Unsupported media type for media group: {file_path}")
                    delete_file(file_path)
            except Exception as e:
                logger.error(f"Error opening file {file_path}: {e}")
                # Clean up any opened file handles before continuing
                for handle in file_handles:
                    try:
                        handle.close()
                    except:
                        pass
                file_handles.clear()
                # Try to delete the problematic file
                delete_file(file_path)
        # Send media group if we have any items
        # if media_group len >10, seperate into multiple album.
        if media_items:
            # Split media items into groups of 10 (Telegram's limit)
            for i in range(0, len(media_items), 10):
                media_group = media_items[i:i+10]
                media_group_items = [item[0] for item in media_group]
                group_files = [item[1] for item in media_group]

                try:
                    await context.bot.send_media_group(chat_id=chat_id, media=media_group_items)
                    # Delete files after successful send
                    for file_path in group_files:
                        delete_file(file_path)
                except Exception as e:
                    logger.error(f"Unexpected error sending media group: {e}")
                    # Send error message for the first group
                    if i == 0:
                        await context.bot.send_message(chat_id=chat_id, text=f"Error sending media group: {str(e)}")
                    # Delete files even if sending failed
                    for file_path in group_files:
                        delete_file(file_path)
                finally:
                    # Always close file handles
                    for media_item, _ in media_group:
                        try:
                            # Close the underlying file handle
                            if hasattr(media_item.media, 'close'):
                                media_item.media.close()
                        except Exception as e:
                            logger.error(f"Error closing file handle: {e}")
    else:
        # Single file - send normally
        for i, file_path in enumerate(file_paths):
            file_handle = None
            try:
                caption = file_caption if i == 0 else None

                if file_path.lower().endswith(('.mp4', '.avi', '.mov', '.mkv', '.webm')):
                    file_handle = open(file_path, 'rb')
                    await context.bot.send_video(chat_id=chat_id, video=file_handle, caption=caption)
                elif file_path.lower().endswith(('.jpg', '.jpeg', '.png', '.gif', '.webp')):
                    file_handle = open(file_path, 'rb')
                    await context.bot.send_photo(chat_id=chat_id, photo=file_handle, caption=caption)
                else:
                    file_handle = open(file_path, 'rb')
                    await context.bot.send_document(chat_id=chat_id, document=file_handle, caption=caption)

                # Delete file after successful send
                delete_file(file_path)

            except Exception as e:
                logger.error(f"Error sending file {file_path}: {e}")
                # Delete file even if sending failed
                delete_file(file_path)
            finally:
                # Always close file handle
                if file_handle:
                    try:
                        file_handle.close()
                    except Exception as e:
                        logger.error(f"Error closing file handle: {e}")

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

    # Clean URL by removing tracking parameters
    clean_url_str = clean_url(url)

    # Instead send message, use chat action upload_document
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="upload_document")

    # Download media
    file_paths, post_url, description, username, fullname = download_media(clean_url_str)

    if file_paths is None:
        # Send error message if download failed
        # Try to delete user's message
        try:
            await update.message.delete()
        except Exception as e:
            logger.warning(f"Could not delete user's message: {e}")
        return

    if not file_paths:
        # Send message if no media found
        # Try to delete user's message
        try:
            await update.message.delete()
        except Exception as e:
            logger.warning(f"Could not delete user's message: {e}")
        return

    # Try to delete user's message
    try:
        await update.message.delete()
    except Exception as e:
        logger.warning(f"Could not delete user's message: {e}")

    # Send media
    await send_media(update, context, file_paths, post_url, description, fullname, username)

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
