# CollaLearn - Collaborative Learning Telegram Bot

**Version:** 1.0.0  
**Author:** LukermanPrint  
**Date:** 2025-11-15

A production-ready Telegram bot designed for collaborative learning in study groups. Built as a BSc Computer Science major project.

---

## 🎯 Overview

CollaLearn transforms any Telegram group into a smart study room where students can:
- Upload and organize study materials
- Search files with intelligent tagging
- Use AI-powered features for summaries, explanations, and quizzes
- Collaborate effectively with classmates

---

## ✨ Features

### 📚 File Management
- Support for PDF, DOCX, PPTX, images, and text files
- Manual and AI-powered tagging
- Smart search with privacy protection
- One-click file retrieval

### 🤖 AI Features (Powered by Perplexity AI)
- **Summarization**: Get concise summaries of study materials
- **Explanations**: Ask questions and get detailed explanations
- **Quiz Generation**: Auto-generate practice MCQs from content
- **Auto-tagging**: AI suggests relevant tags for files

### 👥 Dual Admin System
- **Group Admins**: Manage group-specific settings and files
- **Bot Admins**: Global oversight and bot-wide management

### 🔍 Smart Search
- Search by tags, filenames, or content
- Results visible only to requester (privacy)
- Pagination for large result sets
- Session-based access control

---

## 🛠️ Technology Stack

- **Python 3.10+**
- **python-telegram-bot v20+** (async)
- **MongoDB** for database
- **Perplexity AI API** for AI features
- **PyPDF2, python-docx, python-pptx** for document processing

---

## 📋 Prerequisites

