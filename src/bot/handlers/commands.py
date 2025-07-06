from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from typing import Dict, Any
import asyncio

from ...utils.logger import get_logger, log_function_call
from ...services.ai.ai_service import AIService
from ...services.database.connection import DatabaseService
from ...services.cache.redis_client import RedisClient

logger = get_logger(__name__)

class CommandHandler:
    """Handler for Telegram bot commands"""
    
    def __init__(self, ai_service: AIService = None):
        self.ai_service = ai_service
        self.db_service = None
        self.redis_client = None
    
    def set_services(self, db_service: DatabaseService, redis_client: RedisClient):
        """Set database and Redis services"""
        self.db_service = db_service
        self.redis_client = redis_client
    
    @log_function_call
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /start command"""
        user = update.effective_user
        chat_id = update.effective_chat.id
        
        welcome_message = (
            f"👋 Привет, {user.first_name}!\n\n"
            "🤖 Я AI-ассистент, готовый помочь тебе с различными задачами:\n\n"
            "• 💬 Отвечу на любые вопросы\n"
            "• 📝 Помогу с написанием текстов\n"
            "• 🔍 Проведу анализ данных\n"
            "• 🎯 Решу математические задачи\n"
            "• 🌍 Переведу тексты\n\n"
            "Просто напиши мне сообщение, и я постараюсь помочь!\n\n"
            "📋 Доступные команды:\n"
            "/help - Показать справку\n"
            "/stats - Статистика использования\n"
            "/clear - Очистить историю разговора\n"
            "/providers - Выбрать AI провайдера\n"
            "/status - Статус AI провайдеров"
        )
        
        # Create inline keyboard
        keyboard = [
            [
                InlineKeyboardButton("📋 Помощь", callback_data="help"),
                InlineKeyboardButton("📊 Статистика", callback_data="stats")
            ],
            [
                InlineKeyboardButton("🗑️ Очистить историю", callback_data="clear")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(welcome_message, reply_markup=reply_markup)
        
        # Log user interaction
        await self._log_user_interaction(chat_id, user.id, "start_command")
    
    @log_function_call
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /help command"""
        help_message = (
            "🤖 **Справка по использованию AI-ассистента**\n\n"
            "**Основные возможности:**\n"
            "• 💬 Общение и ответы на вопросы\n"
            "• 📝 Создание и редактирование текстов\n"
            "• 🔍 Анализ и обработка данных\n"
            "• 🎯 Решение задач и вычисления\n"
            "• 🌍 Перевод текстов\n"
            "• 📚 Объяснение сложных концепций\n\n"
            "**Команды:**\n"
            "/start - Начать работу с ботом\n"
            "/help - Показать эту справку\n"
            "/stats - Показать статистику использования\n"
            "/clear - Очистить историю разговора\n"
            "/providers - Выбрать AI провайдера и модель\n"
            "/status - Проверить статус AI провайдеров\n\n"
            "**Советы:**\n"
            "• Будьте конкретны в вопросах\n"
            "• Используйте контекст из предыдущих сообщений\n"
            "• Для сложных задач разбивайте их на части\n\n"
            "**Ограничения:**\n"
            "• Максимум 30 запросов в минуту\n"
            "• История разговора сохраняется на 10 сообщений\n"
            "• Размер ответа ограничен 1000 токенами"
        )
        
        await update.message.reply_text(help_message, parse_mode='Markdown')
        
        # Log user interaction
        chat_id = update.effective_chat.id
        user_id = update.effective_user.id
        await self._log_user_interaction(chat_id, user_id, "help_command")
    
    @log_function_call
    async def stats_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /stats command"""
        user_id = update.effective_user.id
        chat_id = update.effective_chat.id
        
        try:
            # Get user statistics from database
            stats = await self.db_service.get_user_stats(user_id)
            
            if stats:
                stats_message = (
                    f"📊 **Статистика использования**\n\n"
                    f"**Общая статистика:**\n"
                    f"• Всего сообщений: {stats.get('total_messages', 0)}\n"
                    f"• Сегодня: {stats.get('messages_today', 0)}\n"
                    f"• На этой неделе: {stats.get('messages_this_week', 0)}\n\n"
                    f"**Активность:**\n"
                    f"• Первое использование: {stats.get('first_used', 'Неизвестно')}\n"
                    f"• Последнее использование: {stats.get('last_used', 'Неизвестно')}\n\n"
                    f"**Токены:**\n"
                    f"• Использовано токенов: {stats.get('tokens_used', 0)}\n"
                    f"• Средняя длина ответа: {stats.get('avg_response_length', 0)} символов"
                )
            else:
                stats_message = (
                    "📊 **Статистика использования**\n\n"
                    "У вас пока нет статистики использования.\n"
                    "Начните общение с ботом, чтобы увидеть данные!"
                )
            
            await update.message.reply_text(stats_message, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Error getting stats for user {user_id}: {str(e)}")
            await update.message.reply_text(
                "❌ Произошла ошибка при получении статистики. Попробуйте позже."
            )
        
        # Log user interaction
        await self._log_user_interaction(chat_id, user_id, "stats_command")
    
    @log_function_call
    async def clear_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /clear command"""
        user_id = update.effective_user.id
        chat_id = update.effective_chat.id
        
        try:
            # Clear conversation history from Redis
            await self.redis_client.clear_conversation_history(user_id)
            
            # Clear from database if needed
            await self.db_service.clear_user_conversation(user_id)
            
            await update.message.reply_text(
                "🗑️ История разговора успешно очищена!\n\n"
                "Теперь мы начнем новый диалог. 👋"
            )
            
        except Exception as e:
            logger.error(f"Error clearing conversation for user {user_id}: {str(e)}")
            await update.message.reply_text(
                "❌ Произошла ошибка при очистке истории. Попробуйте позже."
            )
        
        # Log user interaction
        await self._log_user_interaction(chat_id, user_id, "clear_command")
    
    @log_function_call
    async def callback_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle inline keyboard callbacks"""
        query = update.callback_query
        
        # Debug logging
        logger.info(f"🔍 [COMMANDS] Received callback: {query.data} from user {query.from_user.id}")
        
        await query.answer()
        
        user_id = query.from_user.id
        chat_id = query.message.chat_id
        
        logger.info(f"🔍 [COMMANDS] Processing callback: {query.data}")
        
        try:
            if query.data == "help":
                logger.info("🔍 [COMMANDS] Handling help callback")
                await self.help_command_callback(update, context)
            elif query.data == "stats":
                logger.info("🔍 [COMMANDS] Handling stats callback")
                await self.stats_command_callback(update, context)
            elif query.data == "clear":
                logger.info("🔍 [COMMANDS] Handling clear callback")
                await self.clear_command_callback(update, context)
            elif query.data == "back_to_main":
                logger.info("🔍 [COMMANDS] Handling back to main callback")
                await self.start_command_callback(update, context)
            else:
                logger.warning(f"🔍 [COMMANDS] Unknown callback data: {query.data}")
            
            # Log user interaction
            await self._log_user_interaction(chat_id, user_id, f"callback_{query.data}")
            
        except Exception as e:
            logger.error(f"🔍 [COMMANDS] Error in callback handler: {str(e)}")
            await query.edit_message_text("❌ Произошла ошибка при обработке запроса. Попробуйте позже.")
    
    @log_function_call
    async def start_command_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /start command (callback version)"""
        query = update.callback_query
        user = query.from_user
        chat_id = query.message.chat_id
        
        welcome_message = (
            f"👋 Привет, {user.first_name}!\n\n"
            "🤖 Я AI-ассистент, готовый помочь тебе с различными задачами:\n\n"
            "• 💬 Отвечу на любые вопросы\n"
            "• 📝 Помогу с написанием текстов\n"
            "• 🔍 Проведу анализ данных\n"
            "• 🎯 Решу математические задачи\n"
            "• 🌍 Переведу тексты\n\n"
            "Просто напиши мне сообщение, и я постараюсь помочь!\n\n"
            "📋 Доступные команды:\n"
            "/help - Показать справку\n"
            "/stats - Статистика использования\n"
            "/clear - Очистить историю разговора\n"
            "/providers - Выбрать AI провайдера\n"
            "/status - Статус AI провайдеров"
        )
        
        # Create inline keyboard
        keyboard = [
            [
                InlineKeyboardButton("📋 Помощь", callback_data="help"),
                InlineKeyboardButton("📊 Статистика", callback_data="stats")
            ],
            [
                InlineKeyboardButton("🗑️ Очистить историю", callback_data="clear")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(welcome_message, reply_markup=reply_markup)
        
        # Log user interaction
        await self._log_user_interaction(chat_id, user.id, "start_command_callback")
    
    @log_function_call
    async def help_command_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /help command (callback version)"""
        query = update.callback_query
        chat_id = query.message.chat_id
        user_id = query.from_user.id
        
        help_message = (
            "🤖 **Справка по использованию AI-ассистента**\n\n"
            "**Основные возможности:**\n"
            "• 💬 Общение и ответы на вопросы\n"
            "• 📝 Создание и редактирование текстов\n"
            "• 🔍 Анализ и обработка данных\n"
            "• 🎯 Решение задач и вычисления\n"
            "• 🌍 Перевод текстов\n"
            "• 📚 Объяснение сложных концепций\n\n"
            "**Команды:**\n"
            "/start - Начать работу с ботом\n"
            "/help - Показать эту справку\n"
            "/stats - Показать статистику использования\n"
            "/clear - Очистить историю разговора\n"
            "/providers - Выбрать AI провайдера и модель\n"
            "/status - Проверить статус AI провайдеров\n\n"
            "**Советы:**\n"
            "• Будьте конкретны в вопросах\n"
            "• Используйте контекст из предыдущих сообщений\n"
            "• Для сложных задач разбивайте их на части\n\n"
            "**Ограничения:**\n"
            "• Максимум 30 запросов в минуту\n"
            "• История разговора сохраняется на 10 сообщений\n"
            "• Размер ответа ограничен 1000 токенами"
        )
        
        keyboard = [[
            InlineKeyboardButton("🔙 Назад", callback_data="back_to_main")
        ]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(help_message, reply_markup=reply_markup, parse_mode='Markdown')
        
        # Log user interaction
        await self._log_user_interaction(chat_id, user_id, "help_command_callback")
    
    @log_function_call
    async def stats_command_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /stats command (callback version)"""
        query = update.callback_query
        user_id = query.from_user.id
        chat_id = query.message.chat_id
        
        try:
            # Get user statistics from database
            stats = await self.db_service.get_user_stats(user_id) if self.db_service else None
            
            if stats:
                stats_message = (
                    f"📊 **Статистика использования**\n\n"
                    f"**Общая статистика:**\n"
                    f"• Всего сообщений: {stats.get('total_messages', 0)}\n"
                    f"• Сегодня: {stats.get('messages_today', 0)}\n"
                    f"• На этой неделе: {stats.get('messages_this_week', 0)}\n\n"
                    f"**Активность:**\n"
                    f"• Первое использование: {stats.get('first_used', 'Неизвестно')}\n"
                    f"• Последнее использование: {stats.get('last_used', 'Неизвестно')}\n\n"
                    f"**Токены:**\n"
                    f"• Использовано токенов: {stats.get('tokens_used', 0)}\n"
                    f"• Средняя длина ответа: {stats.get('avg_response_length', 0)} символов"
                )
            else:
                stats_message = (
                    "📊 **Статистика использования**\n\n"
                    "У вас пока нет статистики использования.\n"
                    "Начните общение с ботом, чтобы увидеть данные!"
                )
            
            keyboard = [[
                InlineKeyboardButton("🔙 Назад", callback_data="back_to_main")
            ]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(stats_message, reply_markup=reply_markup, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Error getting stats for user {user_id}: {str(e)}")
            await query.edit_message_text(
                "❌ Произошла ошибка при получении статистики. Попробуйте позже.",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 Назад", callback_data="back_to_main")
                ]])
            )
        
        # Log user interaction
        await self._log_user_interaction(chat_id, user_id, "stats_command_callback")
    
    @log_function_call
    async def clear_command_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /clear command (callback version)"""
        query = update.callback_query
        user_id = query.from_user.id
        chat_id = query.message.chat_id
        
        try:
            # Clear conversation history from Redis
            if self.redis_client:
                await self.redis_client.clear_conversation_history(user_id)
            
            # Clear from database if needed
            if self.db_service:
                await self.db_service.clear_user_conversation(user_id)
            
            clear_message = (
                "🗑️ История разговора успешно очищена!\n\n"
                "Теперь мы начнем новый диалог. 👋"
            )
            
            keyboard = [[
                InlineKeyboardButton("🔙 Назад", callback_data="back_to_main")
            ]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(clear_message, reply_markup=reply_markup)
            
        except Exception as e:
            logger.error(f"Error clearing conversation for user {user_id}: {str(e)}")
            await query.edit_message_text(
                "❌ Произошла ошибка при очистке истории. Попробуйте позже.",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 Назад", callback_data="back_to_main")
                ]])
            )
        
        # Log user interaction
        await self._log_user_interaction(chat_id, user_id, "clear_command_callback")
    
    async def _log_user_interaction(self, chat_id: int, user_id: int, action: str) -> None:
        """Log user interaction to database"""
        if not self.db_service:
            logger.warning("Database service not set, skipping log")
            return
            
        try:
            await self.db_service.log_user_interaction(
                user_id=user_id,
                chat_id=chat_id,
                action=action,
                message_type="command"
            )
        except Exception as e:
            logger.error(f"Error logging user interaction: {str(e)}")
    
    async def handle_error(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle errors in command processing"""
        logger.error(f"Exception while handling an update: {context.error}")
        
        if update and update.effective_message:
            await update.effective_message.reply_text(
                "❌ Произошла ошибка при обработке команды. Попробуйте позже или обратитесь к администратору."
            ) 