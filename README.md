# LICENSE

ya pokoknya MIT, pokoknya asal ada license. toh ini dibuat sambil makan siang, makanya ada token telegram di sana karena saya percaya AI!
dibuat karena bot yang biasa ku pake tiba2 sering return ddinstagram. D:

jangan percaya yagn ada di bawah2 sini, soalnya ini generate AI

# Telegram Gallery-DL Bot

A Telegram bot that downloads media from URLs using gallery-dl.

## Features

- No command handlers needed - just send a URL directly to the bot
- Downloads images, videos, and other media from supported sites
- Sends media back with a caption containing the original post link
- Automatically removes tracking parameters from URLs
- Supports sending multiple media files as albums
- Uses a virtual environment to avoid affecting system packages
- Automatically deletes user messages after processing to keep chat clean

## Setup

1. Create a virtual environment:
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Set your Telegram bot token as an environment variable:
   ```bash
   export TELEGRAM_BOT_TOKEN="your_bot_token_here"
   ```
   
   Or on Windows:
   ```cmd
   set TELEGRAM_BOT_TOKEN=your_bot_token_here
   ```

4. Run the bot:
   ```bash
   python bot.py
   ```

## Usage

Simply send any URL to the bot, and it will download and send back the media from that URL. The bot will automatically detect URLs in messages.

The output format is:
```
[media] [caption] [link to the post user downloaded]
```

## Supported Sites

This bot uses gallery-dl, which supports a wide range of sites including:
- Instagram
- Twitter
- TikTok
- Reddit
- And many more...

For a complete list of supported sites, see the [gallery-dl documentation](https://github.com/mikf/gallery-dl).

## Social Media Automation

This project also includes social media automation scripts using Playwright:

### Setup

1. Install Playwright dependencies:
   ```bash
   source venv/bin/activate
   playwright install chromium
   ```

2. Create a `.env` file with your social media credentials:
   ```
   TWITTER_USERNAME=your_username_or_email
   TWITTER_PASSWORD=your_password
   INSTAGRAM_USERNAME=your_instagram_username
   INSTAGRAM_PASSWORD=your_instagram_password
   ```

### Scripts

- `twitter_login.py` - Log into Twitter and save session cookies
- `instagram_login.py` - Log into Instagram and save session cookies

### Usage

Run the Twitter login script:
```bash
python twitter_login.py
```

Run the Instagram login script:
```bash
python instagram_login.py
```

Both scripts will save session cookies to the `./tmp` directory for faster subsequent logins.