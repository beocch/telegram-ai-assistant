from openai import AsyncOpenAI
import asyncio
from typing import List, Dict, Any, Optional
import json

from ...utils.config import Config
from ...utils.logger import get_logger, log_function_call, log_execution_time

logger = get_logger(__name__)

class OpenAIService:
    """Service for interacting with OpenAI API"""
    
    def __init__(self):
        self.api_key = Config.OPENAI_API_KEY
        self.model = Config.OPENAI_MODEL
        self.max_tokens = Config.OPENAI_MAX_TOKENS
        self.temperature = Config.OPENAI_TEMPERATURE
        
        # Configure OpenAI client for new API
        self.client = AsyncOpenAI(api_key=self.api_key)
        
        # Validate configuration
        if not self.api_key:
            raise ValueError("OpenAI API key is not configured")
    
    @log_function_call
    @log_execution_time
    async def generate_response(self, messages: List[Dict[str, str]]) -> str:
        """
        Generate AI response using OpenAI API
        
        Args:
            messages: List of message dictionaries with 'role' and 'content'
        
        Returns:
            Generated response text
        """
        try:
            # Prepare the request
            request_data = {
                "model": self.model,
                "messages": messages,
                "max_tokens": self.max_tokens,
                "temperature": self.temperature,
                "top_p": 1.0,
                "frequency_penalty": 0.0,
                "presence_penalty": 0.0
            }
            
            # Make API call
            response = await self._make_api_call(request_data)
            
            # Extract and return the response
            if response and response.choices:
                return response.choices[0].message.content.strip()
            else:
                logger.error("Empty response from OpenAI API")
                return "Извините, произошла ошибка при генерации ответа. Попробуйте еще раз."
                
        except Exception as e:
            logger.error(f"Error generating OpenAI response: {str(e)}")
            return self._get_fallback_response()
    
    async def _make_api_call(self, request_data: Dict[str, Any]) -> Any:
        """Make async API call to OpenAI"""
        try:
            # Use new OpenAI API
            response = await self.client.chat.completions.create(**request_data)
            return response
        except Exception as e:
            logger.error(f"OpenAI API call failed: {str(e)}")
            raise
    
    def _get_fallback_response(self) -> str:
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
    
    @log_function_call
    async def analyze_sentiment(self, text: str) -> Dict[str, Any]:
        """
        Analyze sentiment of the given text
        
        Args:
            text: Text to analyze
        
        Returns:
            Dictionary with sentiment analysis results
        """
        try:
            messages = [
                {
                    "role": "system",
                    "content": (
                        "Analyze the sentiment of the following text. "
                        "Return a JSON object with 'sentiment' (positive/negative/neutral), "
                        "'confidence' (0-1), and 'emotions' (list of detected emotions)."
                    )
                },
                {
                    "role": "user",
                    "content": text
                }
            ]
            
            response = await self.generate_response(messages)
            
            # Try to parse JSON response
            try:
                return json.loads(response)
            except json.JSONDecodeError:
                # Fallback to simple analysis
                return {
                    "sentiment": "neutral",
                    "confidence": 0.5,
                    "emotions": [],
                    "raw_response": response
                }
                
        except Exception as e:
            logger.error(f"Error analyzing sentiment: {str(e)}")
            return {
                "sentiment": "neutral",
                "confidence": 0.0,
                "emotions": [],
                "error": str(e)
            }
    
    @log_function_call
    async def summarize_text(self, text: str, max_length: int = 200) -> str:
        """
        Summarize the given text
        
        Args:
            text: Text to summarize
            max_length: Maximum length of summary
        
        Returns:
            Summarized text
        """
        try:
            messages = [
                {
                    "role": "system",
                    "content": f"Summarize the following text in no more than {max_length} characters. Keep it concise and informative."
                },
                {
                    "role": "user",
                    "content": text
                }
            ]
            
            return await self.generate_response(messages)
            
        except Exception as e:
            logger.error(f"Error summarizing text: {str(e)}")
            return "Не удалось создать краткое содержание текста."
    
    @log_function_call
    async def translate_text(self, text: str, target_language: str = "English") -> str:
        """
        Translate text to target language
        
        Args:
            text: Text to translate
            target_language: Target language for translation
        
        Returns:
            Translated text
        """
        try:
            messages = [
                {
                    "role": "system",
                    "content": f"Translate the following text to {target_language}. Provide only the translation without additional explanations."
                },
                {
                    "role": "user",
                    "content": text
                }
            ]
            
            return await self.generate_response(messages)
            
        except Exception as e:
            logger.error(f"Error translating text: {str(e)}")
            return "Не удалось перевести текст."
    
    @log_function_call
    async def extract_keywords(self, text: str, max_keywords: int = 10) -> List[str]:
        """
        Extract keywords from text
        
        Args:
            text: Text to analyze
            max_keywords: Maximum number of keywords to extract
        
        Returns:
            List of extracted keywords
        """
        try:
            messages = [
                {
                    "role": "system",
                    "content": f"Extract up to {max_keywords} most important keywords from the following text. Return them as a JSON array of strings."
                },
                {
                    "role": "user",
                    "content": text
                }
            ]
            
            response = await self.generate_response(messages)
            
            # Try to parse JSON response
            try:
                keywords = json.loads(response)
                if isinstance(keywords, list):
                    return keywords[:max_keywords]
                else:
                    return []
            except json.JSONDecodeError:
                # Fallback: split response by common delimiters
                keywords = response.replace('[', '').replace(']', '').replace('"', '').split(',')
                return [kw.strip() for kw in keywords if kw.strip()][:max_keywords]
                
        except Exception as e:
            logger.error(f"Error extracting keywords: {str(e)}")
            return []
    
    def get_usage_stats(self) -> Dict[str, Any]:
        """Get usage statistics for the OpenAI service"""
        return {
            "model": self.model,
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
            "api_key_configured": bool(self.api_key)
        } 