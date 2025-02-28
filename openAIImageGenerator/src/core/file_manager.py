"""File manager for handling image storage and organization."""

import os
import re
import logging
import shutil
from datetime import datetime
from pathlib import Path
from typing import Optional, Union
from PIL import Image
from io import BytesIO

logger = logging.getLogger(__name__)

class FileManager:
    """Manages file operations for saving and organizing generated images."""
    
    def __init__(self, output_dir: Union[str, Path]):
        """Initialize the file manager.
        
        Args:
            output_dir: Base directory for storing generated images
        """
        self.output_dir = Path(output_dir)
        self.ensure_directories()
        self._verify_permissions()
        logger.info(f"File manager initialized with output directory: {self.output_dir.absolute()}")
    
    def _verify_permissions(self):
        """Verify write permissions in output directory."""
        if not os.access(self.output_dir, os.W_OK):
            logger.error(f"Output directory is not writable: {self.output_dir}")
            try:
                test_file = self.output_dir / ".write_test"
                test_file.write_text("test")
                test_file.unlink()
                logger.info("Successfully verified write permissions")
            except Exception as e:
                logger.error(f"Failed to verify write permissions: {str(e)}")
                raise PermissionError(f"Output directory is not writable: {self.output_dir}")
    
    def ensure_directories(self) -> Path:
        """Create necessary directories if they don't exist.
        
        Returns:
            Path: Path to today's output directory
        """
        # Create base directory
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Create date-based directory
        today_dir = self.output_dir / datetime.now().strftime("%Y-%m-%d")
        today_dir.mkdir(exist_ok=True)
        
        logger.info(f"Ensured output directory exists: {today_dir.absolute()}")
        return today_dir
    
    def _sanitize_filename(self, text: str) -> str:
        """Create a safe filename from text.
        
        Args:
            text: Text to convert to filename
            
        Returns:
            str: Sanitized filename
        """
        # Replace spaces and invalid characters
        text = text.replace(" ", "_")
        text = re.sub(r'[<>:"/\\|?*]', '', text)
        return text[:50]  # Limit length
    
    def get_output_path(
        self,
        prompt: str,
        description: Optional[str] = None,
        prefix: Optional[str] = None
    ) -> Path:
        """Generate a filename for a new image.
        
        Args:
            prompt: Generation prompt
            description: Optional description
            prefix: Optional filename prefix
            
        Returns:
            Path: Full path for the new image
        """
        today_dir = self.ensure_directories()
        
        # Create components
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        prompt_part = self._sanitize_filename(prompt)
        desc_part = f"_{self._sanitize_filename(description)}" if description else ""
        prefix_part = f"{prefix}_" if prefix else ""
        
        # Combine into filename
        filename = f"{prefix_part}{timestamp}_{prompt_part}{desc_part}.png"
        
        return today_dir / filename
    
    def save_image(
        self,
        image_data: Union[bytes, Image.Image, BytesIO],
        prompt: str,
        description: Optional[str] = None,
        prefix: Optional[str] = None
    ) -> Optional[Path]:
        """Save image data to file.
        
        Args:
            image_data: Image data to save (bytes, PIL Image, or BytesIO)
            prompt: Generation prompt
            description: Optional description
            prefix: Optional filename prefix
            
        Returns:
            Optional[Path]: Path to saved image if successful, None otherwise
        """
        output_path = self.get_output_path(prompt, description, prefix)
        
        try:
            # Ensure parent directory exists
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Convert image data to bytes if needed
            if isinstance(image_data, Image.Image):
                buffer = BytesIO()
                image_data.save(buffer, format="PNG")
                image_data = buffer.getvalue()
            elif isinstance(image_data, BytesIO):
                image_data = image_data.getvalue()
            
            # Save image
            output_path.write_bytes(image_data)
            
            # Verify file was saved correctly
            if output_path.exists() and output_path.stat().st_size > 0:
                logger.info(f"Image saved successfully: {output_path.absolute()}")
                return output_path
            else:
                logger.error(f"Failed to save image (empty or missing file): {output_path}")
                return None
                
        except Exception as e:
            logger.error(f"Failed to save image: {str(e)}")
            if output_path.exists():
                try:
                    output_path.unlink()
                    logger.info(f"Cleaned up failed save attempt: {output_path}")
                except Exception as cleanup_error:
                    logger.error(f"Failed to clean up failed save: {str(cleanup_error)}")
            return None
    
    def backup_image(self, image_path: Union[str, Path], backup_dir: Optional[Union[str, Path]] = None) -> Optional[Path]:
        """Create a backup copy of an image.
        
        Args:
            image_path: Path to image to backup
            backup_dir: Optional custom backup directory
            
        Returns:
            Optional[Path]: Path to backup if successful, None otherwise
        """
        try:
            image_path = Path(image_path)
            if not image_path.exists():
                logger.error(f"Source image does not exist: {image_path}")
                return None
            
            # Use default backup directory if none specified
            if backup_dir is None:
                backup_dir = self.output_dir / "backups" / datetime.now().strftime("%Y-%m-%d")
            else:
                backup_dir = Path(backup_dir)
            
            # Create backup directory
            backup_dir.mkdir(parents=True, exist_ok=True)
            
            # Create backup path with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = backup_dir / f"{timestamp}_{image_path.name}"
            
            # Copy file
            shutil.copy2(image_path, backup_path)
            
            logger.info(f"Created backup: {backup_path.absolute()}")
            return backup_path
            
        except Exception as e:
            logger.error(f"Failed to create backup: {str(e)}")
            return None
    
    def cleanup_old_files(self, days: int = 30) -> bool:
        """Remove files older than specified days.
        
        Args:
            days: Number of days to keep files
            
        Returns:
            bool: True if cleanup was successful
        """
        try:
            cutoff = datetime.now().timestamp() - (days * 24 * 60 * 60)
            
            for path in self.output_dir.rglob("*"):
                if path.is_file() and path.stat().st_mtime < cutoff:
                    try:
                        path.unlink()
                        logger.info(f"Removed old file: {path}")
                    except Exception as e:
                        logger.error(f"Failed to remove file {path}: {str(e)}")
            
            # Remove empty directories
            for path in sorted(self.output_dir.rglob("*"), reverse=True):
                if path.is_dir() and not any(path.iterdir()):
                    try:
                        path.rmdir()
                        logger.info(f"Removed empty directory: {path}")
                    except Exception as e:
                        logger.error(f"Failed to remove directory {path}: {str(e)}")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to cleanup old files: {str(e)}")
            return False

    def get_image_path(self, relative_path: str) -> str:
        """Get absolute path for a stored image.
        
        Args:
            relative_path: Path relative to output directory
            
        Returns:
            Absolute path to the image
        """
        return os.path.join(self.output_dir, relative_path)
    
    def delete_image(self, relative_path: str):
        """Delete an image file.
        
        Args:
            relative_path: Path relative to output directory
        """
        try:
            abs_path = self.get_image_path(relative_path)
            if os.path.exists(abs_path):
                os.remove(abs_path)
                logger.info(f"Deleted image: {relative_path}")
                
                # Try to remove empty parent directory
                parent_dir = os.path.dirname(abs_path)
                if not os.listdir(parent_dir):
                    os.rmdir(parent_dir)
                    logger.info(f"Removed empty directory: {parent_dir}")
        except Exception as e:
            logger.error(f"Failed to delete image: {str(e)}")
            raise 
