"""
CollaLearn Telegram Bot - Main Entry Point
A collaborative learning bot for Telegram groups
Author: LukermanPrint
Date: 2025-11-15
"""

import logging
import asyncio
from datetime import datetime, timedelta
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
    ContextTypes
)

from config import Config
from db import Database
from handlers import base_handlers, file_handlers, search_handlers, ai_handlers, admin_handlers

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)


async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Global error handler for the bot.
    
    Args:
        update: The update that caused the error
        context: The context object containing error information
    """
    logger.error(f"Exception while handling an update: {context.error}", exc_info=context.error)
    
    # Try to inform the user about the error
    if isinstance(update, Update) and update.effective_message:
        try:
            await update.effective_message.reply_text(
                "⚠️ An error occurred while processing your request. "
                "Please try again later or contact the bot administrator."
            )
        except Exception as e:
            logger.error(f"Failed to send error message to user: {e}")


async def cleanup_expired_sessions(context: ContextTypes.DEFAULT_TYPE) -> None:
            logger.error(f"Failed to send error message to user: {e}")


async def cleanup_expired_sessions(context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Background job to clean up expired search sessions.
    Runs periodically to maintain database hygiene.
    """
    try:
        db = Database()
        result = await db.cleanup_expired_search_sessions()
        if result > 0:
            logger.info(f"Cleaned up {result} expired search sessions")
    except Exception as e:
        logger.error(f"Error in cleanup job: {e}")


def main() -> None:
    """
    Main function to initialize and run the bot.
    Sets up all handlers, jobs, and starts polling.
    """
    try:
        # Initialize configuration
        config = Config()
        logger.info("Configuration loaded successfully")
        
        # Initialize database
        db = Database()
        logger.info("Database connection established")
        
        async def notify_admin(app):
            """
            Notify global admins that the bot is online.
            """
            for admin_id in config.GLOBAL_ADMIN_IDS:
                try:
                    await app.bot.send_message(
                        chat_id=admin_id,
                        text="🤖 CollaLearn Bot is now online!"
                    )
                    logger.info(f"Notified admin {admin_id} that bot is online")
                except Exception as e:
                    logger.error(f"Failed to notify admin {admin_id}: {e}")
        
        # Build the application
        application = (
            Application.builder()
            .token(config.BOT_TOKEN)
            .post_init(notify_admin)
            .build()
        )
        
        # Register base handlers
        application.add_handler(CommandHandler("start", base_handlers.start_command))
        application.add_handler(CommandHandler("help", base_handlers.help_command))
        
        # Register file handlers
        application.add_handler(MessageHandler(
            filters.Document.ALL | filters.PHOTO, 
            file_handlers.handle_file_upload
        ))
        application.add_handler(CommandHandler("tag", file_handlers.tag_command))
        application.add_handler(CallbackQueryHandler(
            file_handlers.handle_tag_callback, 
            pattern="^(add_tags|ai_tag|skip_tag|confirm_ai_tag):"
        ))
        
        # Register search handlers
        application.add_handler(CommandHandler("search", search_handlers.search_command))
        application.add_handler(CallbackQueryHandler(
            search_handlers.handle_search_callback,
            pattern="^(file|search_page):"
        ))
        
        # Register AI handlers
        application.add_handler(CommandHandler("summary", ai_handlers.summary_command))
        application.add_handler(CommandHandler("explain", ai_handlers.explain_command))
        application.add_handler(CommandHandler("quiz", ai_handlers.quiz_command))
        
        # Register admin handlers
        application.add_handler(CommandHandler("admin", admin_handlers.admin_panel))
        application.add_handler(CommandHandler("global_admin", admin_handlers.global_admin_panel))
        application.add_handler(CallbackQueryHandler(
            admin_handlers.handle_admin_callback,
            pattern="^(admin|global_admin):"
        ))
        
        # Register ForceReply handlers for multi-step inputs
        application.add_handler(MessageHandler(
            filters.REPLY & filters.TEXT,
            file_handlers.handle_tag_reply
        ))
        
        # Register broadcast message handler
        application.add_handler(MessageHandler(
            filters.TEXT & filters.ChatType.PRIVATE,
            admin_handlers.handle_broadcast_reply
        ))
        
        # Register error handler
        application.add_error_handler(error_handler)
        
        # Schedule cleanup job (every 30 minutes)
        job_queue = application.job_queue
        job_queue.run_repeating(
            cleanup_expired_sessions,
            interval=timedelta(minutes=30),
            first=timedelta(seconds=10)
        )
        
        # Start the bot
        logger.info("Starting CollaLearn bot...")
        application.run_polling(allowed_updates=Update.ALL_TYPES)
        
    except Exception as e:
        logger.critical(f"Failed to start bot: {e}", exc_info=True)
        raise


if __name__ == '__main__':
    main()