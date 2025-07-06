from telegram import Update
from telegram.ext import ContextTypes
from typing import List, Dict, Any
import asyncio
import time

from ...utils.logger import get_logger, log_function_call, log_execution_time
from ...utils.config import Config
from ...services.ai.ai_service import AIService
from ...services.database.connection import DatabaseService
from ...services.cache.redis_client import RedisClient

logger = get_logger(__name__)

class MessageHandler:
    """Handler for processing user messages with AI"""
    
    def __init__(self, ai_service: AIService = None):
        self.ai_service = ai_service
        self.db_service = None  # Will be initialized later
        self.redis_client = None  # Will be initialized later
        self.rate_limit_cache = {}
    
    def set_services(self, db_service, redis_client):
        """Set database and Redis services"""
        self.db_service = db_service
        self.redis_client = redis_client
    
    @log_function_call
    @log_execution_time
    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Main message handler"""
        user = update.effective_user
        chat_id = update.effective_chat.id
        message_text = update.message.text
        
        # Check if this is a command (should be handled by command handlers)
        if message_text.startswith('/'):
            return
        
        # Check if user is in conversation state (settings, etc.)
        if context.user_data.get('conversation_state'):
            logger.info(f"User {user.id} is in conversation state, skipping message handler")
            return
        
        # Check rate limiting
        if not await self._check_rate_limit(user.id):
            await update.message.reply_text(
                "⚠️ Слишком много запросов! Пожалуйста, подождите немного перед следующим сообщением."
            )
            return
        
        # Send typing indicator
        await context.bot.send_chat_action(chat_id=chat_id, action="typing")
        
        try:
            # Get conversation history
            conversation_history = await self._get_conversation_history(user.id)
            
            # Generate AI response
            response = await self._generate_ai_response(message_text, conversation_history, user.id)
            
            # Send response
            await update.message.reply_text(response)
            
            # Update conversation history
            await self._update_conversation_history(user.id, message_text, response)
            
            # Log interaction
            await self._log_user_interaction(chat_id, user.id, "message", len(message_text), len(response))
            
        except Exception as e:
            logger.error(f"Error processing message for user {user.id}: {str(e)}")
            await update.message.reply_text(
                "❌ Произошла ошибка при обработке сообщения. Попробуйте позже или обратитесь к администратору."
            )
    
    async def _check_rate_limit(self, user_id: int) -> bool:
        """Check if user is within rate limits"""
        current_time = time.time()
        minute_ago = current_time - 60
        
        # Get user's recent requests
        user_requests = self.rate_limit_cache.get(user_id, [])
        
        # Remove old requests (older than 1 minute)
        user_requests = [req_time for req_time in user_requests if req_time > minute_ago]
        
        # Check if user has exceeded rate limit
        if len(user_requests) >= Config.RATE_LIMIT_PER_MINUTE:
            return False
        
        # Add current request
        user_requests.append(current_time)
        self.rate_limit_cache[user_id] = user_requests
        
        return True
    
    async def _get_conversation_history(self, user_id: int) -> List[Dict[str, str]]:
        """Get conversation history from Redis"""
        try:
            if self.redis_client:
                history = await self.redis_client.get_conversation_history(user_id)
                return history or []
            else:
                return []
        except Exception as e:
            logger.error(f"Error getting conversation history for user {user_id}: {str(e)}")
            return []
    
    async def _generate_ai_response(self, message: str, history: List[Dict[str, str]], user_id: int) -> str:
        """Generate AI response using selected provider"""
        try:
            # Prepare conversation context
            messages = self._prepare_conversation_context(message, history)
            
            # Generate response using AI service
            if self.ai_service:
                response = await self.ai_service.generate_response(messages, user_id)
            else:
                # Fallback response if no AI service available
                response = "Извините, AI сервис временно недоступен. Попробуйте позже."
            
            return response
            
        except Exception as e:
            logger.error(f"Error generating AI response for user {user_id}: {str(e)}")
            raise
    
    def _prepare_conversation_context(self, current_message: str, history: List[Dict[str, str]]) -> List[Dict[str, str]]:
        """Prepare conversation context for AI"""
        messages = [
            {
                "role": "system",
                "content": (
                    "Ты - полезный AI-ассистент в Telegram боте. "
                    "Отвечай кратко, но информативно. "
                    "Используй эмодзи для лучшего восприятия. "
                    "Будь дружелюбным и готовым помочь. "
                    "Если не знаешь ответа, честно скажи об этом."
                )
            }
        ]
        
        # Add conversation history (limited to last N messages)
        max_history = Config.MAX_CONVERSATION_HISTORY
        recent_history = history[-max_history:] if len(history) > max_history else history
        
        for msg in recent_history:
            messages.append({
                "role": msg.get("role", "user"),
                "content": msg.get("content", "")
            })
        
        # Add current message
        messages.append({
            "role": "user",
            "content": current_message
        })
        
        return messages
    
    async def _update_conversation_history(self, user_id: int, user_message: str, ai_response: str) -> None:
        """Update conversation history in Redis"""
        try:
            if self.redis_client:
                # Add user message and AI response to history
                await self.redis_client.add_to_conversation_history(
                    user_id=user_id,
                    user_message=user_message,
                    ai_response=ai_response
                )
        except Exception as e:
            logger.error(f"Error updating conversation history for user {user_id}: {str(e)}")
    
    async def _log_user_interaction(
        self, 
        chat_id: int, 
        user_id: int, 
        action: str, 
        message_length: int = 0, 
        response_length: int = 0
    ) -> None:
        """Log user interaction to database"""
        try:
            if self.db_service:
                await self.db_service.log_user_interaction(
                    user_id=user_id,
                    chat_id=chat_id,
                    action=action,
                    message_type="message",
                    message_length=message_length,
                    response_length=response_length
                )
        except Exception as e:
            logger.error(f"Error logging user interaction: {str(e)}")
    
    async def handle_photo(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle photo messages"""
        user = update.effective_user
        chat_id = update.effective_chat.id
        
        await update.message.reply_text(
            "📸 Я вижу, что вы отправили фото!\n\n"
            "К сожалению, я пока не могу анализировать изображения. "
            "Пожалуйста, опишите, что вы хотели бы узнать, текстом."
        )
        
        # Log interaction
        await self._log_user_interaction(chat_id, user.id, "photo")
    
    async def handle_document(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle document messages"""
        user = update.effective_user
        chat_id = update.effective_chat.id
        
        await update.message.reply_text(
            "📄 Я вижу, что вы отправили документ!\n\n"
            "К сожалению, я пока не могу обрабатывать файлы. "
            "Пожалуйста, скопируйте текст из документа в сообщение."
        )
        
        # Log interaction
        await self._log_user_interaction(chat_id, user.id, "document")
    
    async def handle_voice(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle voice messages"""
        user = update.effective_user
        chat_id = update.effective_chat.id
        
        await update.message.reply_text(
            "🎤 Я вижу, что вы отправили голосовое сообщение!\n\n"
            "К сожалению, я пока не могу обрабатывать аудио. "
            "Пожалуйста, напишите ваш вопрос текстом."
        )
        
        # Log interaction
        await self._log_user_interaction(chat_id, user.id, "voice")
    
    async def handle_sticker(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle sticker messages"""
        user = update.effective_user
        chat_id = update.effective_chat.id
        
        await update.message.reply_text(
            "😊 Спасибо за стикер! Но я лучше понимаю текстовые сообщения.\n\n"
            "Напишите, что вас интересует, и я постараюсь помочь!"
        )
        
        # Log interaction
        await self._log_user_interaction(chat_id, user.id, "sticker") 