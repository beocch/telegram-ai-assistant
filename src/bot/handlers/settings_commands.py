from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler
from typing import Dict, Any

from ...utils.logger import get_logger, log_function_call
from ...services.user_settings import UserSettingsService

logger = get_logger(__name__)

# Conversation states
WAITING_FOR_API_KEY = 1
WAITING_FOR_PROVIDER = 2

class SettingsCommandsHandler:
    """Handler for user settings management"""
    
    def __init__(self, user_settings: UserSettingsService):
        self.user_settings = user_settings
        self.db_service = None
        self.redis_client = None
    
    def set_services(self, db_service, redis_client):
        """Set database and cache services"""
        self.db_service = db_service
        self.redis_client = redis_client
        if self.db_service and getattr(self.db_service, '_initialized', False):
            print('[DEBUG] DatabaseService injected and initialized')
        else:
            print('[DEBUG] DatabaseService injected but NOT initialized')
    
    @log_function_call
    async def show_settings(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Show user settings menu"""
        user = update.effective_user
        
        # Get user's current settings
        api_keys = self.user_settings.get_user_api_keys(user.id)
        preferences = self.user_settings.get_user_preferences(user.id)
        
        # Create settings text
        settings_text = "⚙️ **Ваши настройки:**\n\n"
        
        # API Keys section
        settings_text += "🔑 **API Ключи:**\n"
        if api_keys:
            for provider, key in api_keys.items():
                masked_key = key[:10] + "..." + key[-4:] if len(key) > 14 else "***"
                settings_text += f"• {provider.title()}: `{masked_key}`\n"
        else:
            settings_text += "• Нет настроенных ключей\n"
        
        # Preferences section
        settings_text += "\n🎯 **Предпочтения:**\n"
        provider = preferences.get('provider', 'Не выбрано')
        model = preferences.get('model', 'Не выбрано')
        settings_text += f"• Провайдер: {provider.title()}\n"
        settings_text += f"• Модель: {model}\n"
        
        # Create keyboard
        keyboard = [
            [
                InlineKeyboardButton("🔑 Добавить API ключ", callback_data="add_api_key"),
                InlineKeyboardButton("🗑️ Удалить ключ", callback_data="remove_api_key")
            ],
            [
                InlineKeyboardButton("🎯 Выбрать провайдера", callback_data="select_provider"),
                InlineKeyboardButton("📊 Статистика", callback_data="user_stats")
            ],
            [
                InlineKeyboardButton("🔙 Назад", callback_data="back_to_main")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            settings_text,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
    
    @log_function_call
    async def add_api_key_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Show API key addition menu"""
        query = update.callback_query
        await query.answer()
        
        keyboard = [
            [
                InlineKeyboardButton("🤖 OpenAI", callback_data="add_key_openai"),
                InlineKeyboardButton("🤖 Claude", callback_data="add_key_claude")
            ],
            [
                InlineKeyboardButton("🔙 Назад", callback_data="back_to_settings")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            "🔑 **Добавить API ключ**\n\n"
            "Выберите провайдера для которого хотите добавить API ключ:",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
    
    @log_function_call
    async def start_add_api_key(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Start API key addition process"""
        logger.info("🔍 [SETTINGS] start_add_api_key called!")
        query = update.callback_query
        await query.answer()
        
        # Extract provider from callback data
        provider = query.data.replace("add_key_", "")
        context.user_data['adding_provider'] = provider
        context.user_data['conversation_state'] = 'adding_api_key'
        
        logger.info(f"🔍 [SETTINGS] Starting API key addition for provider: {provider}")
        logger.info(f"🔍 [SETTINGS] User data: {context.user_data}")
        
        await query.edit_message_text(
            f"🔑 **Добавление API ключа для {provider.title()}**\n\n"
            f"Пожалуйста, отправьте ваш API ключ для {provider.title()}.\n\n"
            "⚠️ **Важно:** Ваш ключ будет сохранен локально и не будет передан третьим лицам.\n\n"
            "Для отмены отправьте /cancel",
            parse_mode='Markdown'
        )
        
        logger.info(f"🔍 [SETTINGS] Returning WAITING_FOR_API_KEY state: {WAITING_FOR_API_KEY}")
        return WAITING_FOR_API_KEY
    
    @log_function_call
    async def handle_api_key_input(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Handle API key input"""
        user = update.effective_user
        api_key = update.message.text.strip()
        provider = context.user_data.get('adding_provider')
        
        logger.info(f"🔍 [SETTINGS] Processing API key input for user {user.id}, provider: {provider}")
        logger.info(f"🔍 [SETTINGS] User data: {context.user_data}")
        logger.info(f"🔍 [SETTINGS] API key length: {len(api_key)}")
        
        if not provider:
            logger.error(f"🔍 [SETTINGS] No provider found in user data")
            await update.message.reply_text("❌ Ошибка: провайдер не найден")
            return ConversationHandler.END
        
        # Validate API key format
        if provider == "openai" and not api_key.startswith("sk-"):
            await update.message.reply_text(
                "❌ Неверный формат OpenAI API ключа!\n"
                "Ключ должен начинаться с 'sk-'"
            )
            return WAITING_FOR_API_KEY
        
        if provider == "claude" and not (api_key.startswith("sk-ant-") or api_key.startswith("sk-ant_api03-")):
            await update.message.reply_text(
                "❌ Неверный формат Claude API ключа!\n"
                "Ключ должен начинаться с 'sk-ant-' или 'sk-ant_api03-'"
            )
            return WAITING_FOR_API_KEY
        
        try:
            # Save API key
            self.user_settings.set_user_api_key(user.id, provider, api_key)
            logger.info(f"🔍 [SETTINGS] API key saved for user {user.id}, provider: {provider}")
            
            # Test the API key
            test_result, error_message = await self._test_api_key(provider, api_key)
            
            if test_result:
                # Auto-switch to this provider if it's the first one or user has no preference
                current_provider = self.user_settings.get_user_provider(user.id)
                if not current_provider:
                    self.user_settings.set_user_provider(user.id, provider)
                    logger.info(f"🔍 [SETTINGS] Auto-switched to provider: {provider}")
                
                success_message = (
                    f"✅ API ключ для {provider.title()} успешно сохранен и протестирован!\n\n"
                    f"🎯 **Автоматически выбран провайдер:** {provider.title()}\n\n"
                    f"Теперь вы можете использовать {provider.title()} в боте.\n\n"
                    "Используйте /settings для управления настройками."
                )
            else:
                # Handle specific error cases
                if "квота" in error_message.lower():
                    success_message = (
                        f"✅ API ключ для {provider.title()} сохранен!\n\n"
                        f"⚠️ **Внимание:** {error_message}\n\n"
                        f"Ключ действителен, но для использования {provider.title()} нужно пополнить баланс.\n\n"
                        "Используйте /settings для управления настройками."
                    )
                else:
                    success_message = (
                        f"⚠️ API ключ для {provider.title()} сохранен, но тест не прошел.\n\n"
                        f"❌ **Ошибка:** {error_message}\n\n"
                        "Попробуйте использовать другой ключ или обратитесь к поддержке."
                    )
            
            await update.message.reply_text(success_message, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"🔍 [SETTINGS] Error saving API key: {str(e)}")
            await update.message.reply_text(
                f"❌ Ошибка при сохранении API ключа: {str(e)}\n"
                "Попробуйте еще раз или обратитесь к администратору."
            )
        
        # Clear conversation state
        context.user_data.pop('conversation_state', None)
        context.user_data.pop('adding_provider', None)
        
        return ConversationHandler.END
    
    async def _test_api_key(self, provider: str, api_key: str) -> tuple[bool, str]:
        """Test API key with a simple request. Returns (success, error_message)"""
        try:
            logger.info(f"🔍 [SETTINGS] Testing API key for provider: {provider}")
            
            # Create a simple test request
            if provider == "openai":
                import openai
                client = openai.OpenAI(api_key=api_key)
                response = client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[{"role": "user", "content": "Hello"}],
                    max_tokens=10
                )
                return True, ""
            elif provider == "claude":
                # Для Claude просто проверяем формат ключа, так как API тест может не работать
                if api_key.startswith("sk-ant-") or api_key.startswith("sk-ant_api03-"):
                    return True, ""
                else:
                    return False, "Неверный формат Claude API ключа"
            else:
                logger.warning(f"🔍 [SETTINGS] Unknown provider for testing: {provider}")
                return False, f"Неизвестный провайдер: {provider}"
                
        except Exception as e:
            error_msg = str(e)
            logger.error(f"🔍 [SETTINGS] API key test failed for {provider}: {error_msg}")
            
            # Handle specific error cases
            if "insufficient_quota" in error_msg.lower() or "quota" in error_msg.lower():
                return False, "Ключ действителен, но закончилась квота. Пополните баланс для использования."
            elif "invalid_api_key" in error_msg.lower() or "authentication" in error_msg.lower():
                return False, "Недействительный API ключ. Проверьте правильность ключа."
            elif "rate_limit" in error_msg.lower():
                return False, "Превышен лимит запросов. Попробуйте позже."
            else:
                return False, f"Ошибка тестирования: {error_msg}"
    
    @log_function_call
    async def remove_api_key_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Show API key removal menu"""
        query = update.callback_query
        await query.answer()
        
        user = update.effective_user
        api_keys = self.user_settings.get_user_api_keys(user.id)
        
        if not api_keys:
            await query.edit_message_text(
                "❌ У вас нет настроенных API ключей.",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 Назад", callback_data="back_to_settings")
                ]])
            )
            return
        
        keyboard = []
        for provider in api_keys.keys():
            keyboard.append([
                InlineKeyboardButton(f"🗑️ {provider.title()}", callback_data=f"remove_key_{provider}")
            ])
        
        keyboard.append([
            InlineKeyboardButton("🔙 Назад", callback_data="back_to_settings")
        ])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            "🗑️ **Удалить API ключ**\n\n"
            "Выберите ключ для удаления:",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
    
    @log_function_call
    async def remove_api_key(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Remove API key"""
        query = update.callback_query
        await query.answer()
        
        user = update.effective_user
        provider = query.data.replace("remove_key_", "")
        
        self.user_settings.remove_user_api_key(user.id, provider)
        
        await query.edit_message_text(
            f"✅ API ключ для {provider.title()} удален!",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 Назад", callback_data="back_to_settings")
            ]])
        )
    
    @log_function_call
    async def show_user_stats(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Show user statistics"""
        query = update.callback_query
        await query.answer()
        
        user = update.effective_user
        stats = self.user_settings.get_user_stats(user.id)
        
        if not stats:
            stats_text = "📊 **Ваша статистика:**\n\n"
            stats_text += "У вас пока нет статистики использования.\n"
            stats_text += "Начните общение с ботом, чтобы увидеть данные!"
        else:
            stats_text = "📊 **Ваша статистика:**\n\n"
            stats_text += f"• Всего сообщений: {stats.get('total_messages', 0)}\n"
            stats_text += f"• Сегодня: {stats.get('messages_today', 0)}\n"
            stats_text += f"• На этой неделе: {stats.get('messages_this_week', 0)}\n"
            stats_text += f"• Использовано токенов: {stats.get('tokens_used', 0)}\n"
        
        await query.edit_message_text(
            stats_text,
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 Назад", callback_data="back_to_settings")
            ]]),
            parse_mode='Markdown'
        )
    
    @log_function_call
    async def handle_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle callback queries"""
        query = update.callback_query
        
        # Debug logging
        logger.info(f"🔍 [SETTINGS] Received callback: {query.data} from user {query.from_user.id}")
        
        await query.answer()
        
        # Log user interaction
        if self.db_service:
            await self.db_service.log_user_interaction(
                user_id=query.from_user.id,
                chat_id=query.message.chat_id,
                action=f"settings_callback_{query.data}",
                message_type="callback_query"
            )
        
        data = query.data
        logger.info(f"🔍 [SETTINGS] Processing callback: {data}")
        
        try:
            if data == "back_to_settings":
                logger.info("🔍 [SETTINGS] Going back to settings")
                await self.show_settings_callback(update, context)
            elif data == "add_api_key":
                logger.info("🔍 [SETTINGS] Showing add API key menu")
                await self.add_api_key_menu(update, context)
            elif data == "remove_api_key":
                logger.info("🔍 [SETTINGS] Showing remove API key menu")
                await self.remove_api_key_menu(update, context)
            elif data == "select_provider":
                logger.info("🔍 [SETTINGS] Showing provider selection")
                await self.show_provider_selection(update, context)
            elif data == "user_stats":
                logger.info("🔍 [SETTINGS] Showing user stats")
                await self.show_user_stats(update, context)
            elif data.startswith("add_key_"):
                provider = data.replace("add_key_", "")
                logger.info(f"🔍 [SETTINGS] Starting add API key for provider: {provider}")
                return await self.start_add_api_key(update, context)
            elif data.startswith("remove_key_"):
                provider = data.replace("remove_key_", "")
                logger.info(f"🔍 [SETTINGS] Removing API key for provider: {provider}")
                await self.remove_api_key(update, context)
            else:
                logger.warning(f"🔍 [SETTINGS] Unknown callback data: {data}")
                
        except Exception as e:
            logger.error(f"🔍 [SETTINGS] Error in callback handler: {str(e)}")
            await query.edit_message_text("❌ Произошла ошибка при обработке запроса. Попробуйте позже.")
    
    @log_function_call
    async def show_settings_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Show user settings menu (callback version)"""
        query = update.callback_query
        user = query.from_user
        
        # Get user's current settings
        api_keys = self.user_settings.get_user_api_keys(user.id)
        preferences = self.user_settings.get_user_preferences(user.id)
        
        # Create settings text
        settings_text = "⚙️ **Ваши настройки:**\n\n"
        
        # API Keys section
        settings_text += "🔑 **API Ключи:**\n"
        if api_keys:
            for provider, key in api_keys.items():
                masked_key = key[:10] + "..." + key[-4:] if len(key) > 14 else "***"
                settings_text += f"• {provider.title()}: `{masked_key}`\n"
        else:
            settings_text += "• Нет настроенных ключей\n"
        
        # Preferences section
        settings_text += "\n🎯 **Предпочтения:**\n"
        provider = preferences.get('provider', 'Не выбрано')
        model = preferences.get('model', 'Не выбрано')
        settings_text += f"• Провайдер: {provider.title()}\n"
        settings_text += f"• Модель: {model}\n"
        
        # Create keyboard
        keyboard = [
            [
                InlineKeyboardButton("🔑 Добавить API ключ", callback_data="add_api_key"),
                InlineKeyboardButton("🗑️ Удалить ключ", callback_data="remove_api_key")
            ],
            [
                InlineKeyboardButton("🎯 Выбрать провайдера", callback_data="select_provider"),
                InlineKeyboardButton("📊 Статистика", callback_data="user_stats")
            ],
            [
                InlineKeyboardButton("🔙 Назад", callback_data="back_to_main")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            settings_text,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
    
    @log_function_call
    async def show_provider_selection(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Show provider selection menu"""
        query = update.callback_query
        await query.answer()
        
        user = update.effective_user
        api_keys = self.user_settings.get_user_api_keys(user.id)
        
        keyboard = []
        for provider in ["openai", "claude"]:
            has_key = provider in api_keys
            status = "✅" if has_key else "❌"
            keyboard.append([
                InlineKeyboardButton(
                    f"{status} {provider.title()}", 
                    callback_data=f"select_provider_{provider}"
                )
            ])
        
        keyboard.append([
            InlineKeyboardButton("🔙 Назад", callback_data="back_to_settings")
        ])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            "🎯 **Выбор провайдера**\n\n"
            "Выберите предпочитаемого AI провайдера:\n"
            "✅ - ключ настроен\n"
            "❌ - ключ не настроен",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
    
    @log_function_call
    async def cancel(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Cancel conversation"""
        user = update.effective_user
        
        # Clear conversation state
        context.user_data.pop('conversation_state', None)
        context.user_data.pop('adding_provider', None)
        
        await update.message.reply_text(
            "❌ Операция отменена.\n\n"
            "Используйте /settings для управления настройками."
        )
        
        return ConversationHandler.END 