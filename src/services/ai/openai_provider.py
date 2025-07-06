from openai import AsyncOpenAI
from typing import List, Dict, Any
import asyncio

from .base_provider import BaseAIProvider
from ...utils.logger import get_logger

logger = get_logger(__name__)

class OpenAIProvider(BaseAIProvider):
    """OpenAI API provider"""
    
    def __init__(self, api_key: str, model: str = "gpt-3.5-turbo"):
        super().__init__(api_key, model)
        self.client = AsyncOpenAI(api_key=self.api_key)
        self.max_tokens = 1000
        self.temperature = 0.7
    
    def validate_config(self) -> bool:
        """Validate OpenAI configuration"""
        return bool(self.api_key and self.api_key.startswith('sk-'))
    
    def get_available_models(self) -> List[Dict[str, str]]:
        """Get list of available OpenAI models"""
        return [
            {"id": "gpt-4", "name": "GPT-4", "description": "Most capable model"},
            {"id": "gpt-4-turbo", "name": "GPT-4 Turbo", "description": "Latest GPT-4 model"},
            {"id": "gpt-3.5-turbo", "name": "GPT-3.5 Turbo", "description": "Fast and efficient"},
            {"id": "gpt-3.5-turbo-16k", "name": "GPT-3.5 Turbo 16K", "description": "Extended context"},
        ]
    
    async def generate_response(self, messages: List[Dict[str, str]]) -> str:
        """Generate response using OpenAI API"""
        try:
            request_data = {
                "model": self.model,
                "messages": messages,
                "max_tokens": self.max_tokens,
                "temperature": self.temperature,
                "top_p": 1.0,
                "frequency_penalty": 0.0,
                "presence_penalty": 0.0
            }
            
            response = await self.client.chat.completions.create(**request_data)
            
            if response and response.choices:
                return response.choices[0].message.content.strip()
            else:
                logger.error("Empty response from OpenAI API")
                return self.get_fallback_response()
                
        except Exception as e:
            error_msg = str(e)
            logger.error(f"OpenAI API call failed: {error_msg}")
            
            # Handle specific error cases
            if "insufficient_quota" in error_msg.lower() or "quota" in error_msg.lower():
                return "⚠️ Закончилась квота OpenAI. Пополните баланс для продолжения использования."
            elif "invalid_api_key" in error_msg.lower() or "authentication" in error_msg.lower():
                return "❌ Недействительный API ключ OpenAI. Проверьте настройки в /settings."
            elif "rate_limit" in error_msg.lower():
                return "⏳ Превышен лимит запросов OpenAI. Попробуйте через несколько минут."
            elif "context_length" in error_msg.lower():
                return "📝 Слишком длинное сообщение. Попробуйте сократить текст."
            else:
                return self.get_fallback_response()
    
    def set_parameters(self, max_tokens: int = None, temperature: float = None):
        """Set generation parameters"""
        if max_tokens is not None:
            self.max_tokens = max_tokens
        if temperature is not None:
            self.temperature = temperature 