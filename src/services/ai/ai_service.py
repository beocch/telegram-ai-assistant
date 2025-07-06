from typing import List, Dict, Any, Optional
from .base_provider import BaseAIProvider
from .openai_provider import OpenAIProvider
from .claude_provider import ClaudeProvider
from ...utils.logger import get_logger, log_function_call, log_execution_time

logger = get_logger(__name__)

class AIService:
    """Universal AI service for multiple providers"""
    
    def __init__(self, user_settings_service=None):
        self.providers = {}
        self.current_provider = None
        self.user_preferences = {}  # Store user preferences
        self.user_settings_service = user_settings_service  # For user API keys
    
    def set_user_settings_service(self, user_settings_service):
        """Set user settings service for API key management"""
        self.user_settings_service = user_settings_service
        logger.info("User settings service connected to AI service")
    
    def add_provider(self, provider_name: str, provider: BaseAIProvider):
        """Add AI provider"""
        self.providers[provider_name] = provider
        logger.info(f"Added AI provider: {provider_name}")
    
    def set_current_provider(self, provider_name: str):
        """Set current AI provider"""
        if provider_name in self.providers:
            self.current_provider = self.providers[provider_name]
            logger.info(f"Current AI provider set to: {provider_name}")
        else:
            logger.error(f"Provider {provider_name} not found")
    
    def get_current_provider(self) -> Optional[BaseAIProvider]:
        """Get current AI provider"""
        return self.current_provider
    
    def get_available_providers(self) -> List[str]:
        """Get list of available providers"""
        return list(self.providers.keys())
    
    def get_provider_models(self, provider_name: str) -> List[Dict[str, str]]:
        """Get available models for specific provider"""
        if provider_name in self.providers:
            return self.providers[provider_name].get_available_models()
        return []
    
    def set_user_preference(self, user_id: int, provider: str, model: str = None):
        """Set user preference for AI provider and model"""
        self.user_preferences[user_id] = {
            "provider": provider,
            "model": model
        }
        logger.info(f"Set preference for user {user_id}: {provider}, {model}")
    
    def get_user_preference(self, user_id: int) -> Dict[str, str]:
        """Get user preference"""
        return self.user_preferences.get(user_id, {})
    
    def _get_user_provider(self, user_id: int, provider_name: str) -> Optional[BaseAIProvider]:
        """Get provider instance with user's API key"""
        if not self.user_settings_service:
            return self.providers.get(provider_name)
        
        # Get user's API key
        user_api_keys = self.user_settings_service.get_user_api_keys(user_id)
        user_api_key = user_api_keys.get(provider_name)
        
        if not user_api_key:
            logger.info(f"No API key found for user {user_id}, provider {provider_name}")
            return self.providers.get(provider_name)
        
        # Create provider instance with user's API key
        try:
            if provider_name == "openai":
                provider = OpenAIProvider(api_key=user_api_key)
                provider.set_parameters(
                    max_tokens=1000,
                    temperature=0.7
                )
                return provider
            elif provider_name == "claude":
                provider = ClaudeProvider(api_key=user_api_key)
                provider.set_parameters(
                    max_tokens=1000,
                    temperature=0.7
                )
                return provider
            else:
                logger.warning(f"Unknown provider: {provider_name}")
                return self.providers.get(provider_name)
                
        except Exception as e:
            logger.error(f"Error creating user provider for {provider_name}: {str(e)}")
            return self.providers.get(provider_name)
    
    @log_function_call
    @log_execution_time
    async def generate_response(self, messages: List[Dict[str, str]], user_id: int = None) -> str:
        """Generate AI response using user's preferred provider"""
        try:
            # Get user preference
            if user_id:
                # Check user settings first
                if self.user_settings_service:
                    user_provider = self.user_settings_service.get_user_provider(user_id)
                    if user_provider:
                        logger.info(f"Using user's preferred provider: {user_provider}")
                        provider_instance = self._get_user_provider(user_id, user_provider)
                        if provider_instance:
                            return await provider_instance.generate_response(messages)
                
                # Fallback to in-memory preferences
                if user_id in self.user_preferences:
                    preference = self.user_preferences[user_id]
                    provider_name = preference.get("provider")
                    model = preference.get("model")
                    
                    if provider_name:
                        logger.info(f"Using in-memory preference: {provider_name}")
                        provider_instance = self._get_user_provider(user_id, provider_name)
                        if provider_instance:
                            if model:
                                provider_instance.model = model
                            return await provider_instance.generate_response(messages)
            
            # Fallback to current provider
            if self.current_provider:
                logger.info("Using current provider as fallback")
                return await self.current_provider.generate_response(messages)
            
            # Fallback response if no providers available
            logger.error("No AI providers available")
            return "Извините, AI сервис временно недоступен."
            
        except Exception as e:
            logger.error(f"Error generating AI response: {str(e)}")
            return "Произошла ошибка при обработке запроса. Попробуйте позже."
    
    async def test_provider(self, provider_name: str, user_id: int = None) -> bool:
        """Test if provider is working"""
        try:
            # Test with user's API key if available
            if user_id and self.user_settings_service:
                provider_instance = self._get_user_provider(user_id, provider_name)
                if provider_instance:
                    test_messages = [{"role": "user", "content": "Hello"}]
                    response = await provider_instance.generate_response(test_messages)
                    return response and response != provider_instance.get_fallback_response()
            
            # Fallback to global provider
            if provider_name not in self.providers:
                return False
            
            provider = self.providers[provider_name]
            test_messages = [
                {"role": "user", "content": "Hello"}
            ]
            
            response = await provider.generate_response(test_messages)
            return response and response != provider.get_fallback_response()
            
        except Exception as e:
            logger.error(f"Provider test failed for {provider_name}: {str(e)}")
            return False
    
    def get_provider_status(self) -> Dict[str, bool]:
        """Get status of all providers"""
        status = {}
        for name, provider in self.providers.items():
            status[name] = provider.validate_config()
        return status 