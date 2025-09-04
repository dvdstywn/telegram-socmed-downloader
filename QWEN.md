# Telegram Gallery-DL Bot - Project Documentation

## Project Overview
This is a Telegram bot that downloads media from URLs using gallery-dl. The bot automatically detects URLs in messages and downloads the associated media content, sending it back to the user with metadata.

## Key Features
- No command handlers needed - just send a URL directly to the bot
- Downloads images, videos, and other media from supported sites
- Sends media back with a caption containing the original post link
- Automatically removes tracking parameters from URLs
- Supports sending multiple media files as albums
- Uses a virtual environment to avoid affecting system packages
- Automatically deletes user messages after processing to keep chat clean

## Main Components

### `bot.py`
The main Telegram bot implementation that:
- Listens for messages containing URLs
- Uses gallery-dl to download media from those URLs
- Cleans URLs by removing tracking parameters
- Sends downloaded media back to users
- Automatically deletes user messages after processing

### Social Media Automation Scripts
- `instagram_login.py`: Logs into Instagram using Playwright and saves session cookies
- `twitter_login.py`: Logs into Twitter using Playwright and saves session cookies

### Configuration Files
- `accounts/config.json`: gallery-dl configuration with session cookie paths
- `.env.example`: Template for environment variables

## Setup and Configuration

### Prerequisites
1. Python 3.x
2. Telegram bot token from BotFather
3. Social media credentials (optional, for authenticated downloads)

### Installation
1. Create a virtual environment:
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Install Playwright browsers:
   ```bash
   playwright install chromium
   ```

4. Set up environment variables by copying `.env.example` to `.env` and filling in your credentials:
   ```bash
   cp .env.example .env
   # Edit .env with your actual credentials
   ```

### Environment Variables
- `TELEGRAM_BOT_TOKEN`: Your Telegram bot token from BotFather
- `TWITTER_USERNAME`: Your Twitter username or email (optional)
- `TWITTER_PASSWORD`: Your Twitter password (optional)
- `INSTAGRAM_USERNAME`: Your Instagram username (optional)
- `INSTAGRAM_PASSWORD`: Your Instagram password (optional)

## Usage

### Running the Bot
```bash
python bot.py
```

Simply send any URL to the bot, and it will download and send back the media from that URL.

### Social Media Session Management
Run the login scripts to create session cookies for authenticated downloads:

For Twitter:
```bash
python twitter_login.py
```

For Instagram:
```bash
python instagram_login.py
```

Both scripts will save session cookies to the `./tmp` directory for faster subsequent logins.

## Supported Sites
This bot uses gallery-dl, which supports a wide range of sites including:
- Instagram
- Twitter
- TikTok
- Reddit
- And many more...

For a complete list of supported sites, see the [gallery-dl documentation](https://github.com/mikf/gallery-dl).

## File Structure
```
.
├── accounts/
│   └── config.json          # gallery-dl configuration
├── tmp/                     # Temporary download directory
├── bot.py                   # Main bot implementation
├── instagram_login.py       # Instagram session management
├── twitter_login.py         # Twitter session management
├── requirements.txt         # Python dependencies
├── .env.example             # Environment variable template
└── README.md                # Project README
```

## Troubleshooting
- If downloads fail, ensure your gallery-dl is up to date
- For social media downloads, make sure session cookies are current
- Check that the bot has proper permissions in your Telegram settings