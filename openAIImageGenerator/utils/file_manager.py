import os
import logging
from datetime import datetime
from config import APP_CONFIG

logger = logging.getLogger(__name__)

class FileManager:
    """Manages file operations for saving and organizing generated images."""
    
    def __init__(self):
        """Initialize the file manager."""
        self.output_dir = APP_CONFIG["output_dir"]
        self.ensure_directories()
        logger.info("File manager initialized")
    
    def ensure_directories(self):
        """Create necessary directories if they don't exist."""
        os.makedirs(self.output_dir, exist_ok=True)
        
        # Create date-based output directory
        today = datetime.now().strftime("%Y-%m-%d")
        today_dir = os.path.join(self.output_dir, today)
        os.makedirs(today_dir, exist_ok=True)
        
        return today_dir
    
    def get_output_path(self, prompt, description=None):
        """Generate a filename for a new image based on prompt and description."""
        today_dir = self.ensure_directories()
        
        # Create a timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Create a short prompt summary (first 30 chars)
        prompt_summary = prompt[:30].replace(" ", "_").replace("/", "-")
        
        # Add description if provided
        if description:
            desc_text = f"_{description.replace(' ', '_')}"
        else:
            desc_text = ""
        
        # Create filename
        filename = f"{timestamp}_{prompt_summary}{desc_text}.png"
        
        # Return full path
        return os.path.join(today_dir, filename)
    
    def save_image(self, image_data, prompt, description=None):
        """Save image data to file."""
        output_path = self.get_output_path(prompt, description)
        
        try:
            # Save the image
            with open(output_path, "wb") as f:
                f.write(image_data)
            
            logger.info(f"Image saved to {output_path}")
            return output_path
        except Exception as e:
            logger.error(f"Failed to save image: {str(e)}")
            return None 
