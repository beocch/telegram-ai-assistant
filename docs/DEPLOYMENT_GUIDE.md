# 🚀 Руководство по деплою Telegram AI Assistant

## 📋 Режимы работы бота

### 🔄 Polling режим (для разработки и тестирования)
- **Как работает:** Бот сам опрашивает Telegram каждые несколько секунд на предмет новых сообщений
- **Преимущества:** Простая настройка, не требует публичного URL, подходит для локальной разработки
- **Недостатки:** Менее эффективен, требует постоянного подключения

### 🌐 Webhook режим (для production)
- **Как работает:** Telegram сам отправляет все новые сообщения на ваш сервер по HTTPS
- **Преимущества:** Более эффективен, быстрее реагирует, подходит для production
- **Недостатки:** Требует публичный HTTPS URL, сложнее в настройке

---

## 🔧 Настройка для тестирования (Polling режим)

### 1. Получение токенов

#### Telegram Bot Token
1. Найдите [@BotFather](https://t.me/BotFather) в Telegram
2. Отправьте команду `/newbot`
3. Следуйте инструкциям и получите токен вида: `123456789:ABCdefGHIjklMNOpqrsTUVwxyz`

#### OpenAI API Key
1. Зайдите на [platform.openai.com](https://platform.openai.com)
2. Создайте аккаунт или войдите
3. Перейдите в раздел API Keys
4. Создайте новый ключ

### 2. Настройка .env файла

Откройте файл `.env` и замените значения:

```env
# Telegram Bot Configuration
TELEGRAM_BOT_TOKEN=123456789:ABCdefGHIjklMNOpqrsTUVwxyz
# TELEGRAM_WEBHOOK_URL=https://your-domain.com/webhook  # Закомментировано для polling

# OpenAI Configuration
OPENAI_API_KEY=sk-your-openai-api-key-here
OPENAI_MODEL=gpt-3.5-turbo
OPENAI_MAX_TOKENS=1000
OPENAI_TEMPERATURE=0.7

# Остальные настройки оставьте как есть
```

### 3. Запуск бота

```bash
# Установка зависимостей
pip install -r requirements.txt

# Быстрый запуск для тестирования
python run_bot.py
```

### 4. Тестирование

1. Найдите вашего бота в Telegram
2. Отправьте `/start`
3. Напишите любое сообщение
4. Бот должен ответить с помощью AI

---

## 🌐 Настройка для production (Webhook режим)

### Вариант 1: Через ngrok (для тестирования webhook)

#### Установка ngrok
```bash
# Через npm
npm install -g ngrok

# Или скачайте с https://ngrok.com/download
```

#### Настройка
1. Запустите ngrok:
   ```bash
   ngrok http 8000
   ```

2. Скопируйте HTTPS URL (например: `https://abc123.ngrok.io`)

3. В `.env` раскомментируйте и настройте webhook:
   ```env
   TELEGRAM_WEBHOOK_URL=https://abc123.ngrok.io/webhook
   ```

4. Запустите бота:
   ```bash
   python main.py
   ```

### Вариант 2: На реальном сервере

#### Требования к серверу
- Публичный домен с SSL сертификатом
- Python 3.11+
- Доступ к интернету

#### Настройка на VPS/хостинге

1. **Загрузите код на сервер:**
   ```bash
   git clone https://github.com/your-username/telegram-ai-assistant.git
   cd telegram-ai-assistant
   ```

2. **Настройте .env:**
   ```env
   TELEGRAM_BOT_TOKEN=your_bot_token
   TELEGRAM_WEBHOOK_URL=https://your-domain.com/webhook
   OPENAI_API_KEY=your_openai_key
   ```

3. **Установите зависимости:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Настройте веб-сервер (например, nginx):**
   ```nginx
   server {
       listen 443 ssl;
       server_name your-domain.com;
       
       location /webhook {
           proxy_pass http://localhost:8000;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
       }
   }
   ```

5. **Запустите бота:**
   ```bash
   python main.py
   ```

### Вариант 3: Через Docker

```bash
# Сборка и запуск
docker-compose up -d

# Проверка логов
docker-compose logs -f telegram-bot
```

---

## 🔄 Переключение между режимами

### Из Polling в Webhook
1. Раскомментируйте `TELEGRAM_WEBHOOK_URL` в `.env`
2. Укажите правильный HTTPS URL
3. Перезапустите бота: `python main.py`

### Из Webhook в Polling
1. Закомментируйте `TELEGRAM_WEBHOOK_URL` в `.env`
2. Перезапустите бота: `python main.py`

---

## 🐛 Решение проблем

### Бот не отвечает
- Проверьте правильность токенов в `.env`
- Убедитесь, что бот не заблокирован
- Проверьте логи в `logs/bot.log`

### Ошибка "Redis connection failed"
- Это нормально для тестирования
- Redis не обязателен, бот работает без него

### Webhook не работает
- Проверьте, что URL доступен из интернета
- Убедитесь, что используется HTTPS
- Проверьте, что порт 8000 открыт

### Ошибка "Missing required environment variables"
- Проверьте, что файл `.env` создан
- Убедитесь, что токены указаны правильно
- Проверьте, что нет лишних пробелов

---

## 📊 Мониторинг

### Логи
- Основные логи: `logs/bot.log`
- Тестовые логи: `logs/test.log`

### Статистика
- Команда `/stats` в боте показывает статистику
- База данных: `data/bot_data.db`

---

## 🔒 Безопасность

- **НЕ публикуйте** файл `.env` в GitHub
- Используйте разные токены для тестирования и production
- Регулярно обновляйте зависимости
- Мониторьте логи на подозрительную активность

---

## 📞 Поддержка

Если возникли проблемы:
1. Проверьте логи в `logs/`
2. Убедитесь, что все зависимости установлены
3. Проверьте правильность конфигурации
4. Создайте issue в GitHub репозитории

---

**Удачного деплоя! 🚀** 