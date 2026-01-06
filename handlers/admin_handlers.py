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
            [InlineKeyboardButton("📤 Broadcast", callback_data="global_admin:broadcast_menu")],
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


async def handle_broadcast_reply(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle replies for broadcast message input.
    
    Args:
        update: Telegram update object
        context: Callback context
    """
    try:
        message = update.message
        user = update.effective_user
        
        # Check if user is in broadcast mode
        broadcast_mode = context.user_data.get("broadcast_mode")
        if not broadcast_mode:
            return
        
        # Check if global admin
        if not is_global_admin(user.id):
            return
        
        broadcast_text = message.text
        if not broadcast_text:
            await message.reply_text("❌ Please provide a message to broadcast.")
            return
        
        # Clear broadcast mode
        context.user_data["broadcast_mode"] = False
        
        db = Database()
        success_count = 0
        fail_count = 0
        
        # Handle different broadcast modes
        if broadcast_mode in [True, "groups"]:
            # Broadcast to groups (legacy mode or groups only)
            groups = db.get_all_groups()
            
            if not groups:
                await message.reply_text("⚠️ No groups found to broadcast to.")
                return
            
            for group in groups:
                try:
                    await context.bot.send_message(
                        chat_id=group["chat_id"],
                        text=f"📢 <b>Announcement from Bot Admin</b>\n\n{broadcast_text}",
                        parse_mode=ParseMode.HTML
                    )
                    success_count += 1
                except Exception as e:
                    logger.error(f"Failed to broadcast to group {group['chat_id']}: {e}")
                    fail_count += 1
            
            target_type = "groups"
            
        elif broadcast_mode == "users":
            # Broadcast to users via PM
            users_collection = db._db[config.USERS_COLLECTION]
            users = list(users_collection.find({}, {"user_id": 1}))
            
            if not users:
                await message.reply_text("⚠️ No users found to broadcast to.")
                return
            
            for user_doc in users:
                try:
                    await context.bot.send_message(
                        chat_id=user_doc["user_id"],
                        text=f"📢 <b>Announcement from Bot Admin</b>\n\n{broadcast_text}",
                        parse_mode=ParseMode.HTML
                    )
                    success_count += 1
                except Exception as e:
                    logger.error(f"Failed to broadcast to user {user_doc['user_id']}: {e}")
                    fail_count += 1
            
            target_type = "users"
            
        elif broadcast_mode == "both":
            # Broadcast to both groups and users
            # First, broadcast to groups
            groups = db.get_all_groups()
            for group in groups:
                try:
                    await context.bot.send_message(
                        chat_id=group["chat_id"],
                        text=f"📢 <b>Announcement from Bot Admin</b>\n\n{broadcast_text}",
                        parse_mode=ParseMode.HTML
                    )
                    success_count += 1
                except Exception as e:
                    logger.error(f"Failed to broadcast to group {group['chat_id']}: {e}")
                    fail_count += 1
            
            # Then, broadcast to users
            users_collection = db._db[config.USERS_COLLECTION]
            users = list(users_collection.find({}, {"user_id": 1}))
            for user_doc in users:
                try:
                    await context.bot.send_message(
                        chat_id=user_doc["user_id"],
                        text=f"📢 <b>Announcement from Bot Admin</b>\n\n{broadcast_text}",
                        parse_mode=ParseMode.HTML
                    )
                    success_count += 1
                except Exception as e:
                    logger.error(f"Failed to broadcast to user {user_doc['user_id']}: {e}")
                    fail_count += 1
            
            target_type = "groups and users"
        
        # Report results
        response = (
            f"📤 <b>Broadcast Complete</b>\n\n"
            f"✅ Sent to: <b>{success_count}</b> {target_type}\n"
            f"❌ Failed: <b>{fail_count}</b> {target_type}\n\n"
            f"Message: {broadcast_text[:100]}{'...' if len(broadcast_text) > 100 else ''}"
        )
        
        await message.reply_text(response, parse_mode=ParseMode.HTML)
        logger.info(f"Broadcast completed by {user.id}: {success_count} success, {fail_count} failed to {target_type}")
        
    except Exception as e:
        logger.error(f"Error in handle_broadcast_reply: {e}", exc_info=True)
        await message.reply_text("⚠️ An error occurred while broadcasting.")


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
    
    elif action == "broadcast_menu":
        # Show broadcast options
        keyboard = [
            [InlineKeyboardButton("👥 Broadcast to Groups", callback_data="global_admin:broadcast_groups")],
            [InlineKeyboardButton("👤 Broadcast to Users (PM)", callback_data="global_admin:broadcast_users")],
            [InlineKeyboardButton("🌍 Broadcast to Both", callback_data="global_admin:broadcast_both")],
            [InlineKeyboardButton("◀️ Back", callback_data="global_admin:back")]
        ]
        
        await query.edit_message_text(
            "📤 <b>Broadcast Options</b>\n\n"
            "Choose who to send the announcement to:",
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    
    elif action == "broadcast_groups":
        # Broadcast to groups
        context.user_data["broadcast_mode"] = "groups"
        await query.edit_message_text(
            "📤 <b>Broadcast to Groups</b>\n\n"
            "Send the message you want to broadcast to all study groups.\n\n"
            "Type your message below:",
            parse_mode=ParseMode.HTML,
            reply_markup=None
        )
    
    elif action == "broadcast_users":
        # Broadcast to users (PM)
        context.user_data["broadcast_mode"] = "users"
        await query.edit_message_text(
            "📤 <b>Broadcast to Users</b>\n\n"
            "Send the message you want to broadcast to all users via private message.\n\n"
            "Type your message below:",
            parse_mode=ParseMode.HTML,
            reply_markup=None
        )
    
    elif action == "broadcast_both":
        # Broadcast to both groups and users
        context.user_data["broadcast_mode"] = "both"
        await query.edit_message_text(
            "📤 <b>Broadcast to Groups & Users</b>\n\n"
            "Send the message you want to broadcast to all groups and all users.\n\n"
            "Type your message below:",
            parse_mode=ParseMode.HTML,
            reply_markup=None
        )
    
    elif action == "broadcast":
        # Legacy broadcast (to groups)
        context.user_data["broadcast_mode"] = True
        await query.edit_message_text(
            "📤 <b>Broadcast Message</b>\n\n"
            "Send the message you want to broadcast to all groups.\n\n"
            "Type your message below:",
            parse_mode=ParseMode.HTML,
            reply_markup=None
        )
    
    elif action == "manage":
        # Manage groups - Show list of groups to manage
        groups = db.get_all_groups(limit=10)
        
        response = "🗑 <b>Manage Groups</b>\n\n"
        
        if not groups:
            response += "No groups registered yet."
            keyboard = [[InlineKeyboardButton("◀️ Back", callback_data="global_admin:back")]]
        else:
            response += "Select a group to manage:\n\n"
            keyboard = []
            
            for group in groups:
                title = group['title'].replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
                button_text = f"📁 {title[:30]}"
                keyboard.append([InlineKeyboardButton(
                    button_text,
                    callback_data=f"global_admin:manage_group:{group['chat_id']}"
                )])
            
            keyboard.append([InlineKeyboardButton("◀️ Back", callback_data="global_admin:back")])
        
        await query.edit_message_text(
            response,
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    
    elif action == "manage_group":
        # Show detailed info about specific group
        if len(query.data.split(":")) < 3:
            return
        
        chat_id = int(query.data.split(":")[2])
        group = db.get_group(chat_id)
        
        if not group:
            await query.edit_message_text(
                "⚠️ Group not found.",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("◀️ Back", callback_data="global_admin:manage")
                ]])
            )
            return
        
        title = group['title'].replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
        settings = group.get('settings', {})
        stats = group.get('stats', {})
        
        response = f"📊 <b>Group Details</b>\n\n"
        response += f"<b>Name:</b> {title}\n"
        response += f"<b>ID:</b> <code>{chat_id}</code>\n"
        response += f"<b>Created:</b> {group.get('created_at', 'N/A').strftime('%Y-%m-%d %H:%M') if group.get('created_at') else 'N/A'}\n\n"
        
        response += f"<b>📈 Statistics:</b>\n"
        response += f"• Files: {stats.get('total_files', 0)}\n"
        response += f"• AI Requests: {stats.get('total_ai_requests', 0)}\n\n"
        
        response += f"<b>⚙️ Settings:</b>\n"
        response += f"• AI Enabled: {'✅' if settings.get('ai_enabled') else '❌'}\n"
        response += f"• Auto-tagging: {'✅' if settings.get('auto_tag_enabled') else '❌'}\n"
        response += f"• Admin-only Upload: {'✅' if settings.get('admin_only_indexing') else '❌'}\n"
        response += f"• Max Search Results: {settings.get('max_search_results', 10)}\n"
        
        keyboard = [
            [InlineKeyboardButton("🔄 Reset Settings", callback_data=f"global_admin:reset_settings:{chat_id}")],
            [InlineKeyboardButton("🗑 Delete Group", callback_data=f"global_admin:confirm_delete:{chat_id}")],
            [InlineKeyboardButton("◀️ Back", callback_data="global_admin:manage")]
        ]
        
        await query.edit_message_text(
            response,
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    
    elif action == "reset_settings":
        # Reset group settings to default
        if len(query.data.split(":")) < 3:
            return
        
        chat_id = int(query.data.split(":")[2])
        group = db.get_group(chat_id)
        
        if not group:
            await query.answer("⚠️ Group not found!", show_alert=True)
            return
        
        # Reset to default settings
        success = db.update_group_settings(chat_id, config.DEFAULT_GROUP_SETTINGS.copy())
        
        if success:
            await query.answer("✅ Settings reset successfully!", show_alert=True)
            # Show updated group details
            # We need to reconstruct the action string manually
            query.data = f"global_admin:manage_group:{chat_id}"
            await handle_global_admin_action(query, "manage_group", user, context)
        else:
            await query.answer("❌ Failed to reset settings!", show_alert=True)
    
    elif action == "confirm_delete":
        # Confirm deletion
        if len(query.data.split(":")) < 3:
            return
        
        chat_id = int(query.data.split(":")[2])
        group = db.get_group(chat_id)
        
        if not group:
            await query.answer("⚠️ Group not found!", show_alert=True)
            return
        
        title = group['title'].replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
        stats = group.get('stats', {})
        
        response = f"⚠️ <b>Confirm Deletion</b>\n\n"
        response += f"Are you sure you want to delete this group?\n\n"
        response += f"<b>Group:</b> {title}\n"
        response += f"<b>ID:</b> <code>{chat_id}</code>\n\n"
        response += f"<b>This will permanently delete:</b>\n"
        response += f"• {stats.get('total_files', 0)} files\n"
        response += f"• All group settings\n"
        response += f"• All search sessions\n"
        response += f"• All AI logs\n\n"
        response += f"⚠️ <b>This action cannot be undone!</b>"
        
        keyboard = [
            [InlineKeyboardButton("✅ Yes, Delete", callback_data=f"global_admin:delete_confirmed:{chat_id}")],
            [InlineKeyboardButton("❌ Cancel", callback_data=f"global_admin:manage_group:{chat_id}")]
        ]
        
        await query.edit_message_text(
            response,
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    
    elif action == "delete_confirmed":
        # Execute deletion
        if len(query.data.split(":")) < 3:
            return
        
        chat_id = int(query.data.split(":")[2])
        group = db.get_group(chat_id)
        
        if not group:
            await query.answer("⚠️ Group not found!", show_alert=True)
            return
        
        title = group['title']
        success = db.delete_group(chat_id)
        
        if success:
            await query.answer(f"✅ Group '{title}' deleted successfully!", show_alert=True)
            logger.info(f"Group {chat_id} deleted by global admin {user.id}")
            
            # Return to manage groups list
            await handle_global_admin_action(query, "manage", user, context)
        else:
            await query.answer("❌ Failed to delete group!", show_alert=True)
    
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
