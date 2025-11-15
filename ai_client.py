"""
AI client module for CollaLearn bot.
Handles all interactions with Perplexity AI API.
"""

import logging
import aiohttp
from typing import Optional, List, Dict
from config import config

logger = logging.getLogger(__name__)


class AIClient:
    """
    Client for Perplexity AI API operations.
    Provides methods for summarization, explanation, quiz generation, and tagging.
    """
    
    def __init__(self):
        """Initialize AI client with API credentials."""
        self.api_url = config.PERPLEXITY_API_URL
        self.api_key = config.PERPLEXITY_API_KEY
        self.model = config.PERPLEXITY_MODEL
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        # Validate API key
        if not self.api_key or self.api_key == "your_perplexity_api_key_here":
            logger.error("Perplexity API key not configured properly!")
    
    async def _make_request(self, messages: List[Dict[str, str]], temperature: float = None) -> Optional[str]:
        """
        Make an async request to Perplexity API.
        
        Args:
            messages: List of message dictionaries with role and content
            temperature: Temperature for response randomness
        
        Returns:
            Generated text response or None on error
        """
        try:
            # Validate API key
            if not self.api_key or self.api_key == "your_perplexity_api_key_here":
                logger.error("Perplexity API key not configured!")
                return None
            
            payload = {
                "model": self.model,
                "messages": messages,
                "temperature": temperature or config.AI_TEMPERATURE,
                "max_tokens": config.AI_MAX_TOKENS
            }
            
            logger.info(f"Making Perplexity API request with model: {self.model}")
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.api_url,
                    headers=self.headers,
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=60)
                ) as response:
                    response_text = await response.text()
                    
                    if response.status == 200:
                        data = await response.json()
                        
                        # Check response structure
                        if "choices" not in data or len(data["choices"]) == 0:
                            logger.error(f"Unexpected API response structure: {data}")
                            return None
                        
                        content = data["choices"][0]["message"]["content"]
                        logger.info(f"Successfully received AI response ({len(content)} chars)")
                        return content
                    
                    elif response.status == 401:
                        logger.error(f"Perplexity API authentication failed. Check your API key.")
                        return None
                    
                    elif response.status == 429:
                        logger.error(f"Perplexity API rate limit exceeded")
                        return None
                    
                    else:
                        logger.error(f"Perplexity API error {response.status}: {response_text}")
                        return None
                        
        except aiohttp.ClientError as e:
            logger.error(f"Network error calling Perplexity API: {e}")
            return None
        except asyncio.TimeoutError:
            logger.error(f"Perplexity API request timed out")
            return None
        except Exception as e:
            logger.error(f"Unexpected error calling Perplexity API: {e}", exc_info=True)
            return None
    
    async def summarize_text(self, text: str) -> Optional[str]:
        """
        Generate a concise summary of the given text.
        
        Args:
            text: Text to summarize (will be truncated if too long)
        
        Returns:
            Summary string or None on error
        """
        try:
            # Truncate text if too long
            truncated_text = text[:config.MAX_AI_TEXT_LENGTH]
            
            messages = [
                {
                    "role": "system",
                    "content": "You are a helpful academic assistant. Provide clear, concise summaries of study materials."
                },
                {
                    "role": "user",
                    "content": f"Please provide a comprehensive summary of the following content in bullet points:\n\n{truncated_text}"
                }
            ]
            
            response = await self._make_request(messages)
            return response
        except Exception as e:
            logger.error(f"Error in summarize_text: {e}", exc_info=True)
            return None
    
    async def explain_text(self, text: str, question: str = None) -> Optional[str]:
        """
        Provide a detailed explanation of a topic or answer a question.
        
        Args:
            text: Context text for explanation
            question: Specific question to answer (optional)
        
        Returns:
            Explanation string or None on error
        """
        try:
            truncated_text = text[:config.MAX_AI_TEXT_LENGTH] if text else ""
            
            if question:
                if truncated_text:
                    user_content = f"Context:\n{truncated_text}\n\nQuestion: {question}\n\nProvide a clear, detailed explanation suitable for students."
                else:
                    user_content = f"Question: {question}\n\nProvide a clear, detailed explanation suitable for students."
            else:
                user_content = f"Explain the following content in detail, making it easy for students to understand:\n\n{truncated_text}"
            
            messages = [
                {
                    "role": "system",
                    "content": "You are an expert tutor. Explain concepts clearly with examples where appropriate."
                },
                {
                    "role": "user",
                    "content": user_content
                }
            ]
            
            response = await self._make_request(messages)
            return response
        except Exception as e:
            logger.error(f"Error in explain_text: {e}", exc_info=True)
            return None
    
    async def generate_quiz(self, text: str, count: int = 5) -> Optional[str]:
        """
        Generate multiple choice quiz questions from content.
        
        Args:
            text: Content to generate quiz from
            count: Number of questions to generate
        
        Returns:
            Formatted quiz string or None on error
        """
        try:
            truncated_text = text[:config.MAX_AI_TEXT_LENGTH]
            count = min(max(count, 1), 10)  # Limit between 1-10
            
            messages = [
                {
                    "role": "system",
                    "content": "You are a quiz generator. Create multiple choice questions with 4 options each."
                },
                {
                    "role": "user",
                    "content": f"""Generate {count} multiple choice questions based on this content:

{truncated_text}

Format each question as:
Q1. [Question]
A) [Option]
B) [Option]
C) [Option]
D) [Option]
Correct Answer: [Letter]

Make questions challenging but fair for students."""
                }
            ]
            
            response = await self._make_request(messages, temperature=0.7)
            return response
        except Exception as e:
            logger.error(f"Error in generate_quiz: {e}", exc_info=True)
            return None
    
    async def suggest_tags(self, text: str, filename: str = "") -> Optional[List[str]]:
        """
        Suggest relevant tags for a file based on its content.
        
        Args:
            text: File content text
            filename: Filename for additional context
        
        Returns:
            List of suggested tags or None on error
        """
        try:
            truncated_text = text[:config.MAX_AI_TEXT_LENGTH]
            
            context = f"Filename: {filename}\n\n" if filename else ""
            context += f"Content:\n{truncated_text}"
            
            messages = [
                {
                    "role": "system",
                    "content": "You are a content analyzer. Suggest 3-7 relevant, concise tags for academic content."
                },
                {
                    "role": "user",
                    "content": f"""{context}

Suggest relevant tags for this content. Return ONLY the tags as a comma-separated list (e.g., physics, mechanics, kinematics).
Make tags lowercase, concise, and specific to the academic subject matter."""
                }
            ]
            
            response = await self._make_request(messages)
            if response:
                # Parse tags from response
                tags = [tag.strip().lower() for tag in response.split(",")]
                # Filter and validate tags
                tags = [tag for tag in tags if tag and len(tag) <= config.MAX_TAG_LENGTH]
                return tags[:config.MAX_TAGS_PER_FILE]
            return None
        except Exception as e:
            logger.error(f"Error in suggest_tags: {e}", exc_info=True)
            return None


# Create global AI client instance
ai_client = AIClient()