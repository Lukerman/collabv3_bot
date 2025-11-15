"""
Admin handlers for CollaLearn bot.
Handles both group admin panel and global bot admin panel.
"""

import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from telegram.constants import ParseMode
from telegram.helpers import escape_markdown

from config import config
from db import Database
from utils.validator import is_admin, is_global_admin

logger = logging.getLogger(__name__)


def escape_md(text: str) -> str:
    """
    Escape markdown special characters for MarkdownV2.
    
    Args:
        text: Text to escape
        
    Returns:
        Escaped text safe for Markdown
    """
    if not text:
        return ""
    
    # For MarkdownV2, escape these characters: _*[]()~`>#+-=|{}.!
    special_chars = ['_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']
    
    for char in special_chars:
        text = text.replace(char, f'\\{char}')
    
    return text


async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle /admin command.
    Display group admin panel with management options.
    
    Args:
        update: Telegram update object
        context: Callback context
    """
    try:
        message = update.message
        chat = update.effective_chat
        user = update.effective_user
        
        # Only in groups
        if chat.type not in ["group", "supergroup"]:
            await message.reply_text("Admin panel only works in groups.")
            return
        
        # Check if user is admin
        if not await is_admin(user.id, chat.id, context):
            await message.reply_text("🔒 This command is only for group administrators.")
            return
        
        # Build admin panel
        keyboard = [
            [InlineKeyboardButton("⚙️ Group Settings", callback_data="admin:settings")],
            [InlineKeyboardButton("📚 File & Tag Management", callback_data="admin:files")],
            [InlineKeyboardButton("🤖 AI Controls", callback_data="admin:ai")],
            [InlineKeyboardButton("🧍 User Management", callback_data="admin:users")],
            [InlineKeyboardButton("📊 Statistics", callback_data="admin:stats")],
            [InlineKeyboardButton("❌ Close", callback_data="admin:close")]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        # Use HTML instead of Markdown to avoid parsing issues
        response = (
            f"👥 <b>Group Admin Panel</b>\n\n"
            f"🏫 Group: {chat.title}\n"
            f"👤 Admin: {user.mention_html()}\n\n"
            f"Select an option below:"
        )
        
        await message.reply_text(
            response,
            parse_mode=ParseMode.HTML,
            reply_markup=reply_markup
        )
        
        logger.info(f"Admin panel opened by {user.id} in group {chat.id}")
        
    except Exception as e:
        logger.error(f"Error in admin_panel: {e}", exc_info=True)
        await message.reply_text("⚠️ An error occurred.")


async def global_admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle /global_admin command.
    Display global bot admin panel (only in private chat).
    
    Args:
        update: Telegram update object
        context: Callback context
    """
    try:
        message = update.message
        chat = update.effective_chat
        user = update.effective_user
        
        # Only in private chat
        if chat.type != "private":
            await message.reply_text("Global admin panel only works in private chat.")
            return
        
        # Check if user is global admin
        if not is_global_admin(user.id):
            await message.reply_text("🔒 You don't have access to global admin panel.")
            return
        
        # Build global admin panel
        keyboard = [
            [InlineKeyboardButton("🌍 View All Groups", callback_data="global_admin:groups")],
            [InlineKeyboardButton("📊 Global Statistics", callback_data="global_admin:stats")],
            [InlineKeyboardButton("🤖 Global AI Settings", callback_data="global_admin:ai")],
            [InlineKeyboardButton("📤 Broadcast Message", callback_data="global_admin:broadcast")],
            [InlineKeyboardButton("🗑 Manage Groups", callback_data="global_admin:manage")],
            [InlineKeyboardButton("❌ Close", callback_data="global_admin:close")]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        response = (
            f"🌟 <b>Global Admin Panel</b>\n\n"
            f"👤 Admin: {user.mention_html()}\n"
            f"🤖 Bot: CollaLearn\n\n"
            f"Select an option below:"
        )
        
        await message.reply_text(
            response,
            parse_mode=ParseMode.HTML,
            reply_markup=reply_markup
        )
        
        logger.info(f"Global admin panel opened by {user.id}")
        
    except Exception as e:
        logger.error(f"Error in global_admin_panel: {e}", exc_info=True)
        await message.reply_text("⚠️ An error occurred.")


async def handle_admin_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle all admin panel callback queries.
    Routes to appropriate admin action handlers.
    
    Args:
        update: Telegram update object
        context: Callback context
    """
    try:
        query = update.callback_query
        await query.answer()
        
        user = update.effective_user
        chat = update.effective_chat
        data = query.data
        
        # Parse callback data
        parts = data.split(":")
        if len(parts) < 2:
            await query.edit_message_text("⚠️ Invalid callback data.", reply_markup=None)
            return
        
        panel_type = parts[0]  # "admin" or "global_admin"
        action = parts[1]
        
        # Route to appropriate handler
        if panel_type == "admin":
            await handle_group_admin_action(query, action, chat, user, context)
        elif panel_type == "global_admin":
            await handle_global_admin_action(query, action, user, context)
        
    except Exception as e:
        logger.error(f"Error in handle_admin_callback: {e}", exc_info=True)
        try:
            await query.edit_message_text("⚠️ An error occurred.", reply_markup=None)
        except:
            pass


async def handle_group_admin_action(query, action: str, chat, user, context) -> None:
    """Handle group admin panel actions."""
    db = Database()
    
    if action == "close":
        await query.edit_message_text("✅ Admin panel closed.", reply_markup=None)
        return
    
    elif action == "settings":
        # Show group settings
        group = db.get_group(chat.id)
        if not group:
            await query.edit_message_text("⚠️ Group not found.", reply_markup=None)
            return
        
        settings = group.get("settings", {})
        
        keyboard = [
            [InlineKeyboardButton(
                f"{'✅' if settings.get('ai_enabled') else '❌'} AI Features",
                callback_data="admin:toggle:ai_enabled"
            )],
            [InlineKeyboardButton(
                f"{'✅' if settings.get('auto_tag_enabled') else '❌'} Auto-Tagging",
                callback_data="admin:toggle:auto_tag_enabled"
            )],
            [InlineKeyboardButton(
                f"{'✅' if settings.get('admin_only_indexing') else '❌'} Admin-Only Upload",
                callback_data="admin:toggle:admin_only_indexing"
            )],
            [InlineKeyboardButton(
                f"🔢 Max Search Results: {settings.get('max_search_results', 10)}",
                callback_data="admin:adjust:max_search_results"
            )],
            [InlineKeyboardButton("◀️ Back", callback_data="admin:back")]
        ]
        
        await query.edit_message_text(
            "⚙️ <b>Group Settings</b>\n\n"
            "Toggle features or adjust limits:",
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    
    elif action == "files":
        # Show recent files - USE HTML TO AVOID MARKDOWN ISSUES
        files = db.get_latest_files(chat.id, limit=5)
        
        response = "📚 <b>Recent Files</b>\n\n"
        
        if not files:
            response += "No files uploaded yet."
        else:
            for i, file in enumerate(files, 1):
                # Escape HTML special characters
                file_name = file['file_name'].replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
                response += f"{i}. {file_name}\n"
                
                if file.get('tags'):
                    tags = ', '.join(['#' + t for t in file['tags'][:3]])
                    response += f"   🏷 {tags}\n"
                
                uploader = file['uploader_username'].replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
                response += f"   👤 @{uploader}\n\n"
        
        keyboard = [
            [InlineKeyboardButton("🔄 Refresh", callback_data="admin:files")],
            [InlineKeyboardButton("◀️ Back", callback_data="admin:back")]
        ]
        
        await query.edit_message_text(
            response,
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    
    elif action == "ai":
        # AI controls
        group = db.get_group(chat.id)
        settings = group.get("settings", {})
        
        keyboard = [
            [InlineKeyboardButton(
                f"{'✅' if settings.get('summarization_enabled') else '❌'} Summarization",
                callback_data="admin:toggle:summarization_enabled"
            )],
            [InlineKeyboardButton(
                f"{'✅' if settings.get('explanation_enabled') else '❌'} Explanations",
                callback_data="admin:toggle:explanation_enabled"
            )],
            [InlineKeyboardButton(
                f"{'✅' if settings.get('quiz_enabled') else '❌'} Quiz Generation",
                callback_data="admin:toggle:quiz_enabled"
            )],
            [InlineKeyboardButton("◀️ Back", callback_data="admin:back")]
        ]
        
        await query.edit_message_text(
            "🤖 <b>AI Controls</b>\n\n"
            "Enable or disable AI features:",
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    
    elif action == "users":
        # User management
        keyboard = [
            [InlineKeyboardButton("📋 View Top Contributors", callback_data="admin:top_users")],
            [InlineKeyboardButton("🚫 Blocked Users List", callback_data="admin:blocked_users")],
            [InlineKeyboardButton("◀️ Back", callback_data="admin:back")]
        ]
        
        await query.edit_message_text(
            "🧍 <b>User Management</b>\n\n"
            "Select an option:",
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    
    elif action == "stats":
        # Show group statistics
        stats = db.get_group_stats(chat.id)
        
        response = "📊 <b>Group Statistics</b>\n\n"
        response += f"📚 Total Files: <b>{stats.get('total_files', 0)}</b>\n"
        response += f"🤖 AI Requests: <b>{stats.get('total_ai_requests', 0)}</b>\n\n"
        
        if stats.get('top_uploaders'):
            response += "👥 <b>Top Contributors:</b>\n"
            for uploader in stats['top_uploaders'][:3]:
                username = uploader['_id'].replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
                response += f"• @{username}: {uploader['count']} files\n"
        
        if stats.get('tag_distribution'):
            response += "\n🏷 <b>Popular Tags:</b>\n"
            for tag, count in list(stats['tag_distribution'].items())[:5]:
                response += f"• #{tag}: {count}\n"
        
        keyboard = [[InlineKeyboardButton("◀️ Back", callback_data="admin:back")]]
        
        await query.edit_message_text(
            response,
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    
    elif action == "toggle":
        # Toggle a setting
        if len(query.data.split(":")) < 3:
            return
        
        setting_key = query.data.split(":")[2]
        group = db.get_group(chat.id)
        settings = group.get("settings", {})
        
        # Toggle the setting
        settings[setting_key] = not settings.get(setting_key, False)
        db.update_group_settings(chat.id, settings)
        
        await query.answer("✅ Setting updated!")
        
        # Return to appropriate page
        if "ai" in query.data or setting_key in ["summarization_enabled", "explanation_enabled", "quiz_enabled"]:
            await handle_group_admin_action(query, "ai", chat, user, context)
        else:
            await handle_group_admin_action(query, "settings", chat, user, context)
    
    elif action == "top_users":
        # Show top contributors
        stats = db.get_group_stats(chat.id)
        
        response = "👥 <b>Top Contributors</b>\n\n"
        
        if stats.get('top_uploaders'):
            for i, uploader in enumerate(stats['top_uploaders'][:10], 1):
                username = uploader['_id'].replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
                response += f"{i}. @{username}: <b>{uploader['count']}</b> files\n"
        else:
            response += "No contributors yet."
        
        keyboard = [[InlineKeyboardButton("◀️ Back", callback_data="admin:users")]]
        
        await query.edit_message_text(
            response,
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    
    elif action == "blocked_users":
        # Show blocked users
        group = db.get_group(chat.id)
        blocked = group.get("settings", {}).get("blocked_users", [])
        
        response = "🚫 <b>Blocked Users</b>\n\n"
        
        if blocked:
            for user_id in blocked:
                response += f"• User ID: <code>{user_id}</code>\n"
        else:
            response += "No blocked users."
        
        keyboard = [[InlineKeyboardButton("◀️ Back", callback_data="admin:users")]]
        
        await query.edit_message_text(
            response,
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    
    elif action == "back":
        # Return to main admin panel
        keyboard = [
            [InlineKeyboardButton("⚙️ Group Settings", callback_data="admin:settings")],
            [InlineKeyboardButton("📚 File & Tag Management", callback_data="admin:files")],
            [InlineKeyboardButton("🤖 AI Controls", callback_data="admin:ai")],
            [InlineKeyboardButton("🧍 User Management", callback_data="admin:users")],
            [InlineKeyboardButton("📊 Statistics", callback_data="admin:stats")],
            [InlineKeyboardButton("❌ Close", callback_data="admin:close")]
        ]
        
        await query.edit_message_text(
            "👥 <b>Group Admin Panel</b>\n\n"
            "Select an option:",
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )


async def handle_global_admin_action(query, action: str, user, context) -> None:
    """Handle global admin panel actions."""
    db = Database()
    
    if action == "close":
        await query.edit_message_text("✅ Global admin panel closed.", reply_markup=None)
        return
    
    elif action == "stats":
        # Show global statistics
        stats = db.get_global_stats()
        
        response = "📊 <b>Global Bot Statistics</b>\n\n"
        response += f"👥 Total Groups: <b>{stats.get('total_groups', 0)}</b>\n"
        response += f"🧑‍🎓 Total Users: <b>{stats.get('total_users', 0)}</b>\n"
        response += f"📚 Total Files: <b>{stats.get('total_files', 0)}</b>\n"
        response += f"🤖 AI Requests: <b>{stats.get('total_ai_requests', 0)}</b>\n"
        
        keyboard = [[InlineKeyboardButton("◀️ Back", callback_data="global_admin:back")]]
        
        await query.edit_message_text(
            response,
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    
    elif action == "groups":
        # Show all groups
        groups = db.get_all_groups(limit=10)
        
        response = "🌍 <b>All Study Room Groups</b>\n\n"
        
        if not groups:
            response += "No groups registered yet."
        else:
            for i, group in enumerate(groups, 1):
                title = group['title'].replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
                response += f"{i}. <b>{title}</b>\n"
                response += f"   ID: <code>{group['chat_id']}</code>\n"
                response += f"   Files: {group.get('stats', {}).get('total_files', 0)}\n\n"
        
        keyboard = [[InlineKeyboardButton("◀️ Back", callback_data="global_admin:back")]]
        
        await query.edit_message_text(
            response,
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    
    elif action == "ai":
        # Global AI settings info
        response = (
            "🤖 <b>Global AI Settings</b>\n\n"
            "AI features are currently <b>ENABLED</b> globally.\n\n"
            "Individual groups can control their AI settings via group admin panel.\n\n"
            f"<b>Configuration:</b>\n"
            f"• API: Perplexity AI\n"
            f"• Model: {config.PERPLEXITY_MODEL}\n"
            f"• Temperature: {config.AI_TEMPERATURE}\n"
            f"• Max Tokens: {config.AI_MAX_TOKENS}"
        )
        
        keyboard = [[InlineKeyboardButton("◀️ Back", callback_data="global_admin:back")]]
        
        await query.edit_message_text(
            response,
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    
    elif action == "broadcast":
        # Broadcast message
        await query.edit_message_text(
            "📤 <b>Broadcast Message</b>\n\n"
            "This feature allows sending announcements to all groups.\n\n"
            "⚠️ <b>Coming Soon!</b>\n\n"
            "Implementation planned for future version.",
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("◀️ Back", callback_data="global_admin:back")
            ]])
        )
    
    elif action == "manage":
        # Manage groups
        await query.edit_message_text(
            "🗑 <b>Manage Groups</b>\n\n"
            "This feature allows:\n"
            "• Deleting groups from database\n"
            "• Resetting group settings\n"
            "• Viewing detailed group info\n\n"
            "⚠️ <b>Coming Soon!</b>\n\n"
            "Implementation planned for future version.",
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("◀️ Back", callback_data="global_admin:back")
            ]])
        )
    
    elif action == "back":
        # Return to main global admin panel
        keyboard = [
            [InlineKeyboardButton("🌍 View All Groups", callback_data="global_admin:groups")],
            [InlineKeyboardButton("📊 Global Statistics", callback_data="global_admin:stats")],
            [InlineKeyboardButton("🤖 Global AI Settings", callback_data="global_admin:ai")],
            [InlineKeyboardButton("📤 Broadcast Message", callback_data="global_admin:broadcast")],
            [InlineKeyboardButton("🗑 Manage Groups", callback_data="global_admin:manage")],
            [InlineKeyboardButton("❌ Close", callback_data="global_admin:close")]
        ]
        
        await query.edit_message_text(
            "🌟 <b>Global Admin Panel</b>\n\n"
            "Select an option:",
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )