import os
import logging
from openai import OpenAI
from config import OPENAI_CONFIG

logger = logging.getLogger(__name__)

class OpenAIClient:
    """Wrapper for OpenAI API client with DALL-E specific functionality."""
    
    def __init__(self):
        """Initialize the OpenAI client with API key from config."""
        self.api_key = OPENAI_CONFIG["api_key"]
        if not self.api_key:
            logger.error("OpenAI API key not found")
            raise ValueError("OpenAI API key is required")
        
        self.client = OpenAI(
            api_key=self.api_key,
            organization=OPENAI_CONFIG["organization"],
            timeout=OPENAI_CONFIG["timeout"]
        )
        logger.info("OpenAI client initialized")
    
    def validate_api_key(self):
        """Validate the API key by making a simple request."""
        try:
            # Make a simple models list request to validate the API key
            self.client.models.list(limit=1)
            logger.info("API key validated successfully")
            return True
        except Exception as e:
            logger.error(f"API key validation failed: {str(e)}")
            return False 
