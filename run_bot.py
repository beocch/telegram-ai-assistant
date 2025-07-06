#!/usr/bin/env python3
"""
Quick start script for Telegram AI Assistant
Use this for testing and development
"""

import asyncio
import sys
from pathlib import Path

# Add src to Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from main import TelegramAIAssistant
from src.utils.logger import setup_logger

async def run_bot():
    """Run the bot in development mode"""
    # Setup logger
    logger = setup_logger(log_file="logs/bot.log")
    
    logger.info("🚀 Starting Telegram AI Assistant in development mode...")
    
    # Create bot instance
    bot = TelegramAIAssistant()
    
    try:
        # Initialize bot
        if not await bot.initialize():
            logger.error("❌ Failed to initialize bot. Exiting.")
            return
        
        logger.info("✅ Bot initialized successfully!")
        logger.info("📡 Running in POLLING mode (development)")
        logger.info("🤖 Bot is ready to receive messages!")
        logger.info("🛑 Press Ctrl+C to stop the bot")
        
        # Start bot
        await bot.start()
        
    except KeyboardInterrupt:
        logger.info("🛑 Received keyboard interrupt, shutting down...")
    except Exception as e:
        logger.error(f"❌ Unexpected error: {str(e)}")
    finally:
        await bot.stop()

if __name__ == "__main__":
    # Create necessary directories
    Path("logs").mkdir(exist_ok=True)
    Path("data").mkdir(exist_ok=True)
    
    # Run the bot
    asyncio.run(run_bot()) 