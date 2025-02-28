"""Configuration management for the application."""

import os
from typing import Dict, Any
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Config:
    """Application configuration."""
    
    # OpenAI settings
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    
    # Image generation defaults
    DEFAULT_IMAGE_SIZE = "1024x1024"
    DEFAULT_IMAGE_QUALITY = "standard"
    DEFAULT_MODEL = "dall-e-3"
    
    # File paths
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    OUTPUT_DIR = os.path.join(BASE_DIR, "outputs")
    DB_PATH = os.path.join(BASE_DIR, "data", "dalle_generator.db")
    LOG_PATH = os.path.join(BASE_DIR, "app.log")
    
    # UI settings
    WINDOW_SIZE = "1200x800"
    WINDOW_TITLE = "DALL-E Image Generator"
    
    @classmethod
    def validate(cls) -> bool:
        """Validate required configuration.
        
        Returns:
            bool: True if configuration is valid
        
        Raises:
            ValueError: If required configuration is missing
        """
        if not cls.OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY environment variable is required")
        return True
    
    @classmethod
    def ensure_directories(cls):
        """Create necessary directories if they don't exist."""
        os.makedirs(cls.OUTPUT_DIR, exist_ok=True)
        os.makedirs(os.path.dirname(cls.DB_PATH), exist_ok=True)
        os.makedirs(os.path.dirname(cls.LOG_PATH), exist_ok=True) 
