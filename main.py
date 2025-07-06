#!/usr/bin/env python3
"""
Telegram AI Assistant - Main Application Entry Point

This is the main entry point for the Telegram AI Assistant bot.
It initializes all services and starts the bot.
"""

import asyncio
import signal
import sys
from pathlib import Path

# Add src to Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, ConversationHandler, filters, ContextTypes

from src.utils.config import Config
from src.utils.logger import get_logger, setup_logger
from src.bot.handlers.commands import CommandHandler as BotCommandHandler
from src.bot.handlers.messages import MessageHandler as BotMessageHandler
from src.bot.handlers.ai_commands import AICommandsHandler
from src.services.database.connection import DatabaseService
from src.services.cache.redis_client import RedisClient
from src.services.ai.ai_service import AIService
from src.services.ai.openai_provider import OpenAIProvider
from src.services.ai.claude_provider import ClaudeProvider
from src.services.user_settings import UserSettingsService
from src.bot.handlers.settings_commands import SettingsCommandsHandler, WAITING_FOR_API_KEY, WAITING_FOR_PROVIDER

# Setup logger
logger = setup_logger(log_file="logs/bot.log")

class TelegramAIAssistant:
    """Main application class for Telegram AI Assistant"""
    
    def __init__(self):
        self.application = None
        self.command_handler = None
        self.message_handler = None
        self.ai_commands_handler = None
        self.settings_commands_handler = None
        self.ai_service = None
        self.db_service = None
        self.redis_client = None
        self.user_settings = None
        
    async def initialize(self):
        """Initialize all services and handlers"""
        try:
            logger.info("🚀 Initializing Telegram AI Assistant...")
            
            # Validate configuration
            if not Config.validate():
                logger.error("❌ Configuration validation failed!")
                return False
            
            # Initialize database
            logger.info("📊 Initializing database...")
            self.db_service = DatabaseService()
            await self.db_service.initialize()
            
            # Initialize Redis
            logger.info("🔴 Initializing Redis...")
            self.redis_client = RedisClient()
            await self.redis_client.initialize()
            
            # Initialize user settings service
            logger.info("⚙️ Initializing user settings service...")
            self.user_settings = UserSettingsService()
            
            # Initialize AI service with user settings
            logger.info("🤖 Initializing AI service...")
            self.ai_service = AIService(user_settings_service=self.user_settings)
            
            # Initialize default AI providers from environment
            if Config.OPENAI_API_KEY:
                openai_provider = OpenAIProvider(
                    api_key=Config.OPENAI_API_KEY,
                    model=Config.OPENAI_MODEL
                )
                openai_provider.set_parameters(
                    max_tokens=Config.OPENAI_MAX_TOKENS,
                    temperature=Config.OPENAI_TEMPERATURE
                )
                self.ai_service.add_provider("openai", openai_provider)
                logger.info("✅ OpenAI provider initialized from environment")
            
            if Config.CLAUDE_API_KEY:
                claude_provider = ClaudeProvider(
                    api_key=Config.CLAUDE_API_KEY,
                    model=Config.CLAUDE_MODEL
                )
                claude_provider.set_parameters(
                    max_tokens=Config.CLAUDE_MAX_TOKENS,
                    temperature=Config.CLAUDE_TEMPERATURE
                )
                self.ai_service.add_provider("claude", claude_provider)
                logger.info("✅ Claude provider initialized from environment")
            
            logger.info("ℹ️  AI providers can be configured via /settings command")
            
            # Initialize handlers
            logger.info("🤖 Initializing bot handlers...")
            self.command_handler = BotCommandHandler(self.ai_service)
            self.message_handler = BotMessageHandler(self.ai_service)
            self.ai_commands_handler = AICommandsHandler(self.ai_service)
            self.settings_commands_handler = SettingsCommandsHandler(self.user_settings)
            
            # Set services for handlers
            self.command_handler.set_services(self.db_service, self.redis_client)
            self.message_handler.set_services(self.db_service, self.redis_client)
            self.settings_commands_handler.set_services(self.db_service, self.redis_client)
            
            # Initialize Telegram application
            logger.info("📱 Initializing Telegram application...")
            self.application = Application.builder().token(Config.TELEGRAM_BOT_TOKEN).build()
            
            # Add handlers
            await self._setup_handlers()
            
            # Add error handler
            self.application.add_error_handler(self._error_handler)
            
            logger.info("✅ Initialization completed successfully!")
            return True
            
        except Exception as e:
            logger.error(f"❌ Initialization failed: {str(e)}")
            return False
    
    async def _setup_handlers(self):
        """Setup all bot handlers"""
        # Settings commands with conversation handler (ConversationHandler должен быть ПЕРВЫМ)
        async def settings_entry_point(update: Update, context: ContextTypes.DEFAULT_TYPE):
            logger.info("🔍 [CONV] Settings entry point called!")
            return await self.settings_commands_handler.show_settings(update, context)
        
        async def settings_api_key_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
            logger.info("🔍 [CONV] Settings API key handler called!")
            return await self.settings_commands_handler.handle_api_key_input(update, context)
        
        async def settings_cancel_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
            logger.info("🔍 [CONV] Settings cancel handler called!")
            return await self.settings_commands_handler.cancel(update, context)
        
        # Добавляем обработчик для перехода в состояние добавления API ключа
        async def settings_add_key_entry(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
            logger.info("🔍 [CONV] Settings add key entry called!")
            return await self.settings_commands_handler.start_add_api_key(update, context)
        
        # Settings conversation handler
        settings_conversation = ConversationHandler(
            entry_points=[
                CommandHandler("settings", settings_entry_point),
                CallbackQueryHandler(settings_add_key_entry, pattern="^add_key_")
            ],
            states={
                WAITING_FOR_API_KEY: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, settings_api_key_handler),
                    CommandHandler("cancel", settings_cancel_handler)
                ]
            },
            fallbacks=[CommandHandler("cancel", settings_cancel_handler)],
            name="settings_conversation",
            persistent=False
        )
        self.application.add_handler(settings_conversation)
        
        # Command handlers
        self.application.add_handler(CommandHandler("start", self.command_handler.start_command))
        self.application.add_handler(CommandHandler("help", self.command_handler.help_command))
        self.application.add_handler(CommandHandler("stats", self.command_handler.stats_command))
        self.application.add_handler(CommandHandler("clear", self.command_handler.clear_command))
        
        # Settings command (fallback)
        self.application.add_handler(CommandHandler("settings", self.settings_commands_handler.show_settings))
        
        # AI provider commands
        self.application.add_handler(CommandHandler("providers", self.ai_commands_handler.show_providers))
        self.application.add_handler(CommandHandler("status", self.ai_commands_handler.show_provider_status))
        
        # Callback query handlers with proper filtering
        # Basic commands (help, stats, clear, back_to_main)
        self.application.add_handler(
            CallbackQueryHandler(
                self.command_handler.callback_handler,
                pattern="^(help|stats|clear|back_to_main)$"
            )
        )
        
        # AI provider callbacks (provider_*, model_*, providers_back)
        self.application.add_handler(
            CallbackQueryHandler(
                self.ai_commands_handler.handle_callback,
                pattern="^(provider_|model_|providers_back)"
            )
        )
        
        # Settings callbacks (add_api_key, remove_api_key, select_provider, etc.)
        # ИСКЛЮЧАЕМ add_key_ из CallbackQueryHandler, так как это обрабатывается ConversationHandler
        async def settings_callback_wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
            logger.info(f"🔍 [CALLBACK] Settings callback received: {update.callback_query.data}")
            return await self.settings_commands_handler.handle_callback(update, context)
        
        self.application.add_handler(
            CallbackQueryHandler(
                settings_callback_wrapper,
                pattern="^(add_api_key|remove_api_key|select_provider|remove_key_|back_to_settings|user_stats)"
            )
        )
        
        # Message handlers (должны быть ПОСЛЕ ConversationHandler)
        self.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.message_handler.handle_message))
        self.application.add_handler(MessageHandler(filters.PHOTO, self.message_handler.handle_photo))
        self.application.add_handler(MessageHandler(filters.Document.ALL, self.message_handler.handle_document))
        self.application.add_handler(MessageHandler(filters.VOICE, self.message_handler.handle_voice))
        # Note: STICKER handling temporarily disabled due to filter compatibility issues
        # self.application.add_handler(MessageHandler(filters.STICKER, self.message_handler.handle_sticker))
        
        logger.info("✅ Handlers setup completed")
    
    async def _error_handler(self, update: Update, context):
        """Handle errors in bot processing"""
        logger.error(f"Exception while handling an update: {context.error}")
        
        if update and update.effective_message:
            await update.effective_message.reply_text(
                "❌ Произошла ошибка при обработке сообщения. Попробуйте позже или обратитесь к администратору."
            )
    
    async def start(self):
        """Start the bot"""
        try:
            logger.info("🤖 Starting Telegram AI Assistant...")
            
            # Start the application
            await self.application.initialize()
            await self.application.start()
            
            # Check if webhook URL is configured
            if Config.TELEGRAM_WEBHOOK_URL and Config.TELEGRAM_WEBHOOK_URL != "https://your-domain.com/webhook":
                logger.info(f"🌐 Starting in webhook mode: {Config.TELEGRAM_WEBHOOK_URL}")
                await self.application.bot.set_webhook(url=Config.TELEGRAM_WEBHOOK_URL)
                logger.info("✅ Webhook set successfully!")
            else:
                logger.info("📡 Starting in polling mode...")
                await self.application.updater.start_polling()
                logger.info("✅ Bot started successfully in polling mode! Press Ctrl+C to stop.")
                # Keep the bot running with interruptible loop
                try:
                    while True:
                        await asyncio.sleep(1)
                except asyncio.CancelledError:
                    logger.info("🛑 Bot shutdown requested")
            
        except Exception as e:
            logger.error(f"❌ Failed to start bot: {str(e)}")
            raise
    
    async def stop(self):
        """Stop the bot gracefully"""
        try:
            logger.info("🛑 Stopping Telegram AI Assistant...")
            
            if self.application:
                await self.application.updater.stop()
                await self.application.stop()
                await self.application.shutdown()
            
            if self.redis_client:
                await self.redis_client.close()
            
            if self.db_service:
                await self.db_service.close()
            
            logger.info("✅ Bot stopped successfully!")
            
        except Exception as e:
            logger.error(f"❌ Error stopping bot: {str(e)}")

async def main():
    """Main function"""
    bot = TelegramAIAssistant()
    
    # Setup signal handlers for graceful shutdown
    def signal_handler(signum, frame):
        logger.info(f"Received signal {signum}, shutting down gracefully...")
        asyncio.create_task(bot.stop())
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        # Initialize bot
        if not await bot.initialize():
            logger.error("❌ Failed to initialize bot. Exiting.")
            return
        
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
    asyncio.run(main()) 