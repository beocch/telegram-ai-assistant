from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional

class BaseAIProvider(ABC):
    """Base class for AI providers"""
    
    def __init__(self, api_key: str, model: str = None):
        self.api_key = api_key
        self.model = model
        self.provider_name = self.__class__.__name__
    
    @abstractmethod
    async def generate_response(self, messages: List[Dict[str, str]]) -> str:
        """Generate AI response"""
        pass
    
    @abstractmethod
    def get_available_models(self) -> List[Dict[str, str]]:
        """Get list of available models"""
        pass
    
    @abstractmethod
    def validate_config(self) -> bool:
        """Validate provider configuration"""
        pass
    
    def get_fallback_response(self) -> str:
        """Get fallback response when AI service is unavailable"""
        fallback_responses = [
            "Извините, у меня временные технические проблемы. Попробуйте через несколько минут.",
            "К сожалению, я сейчас не могу обработать ваш запрос. Попробуйте позже.",
            "Произошла ошибка при обработке вашего сообщения. Попробуйте еще раз.",
            "Сервис временно недоступен. Пожалуйста, попробуйте через некоторое время.",
            "🤖 Привет! Я AI-ассистент. К сожалению, сейчас у меня проблемы с подключением к сервису. Попробуйте позже!",
            "💬 Здравствуйте! Сейчас я не могу обработать ваш запрос из-за технических проблем. Попробуйте через несколько минут."
        ]
        
        import random
        return random.choice(fallback_responses) 