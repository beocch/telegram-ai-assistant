#!/usr/bin/env python3
"""
Скрипт для переключения между polling и webhook режимами
"""

import os
import re
from pathlib import Path

def read_env_file():
    """Читает содержимое .env файла"""
    env_path = Path('.env')
    if not env_path.exists():
        print("❌ Файл .env не найден!")
        return None
    
    with open(env_path, 'r', encoding='utf-8') as f:
        return f.read()

def write_env_file(content):
    """Записывает содержимое в .env файл"""
    with open('.env', 'w', encoding='utf-8') as f:
        f.write(content)

def switch_to_polling():
    """Переключает бота в polling режим"""
    content = read_env_file()
    if content is None:
        return False
    
    # Закомментируем webhook URL
    content = re.sub(
        r'^TELEGRAM_WEBHOOK_URL=',
        '# TELEGRAM_WEBHOOK_URL=',
        content,
        flags=re.MULTILINE
    )
    
    write_env_file(content)
    print("✅ Переключено в POLLING режим")
    print("📝 Webhook URL закомментирован")
    return True

def switch_to_webhook(url=None):
    """Переключает бота в webhook режим"""
    content = read_env_file()
    if content is None:
        return False
    
    if url:
        # Раскомментируем и установим новый URL
        content = re.sub(
            r'^# TELEGRAM_WEBHOOK_URL=.*',
            f'TELEGRAM_WEBHOOK_URL={url}',
            content,
            flags=re.MULTILINE
        )
        content = re.sub(
            r'^TELEGRAM_WEBHOOK_URL=.*',
            f'TELEGRAM_WEBHOOK_URL={url}',
            content,
            flags=re.MULTILINE
        )
    else:
        # Просто раскомментируем
        content = re.sub(
            r'^# TELEGRAM_WEBHOOK_URL=',
            'TELEGRAM_WEBHOOK_URL=',
            content,
            flags=re.MULTILINE
        )
    
    write_env_file(content)
    print("✅ Переключено в WEBHOOK режим")
    if url:
        print(f"🌐 Webhook URL: {url}")
    else:
        print("📝 Webhook URL раскомментирован (установите правильный URL)")
    return True

def show_current_mode():
    """Показывает текущий режим работы"""
    content = read_env_file()
    if content is None:
        return
    
    if re.search(r'^# TELEGRAM_WEBHOOK_URL=', content, re.MULTILINE):
        print("🔄 Текущий режим: POLLING")
        print("📡 Бот будет опрашивать Telegram самостоятельно")
    else:
        webhook_match = re.search(r'^TELEGRAM_WEBHOOK_URL=(.+)$', content, re.MULTILINE)
        if webhook_match:
            url = webhook_match.group(1).strip()
            print(f"🌐 Текущий режим: WEBHOOK")
            print(f"📡 Webhook URL: {url}")
        else:
            print("❓ Режим не определен")

def main():
    """Главная функция"""
    print("🤖 Telegram AI Assistant - Переключение режимов")
    print("=" * 50)
    
    while True:
        print("\nВыберите действие:")
        print("1. Показать текущий режим")
        print("2. Переключить в POLLING режим")
        print("3. Переключить в WEBHOOK режим")
        print("4. Выход")
        
        choice = input("\nВведите номер (1-4): ").strip()
        
        if choice == '1':
            show_current_mode()
        
        elif choice == '2':
            if switch_to_polling():
                print("\n💡 Для запуска используйте: python run_bot.py")
        
        elif choice == '3':
            url = input("Введите webhook URL (или Enter для раскомментирования): ").strip()
            if switch_to_webhook(url if url else None):
                print("\n💡 Для запуска используйте: python main.py")
        
        elif choice == '4':
            print("👋 До свидания!")
            break
        
        else:
            print("❌ Неверный выбор. Попробуйте снова.")

if __name__ == "__main__":
    main() 