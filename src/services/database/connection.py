import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from pathlib import Path
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Text, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.sql import text

from ...utils.config import Config
from ...utils.logger import get_logger, log_function_call

logger = get_logger(__name__)

Base = declarative_base()

class UserInteraction(Base):
    """Database model for user interactions"""
    __tablename__ = 'user_interactions'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, nullable=False, index=True)
    chat_id = Column(Integer, nullable=False)
    action = Column(String(100), nullable=False)
    message_type = Column(String(50), nullable=True)
    message_length = Column(Integer, default=0)
    response_length = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f"<UserInteraction(user_id={self.user_id}, action='{self.action}', created_at='{self.created_at}')>"

class UserStats(Base):
    """Database model for user statistics"""
    __tablename__ = 'user_stats'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, nullable=False, unique=True, index=True)
    total_messages = Column(Integer, default=0)
    messages_today = Column(Integer, default=0)
    messages_this_week = Column(Integer, default=0)
    tokens_used = Column(Integer, default=0)
    avg_response_length = Column(Integer, default=0)
    first_used = Column(DateTime, default=datetime.utcnow)
    last_used = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f"<UserStats(user_id={self.user_id}, total_messages={self.total_messages})>"

class DatabaseService:
    """Service for database operations"""
    
    def __init__(self):
        self.engine = None
        self.SessionLocal = None
        self._initialized = False
    
    async def initialize(self):
        """Initialize database connection and create tables"""
        if self._initialized:
            return
        
        try:
            # Create data directory if it doesn't exist
            data_dir = Path("data")
            data_dir.mkdir(exist_ok=True)
            
            # Create engine
            db_config = Config.get_database_config()
            self.engine = create_engine(
                db_config["url"],
                echo=db_config["echo"],
                pool_pre_ping=True
            )
            
            # Create session factory
            self.SessionLocal = sessionmaker(
                autocommit=False,
                autoflush=False,
                bind=self.engine
            )
            
            # Create tables
            Base.metadata.create_all(bind=self.engine)
            
            self._initialized = True
            logger.info("Database initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize database: {str(e)}")
            raise
    
    def get_session(self) -> Session:
        """Get database session"""
        if not self._initialized:
            raise RuntimeError("Database not initialized. Call initialize() first.")
        
        return self.SessionLocal()
    
    @log_function_call
    async def log_user_interaction(
        self,
        user_id: int,
        chat_id: int,
        action: str,
        message_type: str = None,
        message_length: int = 0,
        response_length: int = 0
    ) -> None:
        """Log user interaction to database"""
        if not self._initialized:
            logger.warning("Database not initialized, skipping log")
            return
            
        session = None
        try:
            session = self.get_session()
            
            # Create interaction record
            interaction = UserInteraction(
                user_id=user_id,
                chat_id=chat_id,
                action=action,
                message_type=message_type,
                message_length=message_length,
                response_length=response_length
            )
            
            session.add(interaction)
            session.commit()
            
            # Update user statistics
            await self._update_user_stats(session, user_id, message_length, response_length)
            
        except Exception as e:
            logger.error(f"Error logging user interaction: {str(e)}")
            if session:
                session.rollback()
        finally:
            if session:
                session.close()
    
    async def _update_user_stats(
        self,
        session: Session,
        user_id: int,
        message_length: int = 0,
        response_length: int = 0
    ) -> None:
        """Update user statistics"""
        try:
            # Get or create user stats
            user_stats = session.query(UserStats).filter(UserStats.user_id == user_id).first()
            
            if not user_stats:
                user_stats = UserStats(user_id=user_id)
                session.add(user_stats)
            
            # Update statistics with safe defaults
            current_total = user_stats.total_messages or 0
            current_tokens = user_stats.tokens_used or 0
            
            user_stats.total_messages = current_total + 1
            user_stats.tokens_used = current_tokens + message_length + response_length
            
            # Calculate average response length
            if user_stats.total_messages > 0:
                user_stats.avg_response_length = user_stats.tokens_used // user_stats.total_messages
            
            user_stats.last_used = datetime.utcnow()
            
            # Update daily and weekly counts
            await self._update_periodic_stats(session, user_stats)
            
            session.commit()
            
        except Exception as e:
            logger.error(f"Error updating user stats: {str(e)}")
            if session:
                session.rollback()
    
    async def _update_periodic_stats(self, session: Session, user_stats: UserStats) -> None:
        """Update daily and weekly message counts"""
        try:
            now = datetime.utcnow()
            today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
            week_start = today_start - timedelta(days=today_start.weekday())
            
            # Count messages today
            today_count = session.query(UserInteraction).filter(
                UserInteraction.user_id == user_stats.user_id,
                UserInteraction.created_at >= today_start
            ).count()
            
            # Count messages this week
            week_count = session.query(UserInteraction).filter(
                UserInteraction.user_id == user_stats.user_id,
                UserInteraction.created_at >= week_start
            ).count()
            
            user_stats.messages_today = today_count
            user_stats.messages_this_week = week_count
            
        except Exception as e:
            logger.error(f"Error updating periodic stats: {str(e)}")
    
    @log_function_call
    async def get_user_stats(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Get user statistics"""
        try:
            session = self.get_session()
            
            user_stats = session.query(UserStats).filter(UserStats.user_id == user_id).first()
            
            if user_stats:
                return {
                    'total_messages': user_stats.total_messages,
                    'messages_today': user_stats.messages_today,
                    'messages_this_week': user_stats.messages_this_week,
                    'tokens_used': user_stats.tokens_used,
                    'avg_response_length': user_stats.avg_response_length,
                    'first_used': user_stats.first_used.strftime('%Y-%m-%d %H:%M:%S'),
                    'last_used': user_stats.last_used.strftime('%Y-%m-%d %H:%M:%S')
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting user stats: {str(e)}")
            return None
        finally:
            if session:
                session.close()
    
    @log_function_call
    async def clear_user_conversation(self, user_id: int) -> None:
        """Clear user conversation history from database"""
        try:
            session = self.get_session()
            
            # Delete user interactions (keep stats)
            session.query(UserInteraction).filter(
                UserInteraction.user_id == user_id
            ).delete()
            
            session.commit()
            logger.info(f"Cleared conversation history for user {user_id}")
            
        except Exception as e:
            logger.error(f"Error clearing user conversation: {str(e)}")
            if session:
                session.rollback()
        finally:
            if session:
                session.close()
    
    @log_function_call
    async def get_system_stats(self) -> Dict[str, Any]:
        """Get system-wide statistics"""
        try:
            session = self.get_session()
            
            # Total users
            total_users = session.query(UserStats).count()
            
            # Total interactions
            total_interactions = session.query(UserInteraction).count()
            
            # Today's interactions
            today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
            today_interactions = session.query(UserInteraction).filter(
                UserInteraction.created_at >= today_start
            ).count()
            
            # Most active users
            active_users = session.query(
                UserInteraction.user_id,
                text('COUNT(*) as interaction_count')
            ).group_by(UserInteraction.user_id).order_by(
                text('interaction_count DESC')
            ).limit(10).all()
            
            return {
                'total_users': total_users,
                'total_interactions': total_interactions,
                'today_interactions': today_interactions,
                'active_users': [{'user_id': user_id, 'count': count} for user_id, count in active_users]
            }
            
        except Exception as e:
            logger.error(f"Error getting system stats: {str(e)}")
            return {}
        finally:
            if session:
                session.close()
    
    async def close(self):
        """Close database connections"""
        if self.engine:
            self.engine.dispose()
            logger.info("Database connections closed") 