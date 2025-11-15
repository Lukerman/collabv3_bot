"""
Group model for CollaLearn bot.
Defines group data structure and helper functions.
"""

from datetime import datetime
from typing import Dict, Optional, List
from config import config


class GroupModel:
    """
    Group model for database operations.
    Represents a Telegram group (study room) in the system.
    """
    
    @staticmethod
    def create_group_document(chat_id: int, title: str) -> Dict:
        """
        Create a new group document structure.
        
        Args:
            chat_id: Telegram chat ID
            title: Group title
        
        Returns:
            Group document dictionary
        """
        return {
            "chat_id": chat_id,
            "title": title,
            "created_at": datetime.utcnow(),
            "last_seen_at": datetime.utcnow(),
            "settings": config.DEFAULT_GROUP_SETTINGS.copy(),
            "stats": {
                "total_files": 0,
                "total_ai_requests": 0
            }
        }
    
    @staticmethod
    def update_group_activity(group_doc: Dict) -> Dict:
        """
        Update group's last seen timestamp.
        
        Args:
            group_doc: Existing group document
        
        Returns:
            Updated group document
        """
        group_doc["last_seen_at"] = datetime.utcnow()
        return group_doc
    
    @staticmethod
    def update_setting(group_doc: Dict, setting_key: str, value: any) -> Dict:
        """
        Update a specific group setting.
        
        Args:
            group_doc: Existing group document
            setting_key: Setting key to update
            value: New value
        
        Returns:
            Updated group document
        """
        if "settings" not in group_doc:
            group_doc["settings"] = config.DEFAULT_GROUP_SETTINGS.copy()
        
        group_doc["settings"][setting_key] = value
        return group_doc
    
    @staticmethod
    def increment_file_count(group_doc: Dict) -> Dict:
        """
        Increment total files count.
        
        Args:
            group_doc: Existing group document
        
        Returns:
            Updated group document
        """
        if "stats" not in group_doc:
            group_doc["stats"] = {"total_files": 0, "total_ai_requests": 0}
        
        group_doc["stats"]["total_files"] += 1
        return group_doc
    
    @staticmethod
    def increment_ai_requests(group_doc: Dict) -> Dict:
        """
        Increment AI requests count.
        
        Args:
            group_doc: Existing group document
        
        Returns:
            Updated group document
        """
        if "stats" not in group_doc:
            group_doc["stats"] = {"total_files": 0, "total_ai_requests": 0}
        
        group_doc["stats"]["total_ai_requests"] += 1
        return group_doc
    
    @staticmethod
    def block_user(group_doc: Dict, user_id: int) -> Dict:
        """
        Add user to blocked users list.
        
        Args:
            group_doc: Existing group document
            user_id: User ID to block
        
        Returns:
            Updated group document
        """
        if "settings" not in group_doc:
            group_doc["settings"] = config.DEFAULT_GROUP_SETTINGS.copy()
        
        if "blocked_users" not in group_doc["settings"]:
            group_doc["settings"]["blocked_users"] = []
        
        if user_id not in group_doc["settings"]["blocked_users"]:
            group_doc["settings"]["blocked_users"].append(user_id)
        
        return group_doc
    
    @staticmethod
    def unblock_user(group_doc: Dict, user_id: int) -> Dict:
        """
        Remove user from blocked users list.
        
        Args:
            group_doc: Existing group document
            user_id: User ID to unblock
        
        Returns:
            Updated group document
        """
        if "settings" in group_doc and "blocked_users" in group_doc["settings"]:
            if user_id in group_doc["settings"]["blocked_users"]:
                group_doc["settings"]["blocked_users"].remove(user_id)
        
        return group_doc
    
    @staticmethod
    def validate_group_document(group_doc: Dict) -> bool:
        """
        Validate group document structure.
        
        Args:
            group_doc: Group document to validate
        
        Returns:
            True if valid, False otherwise
        """
        required_fields = ["chat_id", "title", "created_at", "settings", "stats"]
        return all(field in group_doc for field in required_fields)