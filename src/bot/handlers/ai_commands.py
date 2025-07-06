from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from typing import List, Dict, Any

from ...utils.logger import get_logger, log_function_call
from ...services.ai.ai_service import AIService

logger = get_logger(__name__)

class AICommandsHandler:
    """Handler for AI provider management commands"""
    
    def __init__(self, ai_service: AIService):
        self.ai_service = ai_service
    
    @log_function_call
    async def show_providers(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Show available AI providers"""
        user = update.effective_user
        
        providers = self.ai_service.get_available_providers()
        if not providers:
            await update.message.reply_text(
                "❌ Нет доступных AI провайдеров.\n"
                "Пожалуйста, настройте API ключи в конфигурации."
            )
            return
        
        # Get provider status
        status = self.ai_service.get_provider_status()
        
        # Create provider list
        provider_text = "🤖 **Доступные AI провайдеры:**\n\n"
        for provider in providers:
            status_icon = "✅" if status.get(provider, False) else "❌"
            provider_text += f"{status_icon} **{provider.title()}**\n"
        
        # Add current provider info
        current = self.ai_service.get_current_provider()
        if current:
            provider_text += f"\n🎯 **Текущий провайдер:** {current.provider_name}"
        
        # Create keyboard for provider selection
        keyboard = []
        for provider in providers:
            keyboard.append([
                InlineKeyboardButton(
                    f"🔧 {provider.title()}", 
                    callback_data=f"provider_{provider}"
                )
            ])
        
        keyboard.append([
            InlineKeyboardButton("📊 Статус", callback_data="provider_status"),
            InlineKeyboardButton("⚙️ Настройки", callback_data="provider_settings")
        ])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            provider_text,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
    
    @log_function_call
    async def show_models(self, update: Update, context: ContextTypes.DEFAULT_TYPE, provider_name: str) -> None:
        """Show available models for specific provider"""
        models = self.ai_service.get_provider_models(provider_name)
        
        if not models:
            await update.message.reply_text(f"❌ Нет доступных моделей для {provider_name}")
            return
        
        # Create model list
        model_text = f"🤖 **Модели {provider_name.title()}:**\n\n"
        for model in models:
            model_text += f"• **{model['name']}** (`{model['id']}`)\n"
            model_text += f"  _{model['description']}_\n\n"
        
        # Create keyboard for model selection
        keyboard = []
        for model in models:
            keyboard.append([
                InlineKeyboardButton(
                    f"🎯 {model['name']}", 
                    callback_data=f"model_{provider_name}_{model['id']}"
                )
            ])
        
        keyboard.append([
            InlineKeyboardButton("🔙 Назад к провайдерам", callback_data="providers_back")
        ])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            model_text,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
    
    @log_function_call
    async def set_user_provider(self, update: Update, context: ContextTypes.DEFAULT_TYPE, provider: str, model: str = None) -> None:
        """Set user's preferred AI provider and model"""
        user = update.effective_user
        
        # Test provider first
        is_working = await self.ai_service.test_provider(provider)
        if not is_working:
            await update.message.reply_text(
                f"❌ Провайдер {provider.title()} недоступен.\n"
                "Проверьте API ключ и попробуйте снова."
            )
            return
        
        # Set user preference
        self.ai_service.set_user_preference(user.id, provider, model)
        
        # Set as current provider if it's the first one
        if not self.ai_service.get_current_provider():
            self.ai_service.set_current_provider(provider)
        
        # Create response message
        response = f"✅ **Провайдер изменен!**\n\n"
        response += f"🤖 **Провайдер:** {provider.title()}\n"
        if model:
            response += f"🎯 **Модель:** {model}\n"
        
        await update.message.reply_text(response, parse_mode='Markdown')
    
    @log_function_call
    async def show_provider_status(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Show detailed provider status"""
        status = self.ai_service.get_provider_status()
        current = self.ai_service.get_current_provider()
        
        status_text = "📊 **Статус AI провайдеров:**\n\n"
        
        for provider, is_valid in status.items():
            status_icon = "✅" if is_valid else "❌"
            current_icon = "🎯" if current and current.provider_name == provider else ""
            status_text += f"{status_icon} **{provider.title()}** {current_icon}\n"
        
        if not any(status.values()):
            status_text += "\n⚠️ **Внимание:** Ни один провайдер не настроен корректно!"
        
        await update.message.reply_text(status_text, parse_mode='Markdown')
    
    @log_function_call
    async def handle_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle callback queries for AI provider management"""
        query = update.callback_query
        
        # Debug logging
        logger.info(f"🔍 [AI_COMMANDS] Received callback: {query.data} from user {query.from_user.id}")
        
        await query.answer()
        
        data = query.data
        logger.info(f"🔍 [AI_COMMANDS] Processing callback: {data}")
        
        try:
            if data.startswith("provider_"):
                provider = data.replace("provider_", "")
                logger.info(f"🔍 [AI_COMMANDS] Handling provider callback: {provider}")
                
                if provider == "status":
                    logger.info("🔍 [AI_COMMANDS] Showing provider status")
                    await self.show_provider_status_callback(update, context)
                elif provider == "settings":
                    logger.info("🔍 [AI_COMMANDS] Showing provider settings")
                    await self.show_provider_settings_callback(update, context)
                elif provider == "back":
                    logger.info("🔍 [AI_COMMANDS] Going back to providers")
                    await self.show_providers_callback(update, context)
                else:
                    logger.info(f"🔍 [AI_COMMANDS] Showing models for provider: {provider}")
                    await self.show_models_callback(update, context, provider)
            
            elif data.startswith("model_"):
                parts = data.split("_")
                if len(parts) >= 3:
                    provider = parts[1]
                    model = "_".join(parts[2:])  # Handle model names with underscores
                    logger.info(f"🔍 [AI_COMMANDS] Setting user provider: {provider}, model: {model}")
                    await self.set_user_provider_callback(update, context, provider, model)
            
            elif data == "providers_back":
                logger.info("🔍 [AI_COMMANDS] Going back to providers")
                await self.show_providers_callback(update, context)
            else:
                logger.warning(f"🔍 [AI_COMMANDS] Unknown callback data: {data}")
                
        except Exception as e:
            logger.error(f"🔍 [AI_COMMANDS] Error in callback handler: {str(e)}")
            await query.edit_message_text("❌ Произошла ошибка при обработке запроса. Попробуйте позже.")
    
    @log_function_call
    async def show_providers_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Show available AI providers (callback version)"""
        query = update.callback_query
        
        providers = self.ai_service.get_available_providers()
        if not providers:
            await query.edit_message_text(
                "❌ Нет доступных AI провайдеров.\n"
                "Пожалуйста, настройте API ключи в конфигурации."
            )
            return
        
        # Get provider status
        status = self.ai_service.get_provider_status()
        
        # Create provider list
        provider_text = "🤖 **Доступные AI провайдеры:**\n\n"
        for provider in providers:
            status_icon = "✅" if status.get(provider, False) else "❌"
            provider_text += f"{status_icon} **{provider.title()}**\n"
        
        # Add current provider info
        current = self.ai_service.get_current_provider()
        if current:
            provider_text += f"\n🎯 **Текущий провайдер:** {current.provider_name}"
        
        # Create keyboard for provider selection
        keyboard = []
        for provider in providers:
            keyboard.append([
                InlineKeyboardButton(
                    f"🔧 {provider.title()}", 
                    callback_data=f"provider_{provider}"
                )
            ])
        
        keyboard.append([
            InlineKeyboardButton("📊 Статус", callback_data="provider_status"),
            InlineKeyboardButton("⚙️ Настройки", callback_data="provider_settings")
        ])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            provider_text,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
    
    @log_function_call
    async def show_models_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE, provider_name: str) -> None:
        """Show available models for specific provider (callback version)"""
        query = update.callback_query
        
        models = self.ai_service.get_provider_models(provider_name)
        
        if not models:
            await query.edit_message_text(f"❌ Нет доступных моделей для {provider_name}")
            return
        
        # Create model list
        model_text = f"🤖 **Модели {provider_name.title()}:**\n\n"
        for model in models:
            model_text += f"• **{model['name']}** (`{model['id']}`)\n"
            model_text += f"  _{model['description']}_\n\n"
        
        # Create keyboard for model selection
        keyboard = []
        for model in models:
            keyboard.append([
                InlineKeyboardButton(
                    f"🎯 {model['name']}", 
                    callback_data=f"model_{provider_name}_{model['id']}"
                )
            ])
        
        keyboard.append([
            InlineKeyboardButton("🔙 Назад к провайдерам", callback_data="providers_back")
        ])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            model_text,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
    
    @log_function_call
    async def set_user_provider_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE, provider: str, model: str = None) -> None:
        """Set user's preferred AI provider and model (callback version)"""
        query = update.callback_query
        user = query.from_user
        
        try:
            # Test provider first
            is_working = await self.ai_service.test_provider(provider)
            if not is_working:
                await query.edit_message_text(
                    f"❌ Провайдер {provider.title()} недоступен.\n"
                    "Проверьте API ключ и попробуйте снова."
                )
                return
            
            # Set user preference
            self.ai_service.set_user_preference(user.id, provider, model)
            
            # Set as current provider if it's the first one
            if not self.ai_service.get_current_provider():
                self.ai_service.set_current_provider(provider)
            
            # Create response message
            response = f"✅ **Провайдер изменен!**\n\n"
            response += f"🤖 **Провайдер:** {provider.title()}\n"
            if model:
                response += f"🎯 **Модель:** {model}\n"
            
            await query.edit_message_text(response, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Error setting user provider: {str(e)}")
            await query.edit_message_text(
                f"❌ Ошибка при настройке провайдера: {str(e)}"
            )
    
    @log_function_call
    async def show_provider_status_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Show detailed provider status (callback version)"""
        query = update.callback_query
        
        status = self.ai_service.get_provider_status()
        current = self.ai_service.get_current_provider()
        
        status_text = "📊 **Статус AI провайдеров:**\n\n"
        
        for provider, is_valid in status.items():
            status_icon = "✅" if is_valid else "❌"
            current_icon = "🎯" if current and current.provider_name == provider else ""
            status_text += f"{status_icon} **{provider.title()}** {current_icon}\n"
        
        if not any(status.values()):
            status_text += "\n⚠️ **Внимание:** Ни один провайдер не настроен корректно!"
        
        keyboard = [[
            InlineKeyboardButton("🔙 Назад", callback_data="providers_back")
        ]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            status_text, 
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
    
    @log_function_call
    async def show_provider_settings_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Show provider settings (callback version)"""
        query = update.callback_query
        
        settings_text = "⚙️ **Настройки AI провайдеров:**\n\n"
        settings_text += "🔧 **Доступные команды:**\n"
        settings_text += "• `/providers` - Показать провайдеры\n"
        settings_text += "• `/status` - Статус провайдеров\n"
        settings_text += "• `/test` - Тест провайдеров\n\n"
        settings_text += "💡 **Советы:**\n"
        settings_text += "• Убедитесь, что API ключи настроены\n"
        settings_text += "• Проверьте баланс на счете провайдера\n"
        settings_text += "• Используйте `/test` для проверки подключения"
        
        keyboard = [[
            InlineKeyboardButton("🔙 Назад", callback_data="providers_back")
        ]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            settings_text, 
            reply_markup=reply_markup, 
            parse_mode='Markdown'
        ) 