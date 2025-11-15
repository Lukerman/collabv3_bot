"""
Database module for CollaLearn bot.
Handles all MongoDB operations with async support.
"""

import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Any
from pymongo import MongoClient, ASCENDING, DESCENDING
from pymongo.errors import PyMongoError

from config import config

logger = logging.getLogger(__name__)


class Database:
    """
    Database manager for MongoDB operations.
    Implements singleton pattern for connection management.
    """
    
    _instance = None
    _client = None
    _db = None
    
    def __new__(cls):
        """Implement singleton pattern."""
        if cls._instance is None:
            cls._instance = super(Database, cls).__new__(cls)
            cls._instance._initialize()
        return cls._instance
    
    def _initialize(self) -> None:
        """Initialize database connection."""
        try:
            self._client = MongoClient(config.MONGODB_URI)
            self._db = self._client[config.DB_NAME]
            self._create_indexes()
            logger.info("Database initialized successfully")
        except PyMongoError as e:
            logger.error(f"Failed to initialize database: {e}")
            raise
    
    def _create_indexes(self) -> None:
        """Create database indexes for optimal query performance."""
        try:
            # Users collection indexes
            self._db[config.USERS_COLLECTION].create_index("user_id", unique=True)
            
            # Groups collection indexes
            self._db[config.GROUPS_COLLECTION].create_index("chat_id", unique=True)
            
            # Files collection indexes
            self._db[config.FILES_COLLECTION].create_index([
                ("group_id", ASCENDING),
                ("deleted", ASCENDING)
            ])
            self._db[config.FILES_COLLECTION].create_index("tags")
            self._db[config.FILES_COLLECTION].create_index("file_name")
            self._db[config.FILES_COLLECTION].create_index([("uploaded_at", DESCENDING)])
            
            # Search sessions indexes
            self._db[config.SEARCH_SESSIONS_COLLECTION].create_index("session_id", unique=True)
            self._db[config.SEARCH_SESSIONS_COLLECTION].create_index([("expires_at", ASCENDING)])
            
            # AI logs indexes
            self._db[config.AI_LOGS_COLLECTION].create_index([
                ("group_id", ASCENDING),
                ("created_at", DESCENDING)
            ])
            
            logger.info("Database indexes created successfully")
        except PyMongoError as e:
            logger.error(f"Failed to create indexes: {e}")
    
    # ==================== USER OPERATIONS ====================
    
    def upsert_user(self, user_id: int, username: str = None, first_name: str = None, chat_id: int = None) -> bool:
        """
        Insert or update user information.
        
        Args:
            user_id: Telegram user ID
            username: Username (optional)
            first_name: First name (optional)
            chat_id: Group chat ID to add to user's groups
        
        Returns:
            True if successful, False otherwise
        """
        try:
            update_data = {
                "$set": {
                    "last_seen_at": datetime.utcnow()
                },
                "$setOnInsert": {
                    "user_id": user_id,
                    "first_seen_at": datetime.utcnow(),
                    "is_global_admin": user_id in config.GLOBAL_ADMIN_IDS,
                    "groups": []
                }
            }
            
            if username:
                update_data["$set"]["username"] = username
            
            if first_name:
                update_data["$set"]["first_name"] = first_name
            
            if chat_id:
                update_data["$addToSet"] = {"groups": chat_id}
            
            self._db[config.USERS_COLLECTION].update_one(
                {"user_id": user_id},
                update_data,
                upsert=True
            )
            return True
        except PyMongoError as e:
            logger.error(f"Failed to upsert user {user_id}: {e}")
            return False
    
    def get_user(self, user_id: int) -> Optional[Dict]:
        """Get user document by user_id."""
        try:
            return self._db[config.USERS_COLLECTION].find_one({"user_id": user_id})
        except PyMongoError as e:
            logger.error(f"Failed to get user {user_id}: {e}")
            return None
    
    # ==================== GROUP OPERATIONS ====================
    
    def upsert_group(self, chat_id: int, title: str) -> bool:
        """
        Insert or update group information.
        
        Args:
            chat_id: Telegram chat ID
            title: Group title
        
        Returns:
            True if successful, False otherwise
        """
        try:
            self._db[config.GROUPS_COLLECTION].update_one(
                {"chat_id": chat_id},
                {
                    "$set": {
                        "title": title,
                        "last_seen_at": datetime.utcnow()
                    },
                    "$setOnInsert": {
                        "chat_id": chat_id,
                        "created_at": datetime.utcnow(),
                        "settings": config.DEFAULT_GROUP_SETTINGS.copy(),
                        "stats": {
                            "total_files": 0,
                            "total_ai_requests": 0
                        }
                    }
                },
                upsert=True
            )
            return True
        except PyMongoError as e:
            logger.error(f"Failed to upsert group {chat_id}: {e}")
            return False
    
    def get_group(self, chat_id: int) -> Optional[Dict]:
        """Get group document by chat_id."""
        try:
            return self._db[config.GROUPS_COLLECTION].find_one({"chat_id": chat_id})
        except PyMongoError as e:
            logger.error(f"Failed to get group {chat_id}: {e}")
            return None
    
    def update_group_settings(self, chat_id: int, settings: Dict) -> bool:
        """Update group settings."""
        try:
            self._db[config.GROUPS_COLLECTION].update_one(
                {"chat_id": chat_id},
                {"$set": {"settings": settings}}
            )
            return True
        except PyMongoError as e:
            logger.error(f"Failed to update group settings for {chat_id}: {e}")
            return False
    
    def get_all_groups(self, skip: int = 0, limit: int = 100) -> List[Dict]:
        """Get all groups with pagination."""
        try:
            return list(
                self._db[config.GROUPS_COLLECTION]
                .find()
                .skip(skip)
                .limit(limit)
                .sort("created_at", DESCENDING)
            )
        except PyMongoError as e:
            logger.error(f"Failed to get all groups: {e}")
            return []
    
    def delete_group(self, chat_id: int) -> bool:
        """Delete group and all associated data."""
        try:
            self._db[config.GROUPS_COLLECTION].delete_one({"chat_id": chat_id})
            self._db[config.FILES_COLLECTION].delete_many({"group_id": chat_id})
            self._db[config.SEARCH_SESSIONS_COLLECTION].delete_many({"group_id": chat_id})
            self._db[config.AI_LOGS_COLLECTION].delete_many({"group_id": chat_id})
            return True
        except PyMongoError as e:
            logger.error(f"Failed to delete group {chat_id}: {e}")
            return False
    
    # ==================== FILE OPERATIONS ====================
    
    def insert_file(self, file_data: Dict) -> Optional[str]:
        """
        Insert new file document.
        
        Args:
            file_data: File metadata dictionary
        
        Returns:
            Inserted document ID or None
        """
        try:
            file_data["uploaded_at"] = datetime.utcnow()
            file_data["deleted"] = False
            
            result = self._db[config.FILES_COLLECTION].insert_one(file_data)
            
            # Update group stats
            self._db[config.GROUPS_COLLECTION].update_one(
                {"chat_id": file_data["group_id"]},
                {"$inc": {"stats.total_files": 1}}
            )
            
            return str(result.inserted_id)
        except PyMongoError as e:
            logger.error(f"Failed to insert file: {e}")
            return None
    
    def update_file_tags(self, file_id: str, tags: List[str], ai_tags: List[str] = None) -> bool:
        """Update file tags."""
        try:
            from bson.objectid import ObjectId
            update_data = {"$set": {"tags": tags}}
            if ai_tags is not None:
                update_data["$set"]["ai_tags"] = ai_tags
            
            self._db[config.FILES_COLLECTION].update_one(
                {"_id": ObjectId(file_id)},
                update_data
            )
            return True
        except PyMongoError as e:
            logger.error(f"Failed to update file tags for {file_id}: {e}")
            return False
    
    def search_files(self, group_id: int, query: str, limit: int = 10) -> List[Dict]:
        """
        Search files by tags, filename, or caption.
        
        Args:
            group_id: Group chat ID
            query: Search query
            limit: Maximum results
        
        Returns:
            List of matching file documents
        """
        try:
            search_terms = query.lower().split()
            
            # Build search criteria
            search_conditions = []
            for term in search_terms:
                search_conditions.append({"tags": {"$regex": term, "$options": "i"}})
                search_conditions.append({"file_name": {"$regex": term, "$options": "i"}})
                search_conditions.append({"caption": {"$regex": term, "$options": "i"}})
            
            results = list(
                self._db[config.FILES_COLLECTION].find({
                    "group_id": group_id,
                    "deleted": False,
                    "$or": search_conditions
                })
                .limit(limit)
                .sort("uploaded_at", DESCENDING)
            )
            
            return results
        except PyMongoError as e:
            logger.error(f"Failed to search files in group {group_id}: {e}")
            return []
    
    def get_file_by_id(self, file_id: str) -> Optional[Dict]:
        """Get file by MongoDB ObjectId."""
        try:
            from bson.objectid import ObjectId
            return self._db[config.FILES_COLLECTION].find_one({"_id": ObjectId(file_id)})
        except PyMongoError as e:
            logger.error(f"Failed to get file {file_id}: {e}")
            return None
    
    def get_latest_files(self, group_id: int, limit: int = 10) -> List[Dict]:
        """Get latest files for a group."""
        try:
            return list(
                self._db[config.FILES_COLLECTION]
                .find({"group_id": group_id, "deleted": False})
                .sort("uploaded_at", DESCENDING)
                .limit(limit)
            )
        except PyMongoError as e:
            logger.error(f"Failed to get latest files for group {group_id}: {e}")
            return []
    
    def soft_delete_file(self, file_id: str) -> bool:
        """Soft delete a file."""
        try:
            from bson.objectid import ObjectId
            self._db[config.FILES_COLLECTION].update_one(
                {"_id": ObjectId(file_id)},
                {"$set": {"deleted": True}}
            )
            return True
        except PyMongoError as e:
            logger.error(f"Failed to delete file {file_id}: {e}")
            return False
    
    # ==================== SEARCH SESSION OPERATIONS ====================
    
    def create_search_session(self, session_id: str, requester_id: int, group_id: int, results: List[str]) -> bool:
        """Create a new search session."""
        try:
            self._db[config.SEARCH_SESSIONS_COLLECTION].insert_one({
                "session_id": session_id,
                "requester_id": requester_id,
                "group_id": group_id,
                "results": results,
                "created_at": datetime.utcnow(),
                "expires_at": datetime.utcnow() + timedelta(hours=config.SEARCH_SESSION_EXPIRY_HOURS)
            })
            return True
        except PyMongoError as e:
            logger.error(f"Failed to create search session {session_id}: {e}")
            return False
    
    def get_search_session(self, session_id: str) -> Optional[Dict]:
        """Get search session by ID."""
        try:
            return self._db[config.SEARCH_SESSIONS_COLLECTION].find_one({
                "session_id": session_id,
                "expires_at": {"$gt": datetime.utcnow()}
            })
        except PyMongoError as e:
            logger.error(f"Failed to get search session {session_id}: {e}")
            return None
    
    async def cleanup_expired_search_sessions(self) -> int:
        """Remove expired search sessions."""
        try:
            result = self._db[config.SEARCH_SESSIONS_COLLECTION].delete_many({
                "expires_at": {"$lt": datetime.utcnow()}
            })
            return result.deleted_count
        except PyMongoError as e:
            logger.error(f"Failed to cleanup expired sessions: {e}")
            return 0
    
    # ==================== AI LOG OPERATIONS ====================
    
    def log_ai_request(self, user_id: int, group_id: int, prompt_type: str, text_snippet: str = "") -> bool:
        """Log an AI request."""
        try:
            self._db[config.AI_LOGS_COLLECTION].insert_one({
                "user_id": user_id,
                "group_id": group_id,
                "prompt_type": prompt_type,
                "text_snippet": text_snippet[:200],
                "created_at": datetime.utcnow()
            })
            
            # Update group stats
            self._db[config.GROUPS_COLLECTION].update_one(
                {"chat_id": group_id},
                {"$inc": {"stats.total_ai_requests": 1}}
            )
            
            return True
        except PyMongoError as e:
            logger.error(f"Failed to log AI request: {e}")
            return False
    
    # ==================== STATS OPERATIONS ====================
    
    def get_global_stats(self) -> Dict[str, int]:
        """Get global bot statistics."""
        try:
            return {
                "total_groups": self._db[config.GROUPS_COLLECTION].count_documents({}),
                "total_users": self._db[config.USERS_COLLECTION].count_documents({}),
                "total_files": self._db[config.FILES_COLLECTION].count_documents({"deleted": False}),
                "total_ai_requests": self._db[config.AI_LOGS_COLLECTION].count_documents({})
            }
        except PyMongoError as e:
            logger.error(f"Failed to get global stats: {e}")
            return {}
    
    def get_group_stats(self, group_id: int) -> Dict[str, Any]:
        """Get statistics for a specific group."""
        try:
            group = self.get_group(group_id)
            if not group:
                return {}
            
            # Get top uploaders
            top_uploaders = list(
                self._db[config.FILES_COLLECTION].aggregate([
                    {"$match": {"group_id": group_id, "deleted": False}},
                    {"$group": {
                        "_id": "$uploader_username",
                        "count": {"$sum": 1}
                    }},
                    {"$sort": {"count": -1}},
                    {"$limit": 5}
                ])
            )
            
            # Get tag distribution
            tag_distribution = {}
            files = self._db[config.FILES_COLLECTION].find({"group_id": group_id, "deleted": False})
            for file in files:
                for tag in file.get("tags", []):
                    tag_distribution[tag] = tag_distribution.get(tag, 0) + 1
            
            return {
                "total_files": group["stats"]["total_files"],
                "total_ai_requests": group["stats"]["total_ai_requests"],
                "top_uploaders": top_uploaders,
                "tag_distribution": dict(sorted(tag_distribution.items(), key=lambda x: x[1], reverse=True)[:10])
            }
        except PyMongoError as e:
            logger.error(f"Failed to get group stats for {group_id}: {e}")
            return {}