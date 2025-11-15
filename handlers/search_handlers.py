"""
Search handlers for CollaLearn bot.
Handles file search and result retrieval.
"""

import logging
import uuid
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from telegram.constants import ParseMode
from telegram.error import TelegramError

from config import config
from db import Database
from utils.validator import is_admin

logger = logging.getLogger(__name__)


def escape_html(text: str) -> str:
    """
    Escape HTML special characters.
    
    Args:
        text: Text to escape
        
    Returns:
        Escaped text safe for HTML
    """
    if not text:
        return ""
    
    return text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')


async def search_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle /search command.
    Search for files in the current group and display results as buttons.
    
    Args:
        update: Telegram update object
        context: Callback context
    """
    try:
        message = update.message
        chat = update.effective_chat
        user = update.effective_user
        
        # Only works in groups
        if chat.type not in ["group", "supergroup"]:
            await message.reply_text(
                "🔍 Search only works in study room groups!"
            )
            return
        
        # Check for search query
        if not context.args:
            await message.reply_text(
                "❌ <b>Usage:</b> <code>/search &lt;query&gt;</code>\n\n"
                "<b>Examples:</b>\n"
                "• <code>/search operating systems</code>\n"
                "• <code>/search deadlock</code>\n"
                "• <code>/search #unit2</code>",
                parse_mode=ParseMode.HTML
            )
            return
        
        query = " ".join(context.args)
        
        db = Database()
        
        # Get group settings
        group = db.get_group(chat.id)
        if not group:
            await message.reply_text("⚠️ Group not registered. Use /start first.")
            return
        
        settings = group.get("settings", {})
        max_results = settings.get("max_search_results", config.MAX_SEARCH_RESULTS_DEFAULT)
        
        # Search files
        results = db.search_files(chat.id, query, limit=max_results)
        
        if not results:
            await message.reply_text(
                f"🔍 <b>No results found for:</b> <code>{escape_html(query)}</code>\n\n"
                "💡 <b>Tips:</b>\n"
                "• Try different keywords\n"
                "• Check your spelling\n"
                "• Use tags if you know them",
                parse_mode=ParseMode.HTML
            )
            return
        
        # Create search session
        session_id = str(uuid.uuid4())
        file_ids = [str(file["_id"]) for file in results]
        
        db.create_search_session(
            session_id=session_id,
            requester_id=user.id,
            group_id=chat.id,
            results=file_ids
        )
        
        # Build inline keyboard with file buttons
        keyboard = []
        for i, file in enumerate(results[:10]):  # Limit to 10 for display
            file_name = file.get("file_name", "Unnamed")
            # Truncate long names
            display_name = file_name[:35] + "..." if len(file_name) > 35 else file_name
            
            # Add tags preview
            tags = file.get("tags", [])
            if tags:
                tag_preview = f" [{', '.join(['#' + t for t in tags[:2]])}]"
                if len(tags) > 2:
                    tag_preview += "..."
                display_name += tag_preview
            
            button_text = f"📄 {display_name}"
            callback_data = f"file:{session_id}:{i}"
            
            keyboard.append([InlineKeyboardButton(button_text, callback_data=callback_data)])
        
        # Add pagination if more results
        if len(results) > 10:
            keyboard.append([
                InlineKeyboardButton(
                    f"➡️ More ({len(results) - 10} files)",
                    callback_data=f"search_page:{session_id}:1"
                )
            ])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        response = (
            f"🔍 <b>Search Results for:</b> <code>{escape_html(query)}</code>\n\n"
            f"📊 Found <b>{len(results)}</b> file(s)\n"
            f"👤 Results visible only to you\n\n"
            f"👇 Click a file to view it:"
        )
        
        await message.reply_text(
            response,
            parse_mode=ParseMode.HTML,
            reply_markup=reply_markup
        )
        
        logger.info(f"Search '{query}' by user {user.id} in group {chat.id}: {len(results)} results")
        
    except Exception as e:
        logger.error(f"Error in search_command: {e}", exc_info=True)
        await message.reply_text("⚠️ An error occurred during search.")


async def handle_search_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle inline button callbacks for search results.
    Verify user authorization and send files.
    
    Args:
        update: Telegram update object
        context: Callback context
    """
    try:
        query = update.callback_query
        user = update.effective_user
        chat = update.effective_chat
        
        data_parts = query.data.split(":")
        
        if len(data_parts) < 3:
            await query.answer("⚠️ Invalid callback data.", show_alert=True)
            return
        
        action = data_parts[0]
        session_id = data_parts[1]
        
        db = Database()
        
        # Get search session
        session = db.get_search_session(session_id)
        
        if not session:
            await query.answer(
                "⚠️ Search session expired. Please search again.",
                show_alert=True
            )
            return
        
        # Verify user authorization
        if session["requester_id"] != user.id:
            await query.answer(
                "🔒 Only the user who ran the search can access these results.",
                show_alert=True
            )
            return
        
        if action == "file":
            # Send specific file
            file_index = int(data_parts[2])
            
            if file_index >= len(session["results"]):
                await query.answer("⚠️ File not found.", show_alert=True)
                return
            
            file_id_str = session["results"][file_index]
            file_doc = db.get_file_by_id(file_id_str)
            
            if not file_doc or file_doc.get("deleted", False):
                await query.answer("⚠️ File no longer available.", show_alert=True)
                return
            
            # Send file
            try:
                await query.answer("📤 Sending file...")
                
                # Escape HTML entities in caption
                file_name = escape_html(file_doc['file_name'])
                uploader = escape_html(file_doc['uploader_username'])
                
                caption = f"📄 <b>{file_name}</b>\n"
                
                if file_doc.get("tags"):
                    tags = ', '.join(['#' + escape_html(t) for t in file_doc['tags']])
                    caption += f"🏷 {tags}\n"
                
                caption += f"\n👤 Uploaded by: @{uploader}"
                
                # Send based on file type
                if file_doc["mime_type"].startswith("image/"):
                    await context.bot.send_photo(
                        chat_id=chat.id,
                        photo=file_doc["file_id"],
                        caption=caption,
                        parse_mode=ParseMode.HTML
                    )
                else:
                    await context.bot.send_document(
                        chat_id=chat.id,
                        document=file_doc["file_id"],
                        caption=caption,
                        parse_mode=ParseMode.HTML
                    )
                
                logger.info(f"File {file_doc['file_name']} sent to user {user.id} in group {chat.id}")
                
            except TelegramError as e:
                logger.error(f"Error sending file: {e}")
                await query.answer("⚠️ Failed to send file.", show_alert=True)
        
        elif action == "search_page":
            # Handle pagination (simplified version)
            page = int(data_parts[2])
            start_idx = page * 10
            
            results = session["results"][start_idx:start_idx + 10]
            
            if not results:
                await query.answer("No more results.", show_alert=True)
                return
            
            # Build new keyboard
            keyboard = []
            for i, file_id_str in enumerate(results):
                file_doc = db.get_file_by_id(file_id_str)
                if file_doc and not file_doc.get("deleted", False):
                    file_name = file_doc.get("file_name", "Unnamed")[:35]
                    keyboard.append([
                        InlineKeyboardButton(
                            f"📄 {file_name}",
                            callback_data=f"file:{session_id}:{start_idx + i}"
                        )
                    ])
            
            # Navigation buttons
            nav_buttons = []
            if page > 0:
                nav_buttons.append(
                    InlineKeyboardButton("⬅️ Previous", callback_data=f"search_page:{session_id}:{page-1}")
                )
            if start_idx + 10 < len(session["results"]):
                nav_buttons.append(
                    InlineKeyboardButton("Next ➡️", callback_data=f"search_page:{session_id}:{page+1}")
                )
            
            if nav_buttons:
                keyboard.append(nav_buttons)
            
            await query.edit_message_reply_markup(reply_markup=InlineKeyboardMarkup(keyboard))
            await query.answer()
        
    except Exception as e:
        logger.error(f"Error in handle_search_callback: {e}", exc_info=True)
        try:
            await query.answer("⚠️ An error occurred.", show_alert=True)
        except:
            pass