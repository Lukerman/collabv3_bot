"""
Search session model for CollaLearn bot.
Defines search session data structure and helper functions.
"""

from datetime import datetime, timedelta
from typing import Dict, Optional, List
from config import config


class SearchSessionModel:
    """
    Search session model for database operations.
    Represents a temporary search session with results.
    """
    
    @staticmethod
    def create_session_document(
        session_id: str,
        requester_id: int,
        group_id: int,
        results: List[str]
    ) -> Dict:
        """
        Create a new search session document.
        
        Args:
            session_id: Unique session identifier
            requester_id: User ID who initiated search
            group_id: Group chat ID
            results: List of file IDs in results
        
        Returns:
            Search session document dictionary
        """
        return {
            "session_id": session_id,
            "requester_id": requester_id,
            "group_id": group_id,
            "results": results,
            "created_at": datetime.utcnow(),
            "expires_at": datetime.utcnow() + timedelta(hours=config.SEARCH_SESSION_EXPIRY_HOURS)
        }
    
    @staticmethod
    def is_expired(session_doc: Dict) -> bool:
        """
        Check if search session has expired.
        
        Args:
            session_doc: Search session document
        
        Returns:
            True if expired, False otherwise
        """
        expires_at = session_doc.get("expires_at")
        if not expires_at:
            return True
        
        return datetime.utcnow() > expires_at
    
    @staticmethod
    def is_authorized(session_doc: Dict, user_id: int) -> bool:
        """
        Check if user is authorized to access session results.
        
        Args:
            session_doc: Search session document
            user_id: User ID to check
        
        Returns:
            True if authorized, False otherwise
        """
        return session_doc.get("requester_id") == user_id
    
    @staticmethod
    def get_result_count(session_doc: Dict) -> int:
        """
        Get number of results in session.
        
        Args:
            session_doc: Search session document
        
        Returns:
            Number of results
        """
        return len(session_doc.get("results", []))
    
    @staticmethod
    def get_result_by_index(session_doc: Dict, index: int) -> Optional[str]:
        """
        Get result file ID by index.
        
        Args:
            session_doc: Search session document
            index: Index of result
        
        Returns:
            File ID or None if index out of range
        """
        results = session_doc.get("results", [])
        if 0 <= index < len(results):
            return results[index]
        return None
    
    @staticmethod
    def validate_session_document(session_doc: Dict) -> bool:
        """
        Validate search session document structure.
        
        Args:
            session_doc: Session document to validate
        
        Returns:
            True if valid, False otherwise
        """
        required_fields = [
            "session_id", "requester_id", "group_id",
            "results", "created_at", "expires_at"
        ]
        return all(field in session_doc for field in required_fields)