"""
Base handlers for CollaLearn bot.
Handles /start and /help commands.
"""

import logging
from telegram import Update
from telegram.ext import ContextTypes
from telegram.constants import ParseMode

from config import config
from db import Database

logger = logging.getLogger(__name__)


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle /start command.
    Register user and group, send welcome message.
    
    Args:
        update: Telegram update object
        context: Callback context
    """
    try:
        user = update.effective_user
        chat = update.effective_chat
        
        if not user:
            return
        
        db = Database()
        
        # Register user
        db.upsert_user(
            user_id=user.id,
            username=user.username or user.first_name,
            first_name=user.first_name,
            chat_id=chat.id if chat.type in ["group", "supergroup"] else None
        )
        
        # If in group, register group
        if chat.type in ["group", "supergroup"]:
            db.upsert_group(chat_id=chat.id, title=chat.title)
            
            await update.message.reply_text(
                f"✅ **CollaLearn Activated!**\n\n"
                f"🎓 This group is now a **Study Room**.\n\n"
                f"Everyone can:\n"
                f"• Upload study materials\n"
                f"• Search and access files\n"
                f"• Use AI features\n\n"
                f"Type /help to see all commands!",
                parse_mode=ParseMode.MARKDOWN
            )
        else:
            # Private chat
            await update.message.reply_text(
                config.WELCOME_MESSAGE,
                parse_mode=ParseMode.MARKDOWN
            )
        
        logger.info(f"User {user.id} started bot in chat {chat.id}")
        
    except Exception as e:
        logger.error(f"Error in start_command: {e}")
        await update.message.reply_text(
            "⚠️ An error occurred. Please try again later."
        )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle /help command.
    Send detailed help information.
    
    Args:
        update: Telegram update object
        context: Callback context
    """
    try:
        await update.message.reply_text(
            config.HELP_MESSAGE,
            parse_mode=ParseMode.MARKDOWN
        )
        
        logger.info(f"Help command used by {update.effective_user.id}")
        
    except Exception as e:
        logger.error(f"Error in help_command: {e}")
        await update.message.reply_text(
            "⚠️ An error occurred. Please try again later."
        )