"""History tab for viewing past generations."""

import tkinter as tk
from tkinter import ttk, messagebox
import logging
from typing import List, Optional, Dict, Any
from datetime import datetime
from PIL import Image, ImageTk
from pathlib import Path

from ...core.data_models import Generation
from ...core.database import DatabaseManager
from ...core.file_manager import FileManager
from ...utils.error_handler import handle_errors, DatabaseError, FileError

logger = logging.getLogger(__name__)

class HistoryTab(ttk.Frame):
    """Tab for viewing generation history."""
    
    def __init__(
        self,
        parent: ttk.Notebook,
        db_manager: DatabaseManager,
        file_manager: FileManager,
        error_handler: Any,
        page_size: int = 10
    ):
        """Initialize history tab.
        
        Args:
            parent: Parent notebook widget
            db_manager: Database manager instance
            file_manager: File manager instance
            error_handler: Error handler instance
            page_size: Number of items per page
        """
        super().__init__(parent)
        self.db_manager = db_manager
        self.file_manager = file_manager
        self.error_handler = error_handler
        self.page_size = page_size
        self.current_page = 0  # 0-based pagination
        self.total_items = 0
        
        self._create_ui()
        self._load_history()
        
        logger.debug("History tab initialized")
    
    def _create_ui(self):
        """Create tab UI components."""
        # Main container
        main_frame = ttk.Frame(self, padding="10")
        main_frame.pack(fill="both", expand=True)
        
        # Left side - History table
        table_frame = ttk.LabelFrame(
            main_frame,
            text="Generation History",
            padding="5"
        )
        table_frame.pack(side="left", fill="both", expand=True)
        
        # Create treeview
        columns = (
            "date", "prompt", "size", "quality",
            "style", "rating", "tokens"
        )
        self.tree = ttk.Treeview(
            table_frame,
            columns=columns,
            show="headings",
            selectmode="browse"
        )
        
        # Configure columns
        self.tree.heading("date", text="Date")
        self.tree.heading("prompt", text="Prompt")
        self.tree.heading("size", text="Size")
        self.tree.heading("quality", text="Quality")
        self.tree.heading("style", text="Style")
        self.tree.heading("rating", text="Rating")
        self.tree.heading("tokens", text="Tokens")
        
        self.tree.column("date", width=150)
        self.tree.column("prompt", width=300)
        self.tree.column("size", width=100)
        self.tree.column("quality", width=80)
        self.tree.column("style", width=80)
        self.tree.column("rating", width=80)
        self.tree.column("tokens", width=80)
        
        # Add scrollbar
        scrollbar = ttk.Scrollbar(
            table_frame,
            orient="vertical",
            command=self.tree.yview
        )
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        # Pack table components
        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Bind selection event
        self.tree.bind("<<TreeviewSelect>>", self._on_select)
        
        # Right side - Preview
        preview_frame = ttk.LabelFrame(
            main_frame,
            text="Preview",
            padding="5"
        )
        preview_frame.pack(side="right", fill="both", expand=True, padx=(10, 0))
        
        # Preview image
        self.preview_label = ttk.Label(preview_frame)
        self.preview_label.pack(fill="both", expand=True)
        
        # Details section
        details_frame = ttk.Frame(preview_frame)
        details_frame.pack(fill="x", pady=(10, 0))
        
        # Rating controls
        rating_frame = ttk.Frame(details_frame)
        rating_frame.pack(fill="x", pady=5)
        
        ttk.Label(
            rating_frame,
            text="Rating:",
            font=("Arial", 10, "bold")
        ).pack(side="left")
        
        self.rating_var = tk.StringVar(value="0")
        for i in range(1, 6):
            ttk.Radiobutton(
                rating_frame,
                text=str(i),
                value=str(i),
                variable=self.rating_var,
                command=self._update_rating
            ).pack(side="left", padx=5)
        
        # Action buttons
        button_frame = ttk.Frame(details_frame)
        button_frame.pack(fill="x", pady=5)
        
        ttk.Button(
            button_frame,
            text="Save Copy",
            command=self._save_copy
        ).pack(side="left", padx=5)
        
        ttk.Button(
            button_frame,
            text="Delete",
            command=self._delete_generation,
            style="Danger.TButton"
        ).pack(side="left", padx=5)
        
        # Pagination
        pagination_frame = ttk.Frame(table_frame)
        pagination_frame.pack(fill="x", pady=(10, 0))
        
        self.prev_button = ttk.Button(
            pagination_frame,
            text="Previous",
            command=self._prev_page
        )
        self.prev_button.pack(side="left")
        
        self.page_info = ttk.Label(
            pagination_frame,
            text="Page 1"
        )
        self.page_info.pack(side="left", padx=10)
        
        self.next_button = ttk.Button(
            pagination_frame,
            text="Next",
            command=self._next_page
        )
        self.next_button.pack(side="left")
        
        # Set placeholder
        self._set_placeholder_preview()
    
    def _set_placeholder_preview(self):
        """Set placeholder preview image."""
        placeholder = Image.new('RGB', (512, 512), color='#f0f0f0')
        self.preview_image = ImageTk.PhotoImage(placeholder)
        self.preview_label.config(
            image=self.preview_image,
            text="Select an image to preview",
            compound="center"
        )
    
    @handle_errors()
    def _load_history(self):
        """Load generation history."""
        try:
            # Get total count
            total = self.db_manager.get_generation_count()
            self.total_items = total
            
            # Get page of generations
            generations = self.db_manager.get_generations(
                offset=(self.current_page) * self.page_size,
                limit=self.page_size
            )
            
            # Update tree
            self.tree.delete(*self.tree.get_children())
            for gen in generations:
                self.tree.insert(
                    "",
                    "end",
                    values=(
                        gen.created_at.strftime("%Y-%m-%d %H:%M:%S"),
                        gen.prompt_text[:50] + "..." if len(gen.prompt_text) > 50 else gen.prompt_text,
                        gen.rating or "Not rated"
                    ),
                    tags=(str(gen.id),)
                )
            
            # Update pagination
            self._update_pagination()
            
        except Exception as e:
            logger.error(f"Failed to load history: {str(e)}")
            raise DatabaseError("Failed to load generation history")
    
            messagebox.showerror(
                "Error",
                "Failed to load generation history."
            )
    
    def _on_select(self, event):
        """Handle generation selection."""
        selection = self.tree.selection()
        if not selection:
            return
        
        try:
            # Get generation ID from tags
            gen_id = int(self.tree.item(selection[0])["tags"][0])
            generation = self.db_manager.get_generation(gen_id)
            
            if generation and generation.image_path:
                # Load and display image
                image_path = self.file_manager.get_image_path(generation.image_path)
                image = Image.open(image_path)
                
                # Resize for preview
                preview_size = (512, 512)
                image.thumbnail(preview_size, Image.Resampling.LANCZOS)
                
                # Update preview
                self.preview_image = ImageTk.PhotoImage(image)
                self.preview_label.config(
                    image=self.preview_image,
                    text=""
                )
                
                # Update rating
                self.rating_var.set(str(generation.user_rating))
                
        except Exception as e:
            logger.error(f"Failed to load preview: {str(e)}")
            self._set_placeholder_preview()
    
    def _update_rating(self):
        """Update generation rating."""
        selection = self.tree.selection()
        if not selection:
            return
        
        try:
            gen_id = int(self.tree.item(selection[0])["tags"][0])
            rating = int(self.rating_var.get())
            
            # Update in database
            self.db_manager.update_generation_rating(gen_id, rating)
            
            # Refresh display
            self._load_history()
            
        except Exception as e:
            logger.error(f"Failed to update rating: {str(e)}")
            messagebox.showerror(
                "Error",
                "Failed to update rating."
            )
    
    def _save_copy(self):
        """Save a copy of the selected image."""
        selection = self.tree.selection()
        if not selection:
            return
        
        try:
            gen_id = int(self.tree.item(selection[0])["tags"][0])
            generation = self.db_manager.get_generation(gen_id)
            
            if generation and generation.image_path:
                # Create backup
                backup_path = self.file_manager.backup_image(
                    self.file_manager.get_image_path(generation.image_path)
                )
                
                if backup_path:
                    messagebox.showinfo(
                        "Success",
                        f"Image saved to: {backup_path}"
                    )
                else:
                    raise Exception("Failed to create backup")
                    
        except Exception as e:
            logger.error(f"Failed to save copy: {str(e)}")
            messagebox.showerror(
                "Error",
                "Failed to save image copy."
            )
    
    def _delete_generation(self):
        """Delete selected generation."""
        selection = self.tree.selection()
        if not selection:
            return
        
        if not messagebox.askyesno(
            "Confirm Delete",
            "Are you sure you want to delete this generation?"
        ):
            return
        
        try:
            gen_id = int(self.tree.item(selection[0])["tags"][0])
            
            # Delete from database and file system
            self.db_manager.delete_generation(gen_id)
            
            # Refresh display
            self._load_history()
            self._set_placeholder_preview()
            
        except Exception as e:
            logger.error(f"Failed to delete generation: {str(e)}")
            messagebox.showerror(
                "Error",
                "Failed to delete generation."
            )
    
    def _prev_page(self):
        """Go to previous page."""
        if self.current_page > 0:
            self.current_page -= 1
            self._load_history()
    
    def _next_page(self):
        """Go to next page."""
        if (self.current_page + 1) * self.page_size < self.total_items:
            self.current_page += 1
            self._load_history()

    def _update_pagination(self):
        """Update pagination controls and info."""
        total_pages = (self.total_items + self.page_size - 1) // self.page_size
        
        # Update page info
        self.page_info.config(
            text=f"Page {self.current_page + 1} of {total_pages} "
            f"({self.total_items} total)"
        )
        
        # Update button states
        self.prev_button.config(
            state="normal" if self.current_page > 0 else "disabled"
        )
        self.next_button.config(
            state="normal" 
            if (self.current_page + 1) * self.page_size < self.total_items 
            else "disabled"
        ) 
