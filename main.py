#!/usr/bin/env python3
"""
Telegram Link Swap Bot

A Telegram bot that automatically replaces links in messages with a specified link
while preserving media and text content.

Usage:
    python main.py

Environment Variables:
    BOT_TOKEN: Telegram bot token (defaults to provided token)
    REPLACEMENT_LINK: Link to replace all detected links with (defaults to provided link)
"""

import sys
import signal
from config import logger
from bot import TelegramLinkSwapBot

def signal_handler(sig, frame):
    """Handle shutdown signals gracefully."""
    logger.info("Received shutdown signal. Stopping bot...")
    sys.exit(0)

def main():
    """Main entry point for the bot."""
    # Set up signal handlers for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    logger.info("Initializing Telegram Link Swap Bot...")
    
    try:
        # Create and run the bot
        bot = TelegramLinkSwapBot()
        logger.info("Bot initialized successfully")
        
        # Start the bot
        bot.run()
        
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Fatal error occurred: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
