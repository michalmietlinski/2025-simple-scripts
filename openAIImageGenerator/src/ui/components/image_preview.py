"""Reusable image preview component."""

import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk
import logging

logger = logging.getLogger(__name__)

class ImagePreview(ttk.Frame):
    """A frame for displaying an image with optional controls."""
    
    def __init__(
        self,
        container,
        image: Image.Image = None,
        max_size: tuple = (512, 512),
        *args,
        **kwargs
    ):
        """Initialize image preview.
        
        Args:
            container: Parent widget
            image: PIL Image to display
            max_size: Maximum (width, height) for the image
            *args: Additional positional arguments for ttk.Frame
            **kwargs: Additional keyword arguments for ttk.Frame
        """
        super().__init__(container, *args, **kwargs)
        
        self.max_size = max_size
        self.image = None
        self.photo = None
        
        # Create image label
        self.image_label = ttk.Label(self)
        self.image_label.pack(expand=True, fill="both")
        
        if image:
            self.set_image(image)
    
    def set_image(self, image: Image.Image):
        """Set and display a new image.
        
        Args:
            image: PIL Image to display
        """
        try:
            # Store original image
            self.image = image
            
            # Calculate new size maintaining aspect ratio
            width, height = image.size
            scale = min(
                self.max_size[0] / width,
                self.max_size[1] / height
            )
            new_size = (
                int(width * scale),
                int(height * scale)
            )
            
            # Resize image
            resized = image.resize(new_size, Image.Resampling.LANCZOS)
            
            # Convert to PhotoImage
            self.photo = ImageTk.PhotoImage(resized)
            
            # Update label
            self.image_label.configure(image=self.photo)
            
        except Exception as e:
            logger.error(f"Failed to set image: {str(e)}")
            # Set empty image
            self.image_label.configure(image="") 