1. **Python 3.10 or higher**
2. **MongoDB** (local or cloud instance)
3. **Telegram Bot Token** (from [@BotFather](https://t.me/botfather))
4. **Perplexity API Key** (from [Perplexity](https://www.perplexity.ai/))

---

## 🚀 Installation

### Step 1: Clone or Download

```bash
# If using git
git clone <repository-url>
cd collalearn

# Or extract the ZIP file
```

### Step 2: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 3: Configure Environment Variables

Copy the example environment file:

```bash
cp .env.example .env
```

Edit `.env` with your credentials:

```env
BOT_TOKEN=your_telegram_bot_token_here
MONGODB_URI=mongodb://localhost:27017/
PERPLEXITY_API_KEY=your_perplexity_api_key_here
GLOBAL_ADMIN_IDS=123456789,987654321
```

**Getting your credentials:**

1. **BOT_TOKEN**: Chat with [@BotFather](https://t.me/botfather) on Telegram
   - Send `/newbot`
   - Follow prompts to create your bot
   - Copy the token provided

2. **MONGODB_URI**: 
   - Local: `mongodb://localhost:27017/`
   - MongoDB Atlas: Get connection string from your cluster

3. **PERPLEXITY_API_KEY**: Sign up at [Perplexity](https://www.perplexity.ai/) and get API key

4. **GLOBAL_ADMIN_IDS**: Your Telegram user ID(s)
   - Get your ID from [@userinfobot](https://t.me/userinfobot)
   - Separate multiple IDs with commas

### Step 4: Start MongoDB

```bash
# If using local MongoDB
mongod

# If using MongoDB Atlas, no action needed
```

### Step 5: Run the Bot

```bash
python main.py
```

You should see:
```
INFO - Configuration loaded successfully
INFO - Database connection established
INFO - Starting CollaLearn bot...
```

---

## 📖 Usage Guide

### For Students

#### 1. Add Bot to Group

- Add @YourBotName to your study group
- Send `/start` in the group
- Group becomes a study room automatically

#### 2. Upload Files

Simply send files to the group:
```
[Upload PDF with caption]
Caption: Operating Systems Unit 2 #os #unit2 #deadlock
```

#### 3. Search Files

```
/search operating systems
/search #unit2
/search deadlock
```

Click the file button to retrieve it!

#### 4. Use AI Features

```
/summary (reply to a file or message)
/explain What is deadlock? (or reply to content)
/quiz 5 (reply to study material)
```

#### 5. Tag Files

```
/tag os deadlock scheduling (reply to a file)
```

### For Group Admins

#### Access Admin Panel

```
/admin
```

#### Available Options

- **⚙️ Group Settings**: Toggle features, set limits
- **📚 File Management**: View and manage uploaded files
- **🤖 AI Controls**: Enable/disable AI features
- **🧍 User Management**: Block/unblock users
- **📊 Statistics**: View group analytics

### For Bot Admins

#### Access Global Admin Panel

```
/global_admin (in private chat with bot)
```

#### Available Options

- **🌍 View All Groups**: See all registered groups
- **📊 Global Statistics**: Bot-wide analytics
- **🤖 Global AI Settings**: Manage AI configuration
- **📤 Broadcast**: Send announcements (coming soon)
- **🗑 Manage Groups**: Delete groups from database

---

## 🏗️ Project Structure

```
collalearn/
│
├── main.py                 # Entry point
├── config.py              # Configuration and constants
├── db.py                  # Database operations
├── ai_client.py           # Perplexity AI client
│
├── handlers/              # Command and callback handlers
│   ├── __init__.py
│   ├── base_handlers.py   # /start, /help
│   ├── file_handlers.py   # File uploads, tagging
│   ├── search_handlers.py # Search functionality
│   ├── ai_handlers.py     # AI features
│   └── admin_handlers.py  # Admin panels
│
├── models/                # Database models
│   ├── __init__.py
│   ├── user_model.py
│   ├── group_model.py
│   ├── file_model.py
│   └── search_session_model.py
│
├── utils/                 # Utility functions
│   ├── __init__.py
│   ├── text_extract.py    # Text extraction from files
│   ├── validator.py       # Validation functions
│   └── parser.py          # Parsing utilities
│
├── requirements.txt       # Python dependencies
├── .env.example          # Environment template
└── README.md             # This file
```

---

## 🗄️ Database Schema

### Collections

#### `users`
```javascript
{
  user_id: int,
  username: string,
  first_name: string,
  first_seen_at: datetime,
  last_seen_at: datetime,
  is_global_admin: boolean,
  groups: [chat_ids]
}
```

#### `groups`
```javascript
{
  chat_id: int,
  title: string,
  created_at: datetime,
  last_seen_at: datetime,
  settings: {
    ai_enabled: boolean,
    summarization_enabled: boolean,
    explanation_enabled: boolean,
    quiz_enabled: boolean,
    auto_tag_enabled: boolean,
    max_search_results: int,
    search_sort_order: string,
    blocked_users: [user_ids],
    admin_only_indexing: boolean
  },
  stats: {
    total_files: int,
    total_ai_requests: int
  }
}
```

#### `files`
```javascript
{
  file_id: string,
  file_unique_id: string,
  file_name: string,
  mime_type: string,
  caption: string,
  tags: [strings],
  ai_tags: [strings],
  uploader_id: int,
  uploader_username: string,
  group_id: int,
  message_id: int,
  uploaded_at: datetime,
  deleted: boolean
}
```

#### `search_sessions`
```javascript
{
  session_id: string (uuid),
  requester_id: int,
  group_id: int,
  results: [file_ids],
  created_at: datetime,
  expires_at: datetime
}
```

#### `ai_logs`
```javascript
{
  user_id: int,
  group_id: int,
  prompt_type: string,
  text_snippet: string,
  created_at: datetime
}
```

---

## 🔧 Configuration Options

Edit `config.py` to customize:

```python
# File limits
MAX_FILE_SIZE_MB = 20
MAX_TAGS_PER_FILE = 20

# Search settings
MAX_SEARCH_RESULTS_DEFAULT = 10
SEARCH_SESSION_EXPIRY_HOURS = 1

# AI settings
MAX_AI_TEXT_LENGTH = 8000
AI_TEMPERATURE = 0.2
AI_MAX_TOKENS = 1024

# Pagination
FILES_PER_PAGE = 5
GROUPS_PER_PAGE = 10
```

---

## 🐛 Troubleshooting

### Bot doesn't respond

1. Check bot token in `.env`
2. Verify bot is added to group
3. Check MongoDB connection
4. Review logs in console

### AI features not working

1. Verify Perplexity API key
2. Check `ai_enabled` in group settings
3. Ensure sufficient API credits

### File upload fails

1. Check file size (<20MB)
2. Verify file type is supported
3. Check group settings for admin-only upload

### Search returns no results

1. Verify files are uploaded to current group
2. Check if files have tags
3. Try different search terms

---

## 📊 Performance Considerations

- **Database Indexing**: Automatically created on startup
- **Session Cleanup**: Runs every 30 minutes
- **File Storage**: Uses Telegram's servers (no local storage)
- **Async Operations**: All I/O operations are asynchronous

---

## 🔒 Security Features

- **Admin Verification**: Checks Telegram admin status
- **Search Privacy**: Results only visible to requester
- **User Blocking**: Group admins can block users
- **Input Validation**: All inputs sanitized
- **Error Handling**: Comprehensive error catching

---

## 🚦 Deployment

### Development Mode

```bash
python main.py
```

### Production with systemd (Linux)

1. Create service file `/etc/systemd/system/collalearn.service`:

```ini
[Unit]
Description=CollaLearn Telegram Bot
After=network.target mongodb.service

[Service]
Type=simple
User=youruser
WorkingDirectory=/path/to/collalearn
Environment="PATH=/path/to/venv/bin"
ExecStart=/path/to/venv/bin/python main.py
Restart=always

[Install]
WantedBy=multi-user.target
```

2. Start service:

```bash
sudo systemctl daemon-reload
sudo systemctl start collalearn
sudo systemctl enable collalearn
```

### Production with Docker

Create `Dockerfile`:

```dockerfile
FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "main.py"]
```

Build and run:

```bash
docker build -t collalearn .
docker run -d --name collalearn --env-file .env collalearn
```

---

## 📝 Future Enhancements

- [ ] OCR for text extraction from images
- [ ] Voice note transcription
- [ ] Collaborative note-taking
- [ ] Scheduled quizzes
- [ ] Progress tracking
- [ ] Multi-language support
- [ ] Integration with learning platforms

---

## 🤝 Contributing

This project was created as a BSc Computer Science major project by LukermanPrint.

For contributions or suggestions:
1. Fork the repository
2. Create a feature branch
3. Submit a pull request

---

## 📄 License

This project is created for educational purposes as part of a BSc Computer Science major project.

---

## 👨‍💻 Author

**LukermanPrint**  
BSc Computer Science  
Date: November 15, 2025

---

## 📞 Support

For issues or questions:
- Check the Troubleshooting section above
- Review logs in the console
- Contact the bot administrator

---

## 🙏 Acknowledgments

- Python Telegram Bot library
- Perplexity AI for AI capabilities
- MongoDB for database
- Open source community

---

**Happy Learning! 🎓**