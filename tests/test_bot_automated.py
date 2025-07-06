#!/usr/bin/env python3
"""
Automated testing system for Telegram AI Assistant
This script simulates user interactions and tests bot functionality
"""

import asyncio
import json
import sys
from pathlib import Path
from typing import Dict, Any, List
from datetime import datetime

# Add src to Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.utils.logger import setup_logger
from src.services.user_settings import UserSettingsService
from src.services.ai.ai_service import AIService
from src.bot.handlers.commands import CommandHandler
from src.bot.handlers.ai_commands import AICommandsHandler
from src.bot.handlers.settings_commands import SettingsCommandsHandler

# Setup logger
logger = setup_logger(log_file="logs/test_automated.log")

class MockUpdate:
    """Mock Update object for testing"""
    
    def __init__(self, user_id: int, chat_id: int, message_text: str = None, callback_data: str = None):
        self.effective_user = MockUser(user_id)
        self.effective_chat = MockChat(chat_id)
        self.message = MockMessage(message_text) if message_text else None
        self.callback_query = MockCallbackQuery(callback_data, user_id, chat_id) if callback_data else None

class MockUser:
    """Mock User object"""
    
    def __init__(self, user_id: int):
        self.id = user_id
        self.first_name = f"TestUser{user_id}"

class MockChat:
    """Mock Chat object"""
    
    def __init__(self, chat_id: int):
        self.id = chat_id

class MockMessage:
    """Mock Message object"""
    
    def __init__(self, text: str):
        self.text = text
    
    async def reply_text(self, text: str, **kwargs):
        print(f"📤 REPLY: {text}")
        return MockResponse()

class MockCallbackQuery:
    """Mock CallbackQuery object"""
    
    def __init__(self, data: str, user_id: int, chat_id: int):
        self.data = data
        self.from_user = MockUser(user_id)
        self.message = MockMessage("")
        self.message.chat_id = chat_id
    
    async def answer(self):
        print(f"🔘 CALLBACK ANSWER: {self.data}")
    
    async def edit_message_text(self, text: str, **kwargs):
        print(f"📤 EDIT: {text}")
        return MockResponse()

class MockResponse:
    """Mock Response object"""
    pass

class MockContext:
    """Mock Context object"""
    
    def __init__(self):
        self.user_data = {}

