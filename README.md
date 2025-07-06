# 🤖 Telegram AI Assistant

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://python.org)
[![Telegram Bot API](https://img.shields.io/badge/Telegram%20Bot%20API-20+-green.svg)](https://core.telegram.org/bots/api)
[![Docker](https://img.shields.io/badge/Docker-Ready-blue.svg)](https://docker.com)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

> **🇷🇺 [Read in Russian](README/README_RU.md)**

## 📚 Documentation
- [Quick Start](/docs/QUICK_START.md)
- [Deployment Guide](/docs/DEPLOYMENT_GUIDE.md)
- [AI Providers Guide](/docs/AI_PROVIDERS_GUIDE.md)
- [Testing Guide](/docs/TESTING_GUIDE.md)
- [Upgrade Guide](/docs/UPGRADE_GUIDE.md)

A multifunctional Telegram bot with support for multiple AI providers (OpenAI GPT, Anthropic Claude) and convenient settings management directly in the chat.

## ✨ Features

- 🤖 **Multiple AI Providers**: OpenAI GPT and Anthropic Claude
- ⚙️ **In-bot API Key Management**: Add and remove keys directly in the chat
- 🎯 **Personal Settings**: Each user can choose their preferred provider and model
- 📊 **Usage Statistics**: Message and token tracking
- 🔄 **Caching**: Redis for fast responses
- 🗄️ **Database**: PostgreSQL for storing statistics and settings
- 🐳 **Docker Support**: Full containerization with Docker Compose
- 📱 **Multimedia Support**: Text, photos, documents, voice messages

## 🚀 Quick Start

### Option 1: Docker Compose (Production - Recommended)

1. **Clone the repository:**
```bash
git clone <repository-url>
cd telegram-ai-assistant
```

2. **Create .env file:**
```bash
cp env.example .env
```

3. **Configure environment variables in .env:**
```env
TELEGRAM_BOT_TOKEN=your_telegram_bot_token
```

4. **Start production version:**

**Windows:**
```cmd
start_production.bat
```

**Linux/Mac:**
```bash
chmod +x start_production.sh
./start_production.sh
```

**Or manually:**
```bash
docker-compose up -d
```

5. **Configure API keys in the bot:**
   - Send `/settings` to the bot
   - Add your API keys for OpenAI and/or Claude
   - Choose your preferred provider
   - **Important:** API keys are no longer needed in the .env file!

### Option 2: Local Installation

1. **Install dependencies:**
```bash
pip install -r requirements.txt
```

2. **Configure .env file** (as in option 1)

3. **Start the bot:**
```bash
python run_bot.py
```

## ⚙️ Settings Management

### Bot Commands

- `/start` - Start working with the bot
- `/settings` - Manage settings and API keys
- `/providers` - View available AI providers
- `/status` - Provider status
- `/stats` - Your usage statistics
- `/clear` - Clear conversation history
- `/help` - Help

### Adding API Keys

1. Send `/settings`
2. Click "🔑 Add API Key"
3. Choose provider (OpenAI or Claude)
4. Send your API key
5. The key will be saved and masked for security

### Choosing a Provider

1. In settings, click "🎯 Choose Provider"
2. Select an available provider (✅ means key is configured)
3. The provider will be set as preferred

## 🏗️ Architecture

```
telegram-ai-assistant/
├── src/
│   ├── bot/handlers/          # Command and message handlers
│   ├── services/
│   │   ├── ai/               # AI providers and services
│   │   ├── database/         # Database operations
│   │   ├── cache/            # Redis caching
│   │   └── user_settings.py  # User settings management
│   └── utils/                # Utilities and configuration
├── data/                     # User data and settings
├── logs/                     # Application logs
├── docker-compose.yml        # Docker Compose configuration
├── Dockerfile               # Docker image
└── requirements.txt         # Python dependencies
```

## 🔧 Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `TELEGRAM_BOT_TOKEN` | Telegram bot token | **Required** |
| `TELEGRAM_WEBHOOK_URL` | URL for webhook mode | Optional |
| `DATABASE_URL` | Database URL | `sqlite:///data/bot_data.db` |
| `REDIS_URL` | Redis URL | `redis://localhost:6379` |
| `DEBUG` | Debug mode | `False` |
| `LOG_LEVEL` | Logging level | `INFO` |

**Note:** AI provider API keys are now managed through the bot interface (`/settings`), not through the .env file!

### Database

The project supports:
- **SQLite** (for development)
- **PostgreSQL** (for production, via Docker)

### Caching

Redis is used for:
- Caching AI responses
- Storing temporary data
- Rate limiting

## 🐳 Docker

### Services

- **bot** - Main application
- **postgres** - PostgreSQL database
- **redis** - Redis cache

### Commands

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f bot

# Stop
docker-compose down

# Rebuild
docker-compose up -d --build
```

## 🔒 Security

- API keys are stored locally in encrypted form
- Keys are masked in the interface
- SSL support for PostgreSQL
- API key format validation

## 📊 Monitoring

### Logs

Logs are saved in `logs/`:
- `bot.log` - Main application logs
- `test.log` - Test logs

### Statistics

The bot tracks:
- Message count
- Tokens used
- Daily/weekly activity
- User preferences

## 🧪 Testing

```bash
# Run tests
pytest

# With coverage
pytest --cov=src

# Test the bot
python tests/test_bot.py
```

## 🤝 Contributing

1. Fork the repository
2. Create a branch for your feature
3. Make changes
4. Add tests
5. Create a Pull Request

## 📝 License

MIT License - see LICENSE file for details.

## 🆘 Support

If you have questions or issues:

1. Check the [Issues](../../issues) section
2. Create a new issue with detailed description
3. Make sure to include logs and configuration

---

**Note**: This bot is intended for personal use. Make sure you comply with the terms of use of API providers and Telegram. 