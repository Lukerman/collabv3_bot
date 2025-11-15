"""
Handlers package for CollaLearn bot.
Contains all command and callback handlers.
"""

from . import base_handlers, file_handlers, search_handlers, ai_handlers, admin_handlers

__all__ = [
    'base_handlers',
    'file_handlers',
    'search_handlers',
    'ai_handlers',
    'admin_handlers'
]