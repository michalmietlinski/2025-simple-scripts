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
        
        # Check if output_dir is absolute or relative
        if not os.path.isabs(self.output_dir):
            # Convert to absolute path
            self.output_dir = os.path.abspath(self.output_dir)
            logger.info(f"Converted relative path to absolute: {self.output_dir}")
        
        # Ensure the directory exists
        self.ensure_directories()
        
        # Verify the directory is writable
        if not os.access(self.output_dir, os.W_OK):
            logger.error(f"Output directory is not writable: {self.output_dir}")
            # Try to create a test file
            try:
                test_file = os.path.join(self.output_dir, ".write_test")
                with open(test_file, "w") as f:
                    f.write("test")
                os.remove(test_file)
                logger.info(f"Successfully created and removed test file in output directory")
            except Exception as e:
                logger.error(f"Failed to create test file in output directory: {str(e)}")
        
        logger.info(f"File manager initialized with output directory: {os.path.abspath(self.output_dir)}")
    
    def ensure_directories(self):
        """Create necessary directories if they don't exist."""
        # Ensure base output directory exists
        os.makedirs(self.output_dir, exist_ok=True)
        
        # Create date-based output directory
        today = datetime.now().strftime("%Y-%m-%d")
        today_dir = os.path.join(self.output_dir, today)
        os.makedirs(today_dir, exist_ok=True)
        
        # Log directory creation
        logger.info(f"Ensured output directory exists: {os.path.abspath(today_dir)}")
        
        # Check if directory is writable
        test_file_path = os.path.join(today_dir, ".write_test")
        try:
            with open(test_file_path, "w") as f:
                f.write("test")
            os.remove(test_file_path)
            logger.info(f"Output directory is writable: {os.path.abspath(today_dir)}")
        except Exception as e:
            logger.error(f"Output directory is not writable: {os.path.abspath(today_dir)}, Error: {str(e)}")
        
        return today_dir
    
    def get_output_path(self, prompt, description=None):
        """Generate a filename for a new image based on prompt and description."""
        today_dir = self.ensure_directories()
        
        # Create a timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Create a short prompt summary (first 30 chars)
        prompt_summary = prompt[:30].replace(" ", "_").replace("/", "-").replace("\\", "-")
        # Remove any other invalid filename characters
        import re
        prompt_summary = re.sub(r'[<>:"|?*]', '', prompt_summary)
        
        # Add description if provided
        if description:
            desc_text = f"_{description.replace(' ', '_')}"
            # Remove any invalid filename characters
            desc_text = re.sub(r'[<>:"/\\|?*]', '', desc_text)
        else:
            desc_text = ""
        
        # Create filename
        filename = f"{timestamp}_{prompt_summary}{desc_text}.png"
        
        # Return full path
        full_path = os.path.join(today_dir, filename)
        logger.info(f"Generated output path: {os.path.abspath(full_path)}")
        return full_path
    
    def save_image(self, image_data, prompt, description=None):
        """Save image data to file."""
        output_path = self.get_output_path(prompt, description)
        
        try:
            # Log image data type and size
            logger.info(f"Saving image data of type {type(image_data)} and size {len(image_data) if isinstance(image_data, bytes) else 'unknown'} bytes")
            
            # Normalize path for Windows
            output_path = os.path.normpath(output_path)
            logger.info(f"Normalized output path: {output_path}")
            
            # Ensure the directory exists
            dir_path = os.path.dirname(output_path)
            os.makedirs(dir_path, exist_ok=True)
            logger.info(f"Ensured directory exists: {dir_path}")
            
            # Check if the directory is writable
            if not os.access(dir_path, os.W_OK):
                logger.error(f"Directory is not writable: {os.path.abspath(dir_path)}")
                return None
            
            # Try to create a test file in the directory
            test_file = os.path.join(dir_path, ".test_write")
            try:
                with open(test_file, "wb") as f:
                    f.write(b"test")
                os.remove(test_file)
                logger.info(f"Successfully created and removed test file in {dir_path}")
            except Exception as e:
                logger.error(f"Failed to create test file in {dir_path}: {str(e)}")
                return None
            
            # Save the image with explicit mode
            logger.info(f"Attempting to save image to: {output_path}")
            with open(output_path, "wb") as f:
                if isinstance(image_data, bytes):
                    f.write(image_data)
                    f.flush()  # Force write to disk
                    os.fsync(f.fileno())  # Ensure data is written to disk
                else:
                    logger.error(f"Cannot save image data of type {type(image_data)}")
                    return None
            
            # Verify the file was created and has content
            if os.path.exists(output_path):
                file_size = os.path.getsize(output_path)
                if file_size > 0:
                    logger.info(f"Image saved to {os.path.abspath(output_path)} with size {file_size} bytes")
                    return output_path
                else:
                    logger.error(f"File was created but is empty: {os.path.abspath(output_path)}")
                    return None
            else:
                logger.error(f"File was not created: {os.path.abspath(output_path)}")
                return None
        except Exception as e:
            logger.error(f"Failed to save image: {str(e)}")
            # Log the full exception traceback
            import traceback
            logger.error(f"Exception traceback: {traceback.format_exc()}")
            return None 
