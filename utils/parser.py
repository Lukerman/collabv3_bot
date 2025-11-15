"""
Parsing utilities for CollaLearn bot.
Parses hashtags, commands, and other text formats.
"""

import re
from typing import List, Dict, Optional


def parse_hashtags(text: str) -> List[str]:
    """
    Extract hashtags from text.
    
    Args:
        text: Text containing hashtags
    
    Returns:
        List of hashtag strings (without # symbol)
    """
    if not text:
        return []
    
    # Find all hashtags (word characters after #)
    hashtags = re.findall(r'#(\w+)', text)
    
    # Clean and deduplicate
    tags = []
    for tag in hashtags:
        tag = tag.lower().strip()
        if tag and tag not in tags:
            tags.append(tag)
    
    return tags


def parse_command_args(text: str, command: str) -> List[str]:
    """
    Parse arguments from a command.
    
    Args:
        text: Full message text
        command: Command name (without /)
    
    Returns:
        List of argument strings
    """
    # Remove command from text
    pattern = f"^/{command}\\s*"
    args_text = re.sub(pattern, "", text, flags=re.IGNORECASE).strip()
    
    if not args_text:
        return []
    
    # Split by whitespace
    return args_text.split()


def parse_tag_input(text: str) -> List[str]:
    """
    Parse tags from user input (comma or space separated).
    
    Args:
        text: Input text with tags
    
    Returns:
        List of cleaned tag strings
    """
    if not text:
        return []
    
    # Replace commas with spaces
    text = text.replace(",", " ")
    
    # Remove hashtags if present
    text = text.replace("#", "")
    
    # Split and clean
    tags = []
    for tag in text.split():
        tag = tag.strip().lower()
        # Remove special characters except hyphen and underscore
        tag = "".join(c for c in tag if c.isalnum() or c in ["-", "_"])
        if tag and tag not in tags:
            tags.append(tag)
    
    return tags


def format_file_size(size_bytes: int) -> str:
    """
    Format file size in human-readable format.
    
    Args:
        size_bytes: File size in bytes
    
    Returns:
        Formatted string (e.g., "1.5 MB")
    """
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f} TB"


def truncate_string(text: str, max_length: int, suffix: str = "...") -> str:
    """
    Truncate string to maximum length with suffix.
    
    Args:
        text: Text to truncate
        max_length: Maximum length
        suffix: Suffix to add when truncated
    
    Returns:
        Truncated string
    """
    if not text or len(text) <= max_length:
        return text
    
    return text[:max_length - len(suffix)] + suffix


def escape_markdown(text: str) -> str:
    """
    Escape special Markdown characters.
    
    Args:
        text: Text to escape
    
    Returns:
        Escaped text
    """
    special_chars = ['_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']
    for char in special_chars:
        text = text.replace(char, f'\\{char}')
    return text


def parse_callback_data(data: str, expected_parts: int = 2) -> Optional[Dict[str, str]]:
    """
    Parse callback data from inline buttons.
    
    Args:
        data: Callback data string (format: "action:param1:param2")
        expected_parts: Expected number of parts after split
    
    Returns:
        Dictionary with parsed data or None if invalid
    """
    parts = data.split(":")
    
    if len(parts) < expected_parts:
        return None
    
    result = {"action": parts[0]}
    
    for i, part in enumerate(parts[1:], 1):
        result[f"param{i}"] = part
    
    return result