class BotTester:
    """Automated bot testing system"""
    
    def __init__(self):
        self.user_settings = UserSettingsService()
        self.ai_service = AIService()
        self.command_handler = CommandHandler(self.ai_service)
        self.ai_commands_handler = AICommandsHandler(self.ai_service)
        self.settings_commands_handler = SettingsCommandsHandler(self.user_settings)
        
        self.test_results = []
        self.user_id = 123456789
        self.chat_id = 123456789
    
    def log_test(self, test_name: str, success: bool, details: str = ""):
        """Log test result"""
        result = {
            "test": test_name,
            "success": success,
            "details": details,
            "timestamp": datetime.now().isoformat()
        }
        self.test_results.append(result)
        
        status = "✅" if success else "❌"
        print(f"{status} {test_name}: {details}")
    
    async def test_command_handler(self):
        """Test command handler functionality"""
        print("\n🧪 Testing Command Handler...")
        
        context = MockContext()
        
        # Test /start command
        try:
            update = MockUpdate(self.user_id, self.chat_id, "/start")
            await self.command_handler.start_command(update, context)
            self.log_test("Command: /start", True, "Start command executed successfully")
        except Exception as e:
            self.log_test("Command: /start", False, str(e))
        
        # Test /help command
        try:
            update = MockUpdate(self.user_id, self.chat_id, "/help")
            await self.command_handler.help_command(update, context)
            self.log_test("Command: /help", True, "Help command executed successfully")
        except Exception as e:
            self.log_test("Command: /help", False, str(e))
        
        # Test /stats command
        try:
            update = MockUpdate(self.user_id, self.chat_id, "/stats")
            await self.command_handler.stats_command(update, context)
            self.log_test("Command: /stats", True, "Stats command executed successfully")
        except Exception as e:
            self.log_test("Command: /stats", False, str(e))
        
        # Test /clear command
        try:
            update = MockUpdate(self.user_id, self.chat_id, "/clear")
            await self.command_handler.clear_command(update, context)
            self.log_test("Command: /clear", True, "Clear command executed successfully")
        except Exception as e:
            self.log_test("Command: /clear", False, str(e))
    
    async def test_callback_handlers(self):
        """Test callback handler functionality"""
        print("\n🧪 Testing Callback Handlers...")
        
        context = MockContext()
        
        # Test command callbacks
        command_callbacks = ["help", "stats", "clear", "back_to_main"]
        for callback_data in command_callbacks:
            try:
                update = MockUpdate(self.user_id, self.chat_id, callback_data=callback_data)
                await self.command_handler.callback_handler(update, context)
                self.log_test(f"Callback: {callback_data}", True, "Command callback executed successfully")
            except Exception as e:
                self.log_test(f"Callback: {callback_data}", False, str(e))
        
        # Test AI provider callbacks
        ai_callbacks = ["provider_openai", "provider_claude", "provider_status", "providers_back"]
        for callback_data in ai_callbacks:
            try:
                update = MockUpdate(self.user_id, self.chat_id, callback_data=callback_data)
                await self.ai_commands_handler.handle_callback(update, context)
                self.log_test(f"AI Callback: {callback_data}", True, "AI callback executed successfully")
            except Exception as e:
                self.log_test(f"AI Callback: {callback_data}", False, str(e))
        
        # Test settings callbacks
        settings_callbacks = ["add_api_key", "remove_api_key", "select_provider", "back_to_settings", "user_stats"]
        for callback_data in settings_callbacks:
            try:
                update = MockUpdate(self.user_id, self.chat_id, callback_data=callback_data)
                await self.settings_commands_handler.handle_callback(update, context)
                self.log_test(f"Settings Callback: {callback_data}", True, "Settings callback executed successfully")
            except Exception as e:
                self.log_test(f"Settings Callback: {callback_data}", False, str(e))
    
    async def test_user_settings(self):
        """Test user settings functionality"""
        print("\n🧪 Testing User Settings...")
        
        # Test API key management
        try:
            # Set API key
            self.user_settings.set_user_api_key(self.user_id, "openai", "test_key_123")
            api_keys = self.user_settings.get_user_api_keys(self.user_id)
            if "openai" in api_keys and api_keys["openai"] == "test_key_123":
                self.log_test("User Settings: Set API Key", True, "API key set successfully")
            else:
                self.log_test("User Settings: Set API Key", False, "API key not set correctly")
        except Exception as e:
            self.log_test("User Settings: Set API Key", False, str(e))
        
        # Test preferences
        try:
            self.user_settings.set_user_preference(self.user_id, "provider", "openai")
            preferences = self.user_settings.get_user_preferences(self.user_id)
            if preferences.get("provider") == "openai":
                self.log_test("User Settings: Set Preference", True, "Preference set successfully")
            else:
                self.log_test("User Settings: Set Preference", False, "Preference not set correctly")
        except Exception as e:
            self.log_test("User Settings: Set Preference", False, str(e))
        
        # Test API key removal
        try:
            self.user_settings.remove_user_api_key(self.user_id, "openai")
            api_keys = self.user_settings.get_user_api_keys(self.user_id)
            if "openai" not in api_keys:
                self.log_test("User Settings: Remove API Key", True, "API key removed successfully")
            else:
                self.log_test("User Settings: Remove API Key", False, "API key not removed")
        except Exception as e:
            self.log_test("User Settings: Remove API Key", False, str(e))
    
    async def test_ai_service(self):
        """Test AI service functionality"""
        print("\n🧪 Testing AI Service...")
        
        try:
            providers = self.ai_service.get_available_providers()
            self.log_test("AI Service: Get Providers", True, f"Found providers: {providers}")
        except Exception as e:
            self.log_test("AI Service: Get Providers", False, str(e))
        
        try:
            status = self.ai_service.get_provider_status()
            self.log_test("AI Service: Get Status", True, f"Status: {status}")
        except Exception as e:
            self.log_test("AI Service: Get Status", False, str(e))
    
    def generate_report(self):
        """Generate test report"""
        print("\n📊 Test Report")
        print("=" * 50)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result["success"])
        failed_tests = total_tests - passed_tests
        
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests} ✅")
        print(f"Failed: {failed_tests} ❌")
        print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        
        if failed_tests > 0:
            print("\n❌ Failed Tests:")
            for result in self.test_results:
                if not result["success"]:
                    print(f"  • {result['test']}: {result['details']}")
        
        # Save report to file
        report_file = Path("logs/test_report.json")
        report_file.parent.mkdir(exist_ok=True)
        
        report_data = {
            "timestamp": datetime.now().isoformat(),
            "summary": {
                "total": total_tests,
                "passed": passed_tests,
                "failed": failed_tests,
                "success_rate": (passed_tests/total_tests)*100
            },
            "results": self.test_results
        }
        
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, indent=2, ensure_ascii=False)
        
        print(f"\n📄 Detailed report saved to: {report_file}")
        
        return passed_tests == total_tests
    
    async def run_all_tests(self):
        """Run all tests"""
        print("🚀 Starting Automated Bot Tests...")
        print("=" * 50)
        
        await self.test_command_handler()
        await self.test_callback_handlers()
        await self.test_user_settings()
        await self.test_ai_service()
        
        success = self.generate_report()
        
        if success:
            print("\n🎉 All tests passed!")
        else:
            print("\n⚠️ Some tests failed. Check the report for details.")
        
        return success

async def main():
    """Main test function"""
    tester = BotTester()
    await tester.run_all_tests()

if __name__ == "__main__":
    asyncio.run(main()) 