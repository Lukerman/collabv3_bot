"""
File model for CollaLearn bot.
Defines file data structure and helper functions.
"""

from datetime import datetime
from typing import Dict, Optional, List


class FileModel:
    """
    File model for database operations.
    Represents an uploaded study material file.
    """
    
    @staticmethod
    def create_file_document(
        file_id: str,
        file_unique_id: str,
        file_name: str,
        mime_type: str,
        uploader_id: int,
        uploader_username: str,
        group_id: int,
        message_id: int,
        caption: str = "",
        tags: List[str] = None
    ) -> Dict:
        """
        Create a new file document structure.
        
        Args:
            file_id: Telegram file ID
            file_unique_id: Telegram file unique ID
            file_name: Name of the file
            mime_type: MIME type
            uploader_id: User ID who uploaded
            uploader_username: Username of uploader
            group_id: Group chat ID
            message_id: Message ID of the file
            caption: File caption (optional)
            tags: List of tags (optional)
        
        Returns:
            File document dictionary
        """
        return {
            "file_id": file_id,
            "file_unique_id": file_unique_id,
            "file_name": file_name,
            "mime_type": mime_type,
            "caption": caption,
            "tags": tags or [],
            "ai_tags": [],
            "uploader_id": uploader_id,
            "uploader_username": uploader_username,
            "group_id": group_id,
            "message_id": message_id,
            "uploaded_at": datetime.utcnow(),
            "deleted": False
        }
    
    @staticmethod
    def add_tags(file_doc: Dict, new_tags: List[str]) -> Dict:
        """
        Add tags to a file document.
        
        Args:
            file_doc: Existing file document
            new_tags: List of tags to add
        
        Returns:
            Updated file document
        """
        if "tags" not in file_doc:
            file_doc["tags"] = []
        
        # Merge and deduplicate
        file_doc["tags"] = list(set(file_doc["tags"] + new_tags))
        return file_doc
    
    @staticmethod
    def set_ai_tags(file_doc: Dict, ai_tags: List[str]) -> Dict:
        """
        Set AI-generated tags for a file.
        
        Args:
            file_doc: Existing file document
            ai_tags: List of AI-generated tags
        
        Returns:
            Updated file document
        """
        file_doc["ai_tags"] = ai_tags
        return file_doc
    
    @staticmethod
    def soft_delete(file_doc: Dict) -> Dict:
        """
        Mark file as deleted (soft delete).
        
        Args:
            file_doc: Existing file document
        
        Returns:
            Updated file document
        """
        file_doc["deleted"] = True
        file_doc["deleted_at"] = datetime.utcnow()
        return file_doc
    
    @staticmethod
    def is_image(file_doc: Dict) -> bool:
        """
        Check if file is an image.
        
        Args:
            file_doc: File document
        
        Returns:
            True if image, False otherwise
        """
        mime_type = file_doc.get("mime_type", "")
        return mime_type.startswith("image/")
    
    @staticmethod
    def is_document(file_doc: Dict) -> bool:
        """
        Check if file is a document (PDF, DOCX, etc).
        
        Args:
            file_doc: File document
        
        Returns:
            True if document, False otherwise
        """
        mime_type = file_doc.get("mime_type", "")
        document_types = ["application/pdf", "application/msword", 
                         "application/vnd.openxmlformats-officedocument"]
        return any(doc_type in mime_type for doc_type in document_types)
    
    @staticmethod
    def validate_file_document(file_doc: Dict) -> bool:
        """
        Validate file document structure.
        
        Args:
            file_doc: File document to validate
        
        Returns:
            True if valid, False otherwise
        """
        required_fields = [
            "file_id", "file_unique_id", "file_name", "mime_type",
            "uploader_id", "group_id", "message_id", "uploaded_at"
        ]
        return all(field in file_doc for field in required_fields)