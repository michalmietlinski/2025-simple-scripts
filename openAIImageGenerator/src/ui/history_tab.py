"""History tab for viewing past generations."""

import tkinter as tk
from tkinter import ttk
import logging
from typing import List, Dict, Any, Callable
from datetime import datetime
from .components.scrollable_frame import ScrollableFrame
from .components.image_preview import ImagePreview

logger = logging.getLogger(__name__)

class HistoryTab(ttk.Frame):
    """Tab for viewing generation history."""
    
    def __init__(
        self,
        container,
        on_load_history: Callable[[], List[Dict[str, Any]]],
        on_load_image: Callable[[str], Any],
        *args,
        **kwargs
    ):
        """Initialize history tab.
        
        Args:
            container: Parent widget
            on_load_history: Callback to load generation history
            on_load_image: Callback to load image by path
            *args: Additional positional arguments for ttk.Frame
            **kwargs: Additional keyword arguments for ttk.Frame
        """
        super().__init__(container, *args, **kwargs)
        self.on_load_history = on_load_history
        self.on_load_image = on_load_image
        
        self._init_ui()
    
    def _init_ui(self):
        """Initialize UI components."""
        # Create toolbar
        toolbar = ttk.Frame(self)
        toolbar.pack(fill="x", padx=5, pady=5)
        
        refresh_btn = ttk.Button(
            toolbar,
            text="Refresh",
            command=self.refresh_history
        )
        refresh_btn.pack(side="left")
        
        # Create scrollable container
        self.history_container = ScrollableFrame(self)
        self.history_container.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Load initial history
        self.refresh_history()
    
    def refresh_history(self):
        """Reload and display generation history."""
        try:
            # Clear existing history
            for widget in self.history_container.scrollable_frame.winfo_children():
                widget.destroy()
            
            # Load history
            history = self.on_load_history()
            
            # Create entry for each generation
            for entry in history:
                self._create_history_entry(entry)
                
        except Exception as e:
            logger.error(f"Failed to load history: {str(e)}")
    
    def _create_history_entry(self, entry: Dict[str, Any]):
        """Create UI elements for a history entry.
        
        Args:
            entry: Dictionary containing generation data
        """
        # Create frame for entry
        entry_frame = ttk.Frame(self.history_container.scrollable_frame)
        entry_frame.pack(fill="x", padx=5, pady=5)
        
        # Add separator above entry
        ttk.Separator(self.history_container.scrollable_frame).pack(
            fill="x",
            padx=5,
            pady=(0, 5)
        )
        
        # Create info frame
        info_frame = ttk.Frame(entry_frame)
        info_frame.pack(fill="x")
        
        # Add timestamp
        timestamp = datetime.fromisoformat(entry["generation_date"])
        date_label = ttk.Label(
            info_frame,
            text=timestamp.strftime("%Y-%m-%d %H:%M:%S")
        )
        date_label.pack(anchor="w")
        
        # Add prompt
        prompt_frame = ttk.LabelFrame(entry_frame, text="Prompt")
        prompt_frame.pack(fill="x", pady=5)
        
        prompt_text = tk.Text(
            prompt_frame,
            height=2,
            wrap="word",
            state="disabled"
        )
        prompt_text.pack(fill="x", padx=5, pady=5)
        
        # Insert prompt text
        prompt_text.configure(state="normal")
        prompt_text.insert("1.0", entry["prompt_text"])
        prompt_text.configure(state="disabled")
        
        # Add settings if available
        if entry.get("settings"):
            settings_frame = ttk.LabelFrame(entry_frame, text="Settings")
            settings_frame.pack(fill="x", pady=5)
            
            settings_text = ttk.Label(
                settings_frame,
                text=str(entry["settings"])
            )
            settings_text.pack(padx=5, pady=5)
        
        # Add image preview
        try:
            image = self.on_load_image(entry["image_path"])
            if image:
                preview = ImagePreview(
                    entry_frame,
                    image=image,
                    max_size=(256, 256)
                )
                preview.pack(pady=5)
        except Exception as e:
            logger.error(f"Failed to load image preview: {str(e)}")
            error_label = ttk.Label(
                entry_frame,
                text="Failed to load image preview",
                foreground="red"
            )
            error_label.pack(pady=5)
