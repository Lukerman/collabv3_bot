"""
File handlers for CollaLearn bot.
Handles file uploads, tagging, and tag callbacks.
"""

import logging
import uuid
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ForceReply
from telegram.ext import ContextTypes
from telegram.constants import ParseMode

from config import config
from db import Database
from ai_client import ai_client
from utils.text_extract import extract_text_from_file
from utils.validator import validate_file, is_admin
from utils.parser import parse_hashtags

logger = logging.getLogger(__name__)


async def handle_file_upload(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle file uploads (documents and photos).
    Store file metadata and offer tagging options.
    
    Args:
        update: Telegram update object
        context: Callback context
    """
    try:
        user = update.effective_user
        chat = update.effective_chat
        message = update.message
        
        # Only process in groups
        if chat.type not in ["group", "supergroup"]:
            await message.reply_text(
                "📚 Please use me in a group to upload study materials!"
            )
            return
        
        db = Database()
        
        # Register/update user and group
        db.upsert_user(user.id, user.username, user.first_name, chat.id)
        db.upsert_group(chat.id, chat.title)
        
        # Get group settings
        group = db.get_group(chat.id)
        if not group:
            await message.reply_text("⚠️ Group not registered. Please use /start first.")
            return
        
        settings = group.get("settings", {})
        
        # Check if admin-only indexing is enabled
        if settings.get("admin_only_indexing", False):
            if not await is_admin(user.id, chat.id, context):
                await message.reply_text(
                    "🔒 Only admins can upload files in this group."
                )
                return
        
        # Check if user is blocked
        if user.id in settings.get("blocked_users", []):
            await message.reply_text(
                "⛔ You are blocked from uploading files in this group."
            )
            return
        
        # Get file object
        file_obj = None
        file_name = "Unnamed"
        mime_type = None
        
        if message.document:
            file_obj = message.document
            file_name = file_obj.file_name or "document"
            mime_type = file_obj.mime_type
        elif message.photo:
            file_obj = message.photo[-1]  # Get highest resolution
            file_name = f"photo_{file_obj.file_unique_id}.jpg"
            mime_type = "image/jpeg"
        
        if not file_obj:
            return
        
        # Validate file
        validation_result = validate_file(file_obj, mime_type)
        if not validation_result["valid"]:
            await message.reply_text(f"⚠️ {validation_result['error']}")
            return
        
        # Extract hashtags from caption
        caption = message.caption or ""
        tags = parse_hashtags(caption)
        
        # Store file metadata
        file_data = {
            "file_id": file_obj.file_id,
            "file_unique_id": file_obj.file_unique_id,
            "file_name": file_name,
            "mime_type": mime_type,
            "caption": caption,
            "tags": tags,
            "ai_tags": [],
            "uploader_id": user.id,
            "uploader_username": user.username or user.first_name,
            "group_id": chat.id,
            "message_id": message.message_id
        }
        
        file_id = db.insert_file(file_data)
        
        if not file_id:
            await message.reply_text("⚠️ Failed to save file. Please try again.")
            return
        
        # Build response
        response = f"✅ **File Uploaded Successfully!**\n\n"
        response += f"📄 **Name:** `{file_name}`\n"
        
        if tags:
            response += f"🏷 **Tags:** {', '.join(['#' + tag for tag in tags])}\n"
        
        response += f"\n💡 **What's next?**"
        
        # Build inline keyboard for tagging options
        keyboard = []
        
        if not tags or len(tags) < 3:
            keyboard.append([
                InlineKeyboardButton("➕ Add Tags", callback_data=f"add_tags:{file_id}")
            ])
        
        if settings.get("auto_tag_enabled", True) and settings.get("ai_enabled", True):
            keyboard.append([
                InlineKeyboardButton("🤖 AI Auto-Tag", callback_data=f"ai_tag:{file_id}")
            ])
        
        keyboard.append([
            InlineKeyboardButton("✔️ Done", callback_data=f"skip_tag:{file_id}")
        ])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await message.reply_text(
            response,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=reply_markup
        )
        
        logger.info(f"File {file_name} uploaded by {user.id} in group {chat.id}")
        
    except Exception as e:
        logger.error(f"Error in handle_file_upload: {e}", exc_info=True)
        await update.message.reply_text(
            "⚠️ An error occurred while processing your file."
        )


async def handle_tag_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle inline button callbacks for tagging operations.
    
    Args:
        update: Telegram update object
        context: Callback context
    """
    try:
        query = update.callback_query
        await query.answer()
        
        user = update.effective_user
        data_parts = query.data.split(":", 1)
        
        if len(data_parts) < 2:
            await query.edit_message_text(
                "⚠️ Invalid callback data.",
                reply_markup=None
            )
            return
        
        action, file_id = data_parts
        
        db = Database()
        
        if action == "add_tags":
            # Prompt user to enter tags
            await query.edit_message_text(
                "📝 **Add Tags**\n\n"
                "Reply to this message with your tags separated by spaces or commas.\n\n"
                "Example: `operating-systems deadlock unit2`",
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=None  # Remove inline keyboard
            )
            
            # Store file_id in context for later
            context.user_data[f"add_tags_{query.message.message_id}"] = file_id
            
        elif action == "ai_tag":
            # Generate AI tags
            await query.edit_message_text(
                "🤖 Generating AI tags...\n\n"
                "⏳ This may take a few seconds.",
                reply_markup=None  # Remove inline keyboard
            )
            
            # Get file
            file_doc = db.get_file_by_id(file_id)
            if not file_doc:
                await query.edit_message_text(
                    "⚠️ File not found.",
                    reply_markup=None
                )
                return
            
            # Download and extract text
            try:
                file_obj = await context.bot.get_file(file_doc["file_id"])
                file_bytes = await file_obj.download_as_bytearray()
                
                text = await extract_text_from_file(
                    file_bytes,
                    file_doc["file_name"],
                    file_doc["mime_type"]
                )
                
                if not text or len(text.strip()) < 50:
                    await query.edit_message_text(
                        "⚠️ Could not extract enough text from file for AI tagging.\n"
                        "Please add tags manually.",
                        reply_markup=None
                    )
                    return
                
                # Get AI suggestions
                suggested_tags = await ai_client.suggest_tags(text, file_doc["file_name"])
                
                if not suggested_tags:
                    await query.edit_message_text(
                        "⚠️ AI tagging failed. Please try again or add tags manually.",
                        reply_markup=None
                    )
                    return
                
                # Show suggestions to user
                tags_text = ", ".join([f"#{tag}" for tag in suggested_tags])
                
                keyboard = [
                    [InlineKeyboardButton("✅ Accept These Tags", callback_data=f"confirm_ai_tag:{file_id}:{','.join(suggested_tags)}")],
                    [InlineKeyboardButton("✏️ Edit Manually", callback_data=f"add_tags:{file_id}")],
                    [InlineKeyboardButton("❌ Cancel", callback_data=f"skip_tag:{file_id}")]
                ]
                
                await query.edit_message_text(
                    f"🤖 **AI Suggested Tags:**\n\n"
                    f"{tags_text}\n\n"
                    f"Accept these tags or edit manually?",
                    parse_mode=ParseMode.MARKDOWN,
                    reply_markup=InlineKeyboardMarkup(keyboard)
                )
                
            except Exception as e:
                logger.error(f"Error in AI tagging: {e}")
                await query.edit_message_text(
                    "⚠️ Failed to process file for AI tagging.",
                    reply_markup=None
                )
        
        elif action == "confirm_ai_tag":
            # Confirm and save AI tags
            parts = file_id.split(":", 1)
            if len(parts) < 2:
                await query.edit_message_text(
                    "⚠️ Invalid data.",
                    reply_markup=None
                )
                return
            
            actual_file_id = parts[0]
            tags_str = parts[1]
            ai_tags = [tag.strip() for tag in tags_str.split(",")]
            
            # Get existing tags
            file_doc = db.get_file_by_id(actual_file_id)
            if file_doc:
                existing_tags = file_doc.get("tags", [])
                # Merge and deduplicate
                all_tags = list(set(existing_tags + ai_tags))
                
                db.update_file_tags(actual_file_id, all_tags, ai_tags)
                
                tags_display = ", ".join([f"#{tag}" for tag in all_tags])
                await query.edit_message_text(
                    f"✅ **Tags Updated!**\n\n"
                    f"🏷 {tags_display}\n\n"
                    f"Your file is now searchable with these tags.",
                    parse_mode=ParseMode.MARKDOWN,
                    reply_markup=None
                )
            else:
                await query.edit_message_text(
                    "⚠️ File not found.",
                    reply_markup=None
                )
        
        elif action == "skip_tag":
            await query.edit_message_text(
                "✅ **File saved!**\n\n"
                "You can add tags later using `/tag` command by replying to the file.",
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=None  # Remove inline keyboard
            )
        
    except Exception as e:
        logger.error(f"Error in handle_tag_callback: {e}", exc_info=True)
        try:
            await query.edit_message_text(
                "⚠️ An error occurred.",
                reply_markup=None
            )
        except:
            pass


async def tag_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle /tag command to add tags to a file.
    Must be used as a reply to a file message.
    
    Args:
        update: Telegram update object
        context: Callback context
    """
    try:
        message = update.message
        chat = update.effective_chat
        user = update.effective_user
        
        # Must be in a group
        if chat.type not in ["group", "supergroup"]:
            await message.reply_text("This command only works in groups.")
            return
        
        # Must be a reply
        if not message.reply_to_message:
            await message.reply_text(
                "❌ Please reply to a file with `/tag <tags>`\n\n"
                "Example: `/tag operating-systems deadlock`",
                parse_mode=ParseMode.MARKDOWN
            )
            return
        
        # Get tags from command
        if not context.args:
            await message.reply_text(
                "❌ Please provide tags.\n\n"
                "Example: `/tag operating-systems deadlock unit2`",
                parse_mode=ParseMode.MARKDOWN
            )
            return
        
        # Parse tags
        tags_input = " ".join(context.args)
        tags = [tag.strip().lower().replace("#", "") for tag in tags_input.replace(",", " ").split()]
        tags = [tag for tag in tags if tag and len(tag) <= config.MAX_TAG_LENGTH]
        
        if not tags:
            await message.reply_text("❌ No valid tags provided.")
            return
        
        # Find file in database
        replied_msg = message.reply_to_message
        db = Database()
        
        # Search by message_id and group_id
        file_doc = db._db[config.FILES_COLLECTION].find_one({
            "group_id": chat.id,
            "message_id": replied_msg.message_id,
            "deleted": False
        })
        
        if not file_doc:
            await message.reply_text(
                "⚠️ This file is not in my database. "
                "It may have been uploaded before I was added to the group."
            )
            return
        
        # Update tags
        existing_tags = file_doc.get("tags", [])
        updated_tags = list(set(existing_tags + tags))[:config.MAX_TAGS_PER_FILE]
        
        db.update_file_tags(str(file_doc["_id"]), updated_tags)
        
        tags_display = ", ".join([f"#{tag}" for tag in updated_tags])
        await message.reply_text(
            f"✅ **Tags Updated!**\n\n"
            f"🏷 {tags_display}",
            parse_mode=ParseMode.MARKDOWN
        )
        
        logger.info(f"Tags updated for file in group {chat.id} by user {user.id}")
        
    except Exception as e:
        logger.error(f"Error in tag_command: {e}", exc_info=True)
        await message.reply_text("⚠️ An error occurred while adding tags.")


async def handle_tag_reply(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle replies to ForceReply messages for tag input.
    
    Args:
        update: Telegram update object
        context: Callback context
    """
    try:
        message = update.message
        
        if not message.reply_to_message:
            return
        
        # Check if this is a response to our tag prompt
        replied_msg_id = message.reply_to_message.message_id
        file_id = context.user_data.get(f"add_tags_{replied_msg_id}")
        
        if not file_id:
            return
        
        # Parse tags from user input
        tags_input = message.text
        tags = [tag.strip().lower().replace("#", "") for tag in tags_input.replace(",", " ").split()]
        tags = [tag for tag in tags if tag and len(tag) <= config.MAX_TAG_LENGTH]
        
        if not tags:
            await message.reply_text("❌ No valid tags provided. Please try again.")
            return
        
        # Update file tags
        db = Database()
        file_doc = db.get_file_by_id(file_id)
        
        if not file_doc:
            await message.reply_text("⚠️ File not found.")
            return
        
        existing_tags = file_doc.get("tags", [])
        updated_tags = list(set(existing_tags + tags))[:config.MAX_TAGS_PER_FILE]
        
        db.update_file_tags(file_id, updated_tags)
        
        tags_display = ", ".join([f"#{tag}" for tag in updated_tags])
        await message.reply_text(
            f"✅ **Tags Added!**\n\n"
            f"🏷 {tags_display}\n\n"
            f"Your file is now searchable with these tags.",
            parse_mode=ParseMode.MARKDOWN
        )
        
        # Clean up context
        del context.user_data[f"add_tags_{replied_msg_id}"]
        
    except Exception as e:
        logger.error(f"Error in handle_tag_reply: {e}", exc_info=True)