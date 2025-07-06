import json
import asyncio
from typing import List, Dict, Any, Optional
import redis.asyncio as redis
from datetime import datetime, timedelta

from ...utils.config import Config
from ...utils.logger import get_logger, log_function_call

logger = get_logger(__name__)

class RedisClient:
    """Redis client for caching and conversation history"""
    
    def __init__(self):
        self.redis_client = None
        self._initialized = False
    
    async def initialize(self):
        """Initialize Redis connection"""
        if self._initialized:
            return
        
        try:
            redis_config = Config.get_redis_config()
            self.redis_client = redis.Redis.from_url(
                redis_config["url"],
                db=redis_config["db"],
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5,
                retry_on_timeout=True
            )
            
            # Test connection
            await self.redis_client.ping()
            
            self._initialized = True
            logger.info("Redis client initialized successfully")
            
        except Exception as e:
            logger.warning(f"Failed to initialize Redis client: {str(e)}")
            logger.info("Continuing without Redis - some features will be limited")
            # Don't raise error - Redis is optional for caching
            self._initialized = False
    
    def _get_key(self, key_type: str, user_id: int, *args) -> str:
        """Generate Redis key"""
        parts = [key_type, str(user_id)] + [str(arg) for arg in args]
        return ":".join(parts)
    
    @log_function_call
    async def add_to_conversation_history(
        self,
        user_id: int,
        user_message: str,
        ai_response: str
    ) -> None:
        """Add message and response to conversation history"""
        if not self._initialized:
            logger.debug("Redis not available - skipping conversation history")
            return
        
        try:
            history_key = self._get_key("conversation", user_id)
            
            # Create conversation entry
            entry = {
                "timestamp": datetime.utcnow().isoformat(),
                "user_message": user_message,
                "ai_response": ai_response
            }
            
            # Add to Redis list (left push to keep recent messages first)
            await self.redis_client.lpush(history_key, json.dumps(entry))
            
            # Trim to keep only last N messages
            max_history = Config.MAX_CONVERSATION_HISTORY * 2  # *2 because each entry has user + AI message
            await self.redis_client.ltrim(history_key, 0, max_history - 1)
            
            # Set expiration (24 hours)
            await self.redis_client.expire(history_key, 86400)
            
        except Exception as e:
            logger.error(f"Error adding to conversation history: {str(e)}")
    
    @log_function_call
    async def get_conversation_history(self, user_id: int) -> List[Dict[str, str]]:
        """Get conversation history for user"""
        if not self._initialized:
            logger.debug("Redis not available - returning empty conversation history")
            return []
        
        try:
            history_key = self._get_key("conversation", user_id)
            
            # Get conversation history from Redis
            history_data = await self.redis_client.lrange(history_key, 0, -1)
            
            # Parse and format history
            history = []
            for entry_json in history_data:
                try:
                    entry = json.loads(entry_json)
                    # Add user message
                    history.append({
                        "role": "user",
                        "content": entry.get("user_message", "")
                    })
                    # Add AI response
                    history.append({
                        "role": "assistant",
                        "content": entry.get("ai_response", "")
                    })
                except json.JSONDecodeError:
                    logger.warning(f"Failed to parse conversation entry: {entry_json}")
                    continue
            
            return history
            
        except Exception as e:
            logger.error(f"Error getting conversation history: {str(e)}")
            return []
    
    @log_function_call
    async def clear_conversation_history(self, user_id: int) -> None:
        """Clear conversation history for user"""
        if not self._initialized:
            logger.debug("Redis not available - skipping clear operation")
            return
        
        try:
            history_key = self._get_key("conversation", user_id)
            await self.redis_client.delete(history_key)
            logger.info(f"Cleared conversation history for user {user_id}")
            
        except Exception as e:
            logger.error(f"Error clearing conversation history: {str(e)}")
    
    @log_function_call
    async def set_cache(self, key: str, value: Any, expire_seconds: int = 3600) -> None:
        """Set cache value"""
        if not self._initialized:
            return
        
        try:
            if isinstance(value, (dict, list)):
                value = json.dumps(value)
            await self.redis_client.setex(key, expire_seconds, str(value))
            
        except Exception as e:
            logger.error(f"Error setting cache: {str(e)}")
    
    @log_function_call
    async def get_cache(self, key: str) -> Optional[Any]:
        """Get cache value"""
        if not self._initialized:
            return None
        
        try:
            value = await self.redis_client.get(key)
            if value is None:
                return None
            
            # Try to parse as JSON
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                return value
            
        except Exception as e:
            logger.error(f"Error getting cache: {str(e)}")
            return None
    
    @log_function_call
    async def delete_cache(self, key: str) -> None:
        """Delete cache value"""
        if not self._initialized:
            return
        
        try:
            await self.redis_client.delete(key)
            
        except Exception as e:
            logger.error(f"Error deleting cache: {str(e)}")
    
    @log_function_call
    async def increment_counter(self, key: str, expire_seconds: int = 3600) -> int:
        """Increment counter and return new value"""
        if not self._initialized:
            return 0
        
        try:
            # Use Redis pipeline for atomic operation
            async with self.redis_client.pipeline() as pipe:
                await pipe.incr(key)
                await pipe.expire(key, expire_seconds)
                result = await pipe.execute()
                return result[0]
            
        except Exception as e:
            logger.error(f"Error incrementing counter: {str(e)}")
            return 0
    
    @log_function_call
    async def get_rate_limit_count(self, user_id: int, window_seconds: int = 60) -> int:
        """Get current rate limit count for user"""
        if not self._initialized:
            return 0
        
        try:
            rate_limit_key = self._get_key("rate_limit", user_id, window_seconds)
            count = await self.redis_client.get(rate_limit_key)
            return int(count) if count else 0
            
        except Exception as e:
            logger.error(f"Error getting rate limit count: {str(e)}")
            return 0
    
    @log_function_call
    async def increment_rate_limit(self, user_id: int, window_seconds: int = 60) -> int:
        """Increment rate limit counter for user"""
        if not self._initialized:
            return 0
        
        try:
            rate_limit_key = self._get_key("rate_limit", user_id, window_seconds)
            return await self.increment_counter(rate_limit_key, window_seconds)
            
        except Exception as e:
            logger.error(f"Error incrementing rate limit: {str(e)}")
            return 0
    
    @log_function_call
    async def set_user_preference(self, user_id: int, preference: str, value: Any) -> None:
        """Set user preference"""
        if not self._initialized:
            return
        
        try:
            pref_key = self._get_key("preferences", user_id, preference)
            await self.set_cache(pref_key, value, expire_seconds=86400 * 30)  # 30 days
            
        except Exception as e:
            logger.error(f"Error setting user preference: {str(e)}")
    
    @log_function_call
    async def get_user_preference(self, user_id: int, preference: str) -> Optional[Any]:
        """Get user preference"""
        if not self._initialized:
            return None
        
        try:
            pref_key = self._get_key("preferences", user_id, preference)
            return await self.get_cache(pref_key)
            
        except Exception as e:
            logger.error(f"Error getting user preference: {str(e)}")
            return None
    
    @log_function_call
    async def get_redis_info(self) -> Dict[str, Any]:
        """Get Redis server information"""
        if not self._initialized:
            return {"status": "not_initialized"}
        
        try:
            info = await self.redis_client.info()
            return {
                "status": "connected",
                "version": info.get("redis_version", "unknown"),
                "used_memory": info.get("used_memory_human", "unknown"),
                "connected_clients": info.get("connected_clients", 0),
                "total_commands_processed": info.get("total_commands_processed", 0)
            }
            
        except Exception as e:
            logger.error(f"Error getting Redis info: {str(e)}")
            return {"status": "error", "error": str(e)}
    
    async def close(self):
        """Close Redis connection"""
        if self.redis_client:
            await self.redis_client.close()
            logger.info("Redis connection closed") 