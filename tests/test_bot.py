#!/usr/bin/env python3
"""
Simple test script for Telegram AI Assistant
"""

import asyncio
import sys
from pathlib import Path

# Add src to Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.utils.config import Config
from src.utils.logger import setup_logger

async def test_config():
    """Test configuration loading"""
    print("🔧 Testing configuration...")
    
    # Test config loading
    try:
        print(f"  - Debug mode: {Config.DEBUG}")
        print(f"  - Log level: {Config.LOG_LEVEL}")
        print(f"  - Database URL: {Config.DATABASE_URL}")
        print(f"  - Redis URL: {Config.REDIS_URL}")
        print("✅ Configuration loaded successfully!")
        return True
    except Exception as e:
        print(f"❌ Configuration error: {e}")
        return False

async def test_imports():
    """Test all imports"""
    print("📦 Testing imports...")
    
    try:
        from src.utils.logger import get_logger
        from src.services.ai.openai_service import OpenAIService
        from src.services.database.connection import DatabaseService
        from src.services.cache.redis_client import RedisClient
        from src.bot.handlers.commands import CommandHandler
        from src.bot.handlers.messages import MessageHandler
        
        print("✅ All imports successful!")
        return True
    except Exception as e:
        print(f"❌ Import error: {e}")
        return False

async def test_services():
    """Test service initialization"""
    print("🔧 Testing services...")
    
    try:
        # Test database service
        print("  - Testing database service...")
        from src.services.database.connection import DatabaseService
        db_service = DatabaseService()
        await db_service.initialize()
        print("    ✅ Database service initialized")
        
        # Test Redis service (should work without Redis running)
        print("  - Testing Redis service...")
        from src.services.cache.redis_client import RedisClient
        redis_client = RedisClient()
        await redis_client.initialize()
        print("    ✅ Redis service initialized (with warnings)")
        
        # Test OpenAI service
        print("  - Testing OpenAI service...")
        from src.services.ai.openai_service import OpenAIService
        openai_service = OpenAIService()
        print("    ✅ OpenAI service initialized")
        
        # Cleanup
        await db_service.close()
        await redis_client.close()
        
        print("✅ All services tested successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Service error: {e}")
        return False

async def main():
    """Main test function"""
    print("🧪 Starting Telegram AI Assistant tests...\n")
    
    # Setup logger
    setup_logger(log_file="logs/test.log")
    
    # Run tests
    tests = [
        ("Configuration", test_config),
        ("Imports", test_imports),
        ("Services", test_services),
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n{'='*50}")
        print(f"Running {test_name} test...")
        print('='*50)
        
        try:
            result = await test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} test failed with exception: {e}")
            results.append((test_name, False))
    
    # Summary
    print(f"\n{'='*50}")
    print("TEST SUMMARY")
    print('='*50)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\nResults: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Bot is ready to run.")
        return True
    else:
        print("⚠️  Some tests failed. Check the errors above.")
        return False

if __name__ == "__main__":
    # Create logs directory if it doesn't exist
    Path("logs").mkdir(exist_ok=True)
    Path("data").mkdir(exist_ok=True)
    
    # Run tests
    success = asyncio.run(main())
    sys.exit(0 if success else 1) 