"""
Configuration module for CollaLearn bot.
Loads and validates environment variables and defines constants.
"""

import os
from typing import List
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class Config:
    """
    Configuration class containing all bot settings and constants.
    """
    
    # Bot credentials
    BOT_TOKEN: str = os.getenv("BOT_TOKEN", "")
    MONGODB_URI: str = os.getenv("MONGODB_URI", "mongodb://localhost:27017/")
    PERPLEXITY_API_KEY: str = os.getenv("PERPLEXITY_API_KEY", "")
    
    # Admin configuration
    GLOBAL_ADMIN_IDS: List[int] = [
        int(id_str.strip()) 
        for id_str in os.getenv("GLOBAL_ADMIN_IDS", "").split(",") 
        if id_str.strip().isdigit()
    ]
    
    # Database settings
    DB_NAME: str = "collalearn"
    
    # Collections
    USERS_COLLECTION: str = "users"
    GROUPS_COLLECTION: str = "groups"
    FILES_COLLECTION: str = "files"
    SEARCH_SESSIONS_COLLECTION: str = "search_sessions"
    AI_LOGS_COLLECTION: str = "ai_logs"
    
    # File type restrictions
    SUPPORTED_MIME_TYPES: List[str] = [
        "application/pdf",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",  # docx
        "application/vnd.openxmlformats-officedocument.presentationml.presentation",  # pptx
        "application/msword",  # doc
        "text/plain",
        "image/jpeg",
        "image/png",
        "image/jpg"
    ]
    
    # Limits and timeouts
    MAX_FILE_SIZE_MB: int = 20
    MAX_SEARCH_RESULTS_DEFAULT: int = 10
    MAX_SEARCH_RESULTS_LIMIT: int = 50
    SEARCH_SESSION_EXPIRY_HOURS: int = 1
    MAX_AI_TEXT_LENGTH: int = 8000
    MAX_TAG_LENGTH: int = 50
    MAX_TAGS_PER_FILE: int = 20
    
    # Pagination
    FILES_PER_PAGE: int = 5
    GROUPS_PER_PAGE: int = 10
    
    # AI Configuration
    PERPLEXITY_API_URL: str = "https://api.perplexity.ai/chat/completions"
    # Correct model name as per Perplexity documentation (2024)
    PERPLEXITY_MODEL: str = os.getenv("PERPLEXITY_MODEL", "sonar")
    AI_TEMPERATURE: float = 0.2
    AI_MAX_TOKENS: int = 1024
    
    # Default group settings
    DEFAULT_GROUP_SETTINGS: dict = {
        "ai_enabled": True,
        "summarization_enabled": True,
        "explanation_enabled": True,
        "quiz_enabled": True,
        "auto_tag_enabled": True,
        "max_search_results": 10,
        "search_sort_order": "relevance",
        "blocked_users": [],
        "admin_only_indexing": False
    }
    
    # Messages
    WELCOME_MESSAGE: str = """
🎓 **Welcome to CollaLearn!**

I'm your collaborative study assistant. Here's what I can do:

📚 **File Management:**
• Upload study materials (PDF, DOCX, PPTX, images, text)
• Tag files for easy organization
• AI-powered auto-tagging

🔍 **Smart Search:**
• Search files with `/search <query>`
• Access files with one click
• Privacy-protected results

🤖 **AI Features:**
• `/summary` - Summarize content
• `/explain` - Get explanations
• `/quiz <n>` - Generate practice quizzes

👥 **Study Rooms:**
• Any group becomes a study room automatically
• Collaborate with classmates
• Share and organize materials together

Type /help for detailed commands!
    """
    
    HELP_MESSAGE: str = """
📖 **CollaLearn Help**

**📤 Uploading Files:**
• Send any PDF, document, or image to the group
• Add hashtags in caption like #unit1 #physics
• Or use `/tag <tags>` by replying to a file

**🔍 Searching:**
• `/search <query>` - Find files by tags or name
• Click buttons to retrieve files
• Only you can access your search results

**🤖 AI Commands:**
• `/summary` - Reply to a message to get summary
• `/explain <topic>` - Get explanation (or reply)
• `/quiz <number>` - Generate MCQs (reply to file)

**⚙️ Admin Commands:**
• `/admin` - Group settings panel (group admins)
• `/global_admin` - Bot management (bot admins only)

**💡 Tips:**
• Use specific tags for better organization
• AI works best with clear, focused content
• Search is scoped to your current group

Need help? Contact the bot administrator!
    """
    
    def __init__(self):
        """Validate required environment variables."""
        self.validate()
    
    def validate(self) -> None:
        """
        Validate that all required environment variables are set.
        
        Raises:
            ValueError: If any required variable is missing
        """
        if not self.BOT_TOKEN:
            raise ValueError("BOT_TOKEN environment variable is required")
        
        if not self.MONGODB_URI:
            raise ValueError("MONGODB_URI environment variable is required")
        
        if not self.PERPLEXITY_API_KEY:
            raise ValueError("PERPLEXITY_API_KEY environment variable is required")
        
        if not self.GLOBAL_ADMIN_IDS:
            raise ValueError("GLOBAL_ADMIN_IDS environment variable is required")


# Create global config instance
config = Config()