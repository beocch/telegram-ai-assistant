import anthropic
from typing import List, Dict, Any
import asyncio

from .base_provider import BaseAIProvider
from ...utils.logger import get_logger

logger = get_logger(__name__)

class ClaudeProvider(BaseAIProvider):
    """Anthropic Claude API provider"""
    
    def __init__(self, api_key: str, model: str = "claude-3-haiku-20240307"):
        super().__init__(api_key, model)
        self.client = anthropic.AsyncAnthropic(api_key=self.api_key)
        self.max_tokens = 1000
        self.temperature = 0.7
    
    def validate_config(self) -> bool:
        """Validate Claude configuration"""
        # Claude API keys can have different formats
        valid_prefixes = ['sk-ant-', 'sk-ant_api03-', 'sk-ant_api04-']
        return bool(self.api_key and any(self.api_key.startswith(prefix) for prefix in valid_prefixes))
    
    def get_available_models(self) -> List[Dict[str, str]]:
        """Get list of available Claude models"""
        return [
            {"id": "claude-3-5-sonnet-20241022", "name": "Claude 3.5 Sonnet", "description": "Latest and most capable"},
            {"id": "claude-3-sonnet-20240229", "name": "Claude 3 Sonnet", "description": "Balanced performance"},
            {"id": "claude-3-opus-20240229", "name": "Claude 3 Opus", "description": "Most powerful model"},
            {"id": "claude-3-haiku-20240307", "name": "Claude 3 Haiku", "description": "Fast and efficient"},
        ]
    
    async def generate_response(self, messages: List[Dict[str, str]]) -> str:
        """Generate response using Claude API"""
        try:
            # Convert messages format for Claude
            system_message = ""
            user_messages = []
            
            for msg in messages:
                if msg["role"] == "system":
                    system_message = msg["content"]
                else:
                    user_messages.append(msg["content"])
            
            # Combine user messages
            user_content = "\n\n".join(user_messages)
            
            request_data = {
                "model": self.model,
                "max_tokens": self.max_tokens,
                "temperature": self.temperature,
                "messages": [
                    {
                        "role": "user",
                        "content": user_content
                    }
                ]
            }
            
            # Add system message if present
            if system_message:
                request_data["system"] = system_message
            
            response = await self.client.messages.create(**request_data)
            
            if response and response.content:
                return response.content[0].text.strip()
            else:
                logger.error("Empty response from Claude API")
                return self.get_fallback_response()
                
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Claude API call failed: {error_msg}")
            
            # Handle specific error cases
            if "insufficient_quota" in error_msg.lower() or "quota" in error_msg.lower():
                return "⚠️ Закончилась квота Claude. Пополните баланс для продолжения использования."
            elif "invalid_api_key" in error_msg.lower() or "authentication" in error_msg.lower():
                return "❌ Недействительный API ключ Claude. Проверьте настройки в /settings."
            elif "rate_limit" in error_msg.lower():
                return "⏳ Превышен лимит запросов Claude. Попробуйте через несколько минут."
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