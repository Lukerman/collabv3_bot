"""
Validation utilities for CollaLearn bot.
Validates files, permissions, and settings.
"""

import logging
from typing import Dict, Any, Optional
from telegram.ext import ContextTypes

from config import config

logger = logging.getLogger(__name__)


def validate_file(file_obj: Any, mime_type: str) -> Dict[str, Any]:
    """
    Validate uploaded file.
    
    Args:
        file_obj: Telegram file object
        mime_type: MIME type of the file
    
    Returns:
        Dictionary with 'valid' boolean and 'error' message
    """
    # Check MIME type
    if mime_type not in config.SUPPORTED_MIME_TYPES:
        return {
            "valid": False,
            "error": f"Unsupported file type. Supported types: PDF, DOCX, PPTX, images, text files."
        }
    
    # Check file size
    file_size = getattr(file_obj, 'file_size', 0)
    max_size_bytes = config.MAX_FILE_SIZE_MB * 1024 * 1024
    
    if file_size > max_size_bytes:
        return {
            "valid": False,
            "error": f"File too large. Maximum size: {config.MAX_FILE_SIZE_MB}MB"
        }
    
    return {"valid": True, "error": None}


async def is_admin(user_id: int, chat_id: int, context: ContextTypes.DEFAULT_TYPE) -> bool:
    """
    Check if user is an administrator in the group.
    
    Args:
        user_id: User ID to check
        chat_id: Group chat ID
        context: Bot context
    
    Returns:
        True if user is admin, False otherwise
    """
    try:
        chat_member = await context.bot.get_chat_member(chat_id, user_id)
        return chat_member.status in ["creator", "administrator"]
    except Exception as e:
        logger.error(f"Error checking admin status: {e}")
        return False


def is_global_admin(user_id: int) -> bool:
    """
    Check if user is a global bot administrator.
    
    Args:
        user_id: User ID to check
    
    Returns:
        True if global admin, False otherwise
    """
    return user_id in config.GLOBAL_ADMIN_IDS


def validate_ai_enabled(settings: Dict, feature_key: str) -> bool:
    """
    Check if AI feature is enabled for a group.
    
    Args:
        settings: Group settings dictionary
        feature_key: Specific AI feature key to check
    
    Returns:
        True if enabled, False otherwise
    """
    # Check if AI is globally enabled
    if not settings.get("ai_enabled", True):
        return False
    
    # Check specific feature
    return settings.get(feature_key, True)


def validate_tags(tags: list) -> Dict[str, Any]:
    """
    Validate a list of tags.
    
    Args:
        tags: List of tag strings
    
    Returns:
        Dictionary with 'valid' boolean, 'tags' list, and 'error' message
    """
    if not tags:
        return {"valid": False, "tags": [], "error": "No tags provided"}
    
    if len(tags) > config.MAX_TAGS_PER_FILE:
        return {
            "valid": False,
            "tags": [],
            "error": f"Too many tags. Maximum: {config.MAX_TAGS_PER_FILE}"
        }
    
    # Validate individual tags
    validated_tags = []
    for tag in tags:
        tag = tag.strip().lower().replace("#", "")
        
        if not tag:
            continue
        
        if len(tag) > config.MAX_TAG_LENGTH:
            continue
        
        # Remove special characters except hyphen and underscore
        tag = "".join(c for c in tag if c.isalnum() or c in ["-", "_"])
        
        if tag and tag not in validated_tags:
            validated_tags.append(tag)
    
    if not validated_tags:
        return {"valid": False, "tags": [], "error": "No valid tags"}
    
    return {"valid": True, "tags": validated_tags, "error": None}


def validate_search_query(query: str) -> Dict[str, Any]:
    """
    Validate search query.
    
    Args:
        query: Search query string
    
    Returns:
        Dictionary with 'valid' boolean and 'error' message
    """
    if not query or not query.strip():
        return {"valid": False, "error": "Empty search query"}
    
    if len(query) < 2:
        return {"valid": False, "error": "Query too short. Minimum 2 characters"}
    
    if len(query) > 200:
        return {"valid": False, "error": "Query too long. Maximum 200 characters"}
    
    return {"valid": True, "error": None}