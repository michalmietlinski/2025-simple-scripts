import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Application configuration
APP_CONFIG = {
    "app_name": "DALL-E Image Generator",
    "version": "0.1.0",
    "output_dir": "outputs",
    "data_dir": "data",
    "log_file": "app.log",
    "db_file": "data/prompt_history.db",
    "default_image_size": "1024x1024",
    "default_image_quality": "standard",
    "default_image_style": "vivid",
    "max_batch_size": 10,
    "api_rate_limit": 5  # requests per minute
}

# OpenAI API configuration
OPENAI_CONFIG = {
    "api_key": os.getenv("OPENAI_API_KEY"),  # Will be None if not found
    "model": "dall-e-2",
    "api_base": "https://api.openai.com/v1",
    "organization": os.getenv("OPENAI_ORGANIZATION", ""),  # Optional
    "timeout": 60,  # Seconds
}

# Create necessary directories if they don't exist
def ensure_directories():
    """Create necessary directories if they don't exist."""
    os.makedirs(APP_CONFIG["output_dir"], exist_ok=True)
    os.makedirs(APP_CONFIG["data_dir"], exist_ok=True)
    
    # Create date-based output directory
    from datetime import datetime
    today = datetime.now().strftime("%Y-%m-%d")
    os.makedirs(os.path.join(APP_CONFIG["output_dir"], today), exist_ok=True) 
