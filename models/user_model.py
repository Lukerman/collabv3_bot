"""
User model for CollaLearn bot.
Defines user data structure and helper functions.
"""

from datetime import datetime
from typing import Dict, Optional, List


class UserModel:
    """
    User model for database operations.
    Represents a Telegram user in the system.
    """
    
    @staticmethod
    def create_user_document(
        user_id: int,
        username: str = None,
        first_name: str = None,
        is_global_admin: bool = False
    ) -> Dict:
        """
        Create a new user document structure.
        
        Args:
            user_id: Telegram user ID
            username: Username (optional)
            first_name: First name (optional)
            is_global_admin: Whether user is a global admin
        
        Returns:
            User document dictionary
        """
        return {
            "user_id": user_id,
            "username": username or "Unknown",
            "first_name": first_name or "User",
            "first_seen_at": datetime.utcnow(),
            "last_seen_at": datetime.utcnow(),
            "is_global_admin": is_global_admin,
            "groups": []
        }
    
    @staticmethod
    def update_user_activity(user_doc: Dict) -> Dict:
        """
        Update user's last seen timestamp.
        
        Args:
            user_doc: Existing user document
        
        Returns:
            Updated user document
        """
        user_doc["last_seen_at"] = datetime.utcnow()
        return user_doc
    
    @staticmethod
    def add_group_to_user(user_doc: Dict, chat_id: int) -> Dict:
        """
        Add a group to user's groups list.
        
        Args:
            user_doc: Existing user document
            chat_id: Group chat ID to add
        
        Returns:
            Updated user document
        """
        if "groups" not in user_doc:
            user_doc["groups"] = []
        
        if chat_id not in user_doc["groups"]:
            user_doc["groups"].append(chat_id)
        
        return user_doc
    
    @staticmethod
    def validate_user_document(user_doc: Dict) -> bool:
        """
        Validate user document structure.
        
        Args:
            user_doc: User document to validate
        
        Returns:
            True if valid, False otherwise
        """
        required_fields = ["user_id", "username", "first_seen_at", "last_seen_at"]
        return all(field in user_doc for field in required_fields)