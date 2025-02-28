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
        
        # Table container to hold treeview and pagination
        table_container = ttk.Frame(table_frame)
        table_container.pack(fill="both", expand=True)
        
        # Create treeview
        columns = (
            "date", "prompt", "size", "quality",
            "style", "rating", "tokens"
        )
        self.tree = ttk.Treeview(
            table_container,
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
            table_container,
            orient="vertical",
            command=self.tree.yview
        )
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        # Pack table components
        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Bind selection event
        self.tree.bind("<<TreeviewSelect>>", self._on_select)
        
        # Pagination controls below the table
        pagination_frame = ttk.Frame(table_frame)
        pagination_frame.pack(fill="x", pady=(10, 5), side="bottom")
        
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
        
        # Right side - Preview
        preview_frame = ttk.LabelFrame(
            main_frame,
            text="Preview",
            padding="5"
        )
        preview_frame.pack(side="right", fill="both", expand=True, padx=(10, 0))
        
        # Preview image with zoom controls
        preview_controls = ttk.Frame(preview_frame)
        preview_controls.pack(fill="x", pady=(0, 5))
        
        ttk.Button(
            preview_controls,
            text="Zoom In",
            command=self._zoom_in
        ).pack(side="left", padx=5)
        
        ttk.Button(
            preview_controls,
            text="Zoom Out",
            command=self._zoom_out
        ).pack(side="left", padx=5)
        
        ttk.Button(
            preview_controls,
            text="Fit",
            command=self._zoom_fit
        ).pack(side="left", padx=5)
        
        # Create canvas for image display with scrollbars
        canvas_frame = ttk.Frame(preview_frame)
        canvas_frame.pack(fill="both", expand=True)
        
        self.canvas = tk.Canvas(
            canvas_frame,
            bg="#f0f0f0",
            highlightthickness=0
        )
        
        h_scrollbar = ttk.Scrollbar(
            canvas_frame,
            orient="horizontal",
            command=self.canvas.xview
        )
        v_scrollbar = ttk.Scrollbar(
            canvas_frame,
            orient="vertical",
            command=self.canvas.yview
        )
        
        self.canvas.config(
            xscrollcommand=h_scrollbar.set,
            yscrollcommand=v_scrollbar.set
        )
        
        # Pack canvas and scrollbars
        self.canvas.grid(row=0, column=0, sticky="nsew")
        h_scrollbar.grid(row=1, column=0, sticky="ew")
        v_scrollbar.grid(row=0, column=1, sticky="ns")
        
        # Configure grid weights
        canvas_frame.grid_rowconfigure(0, weight=1)
        canvas_frame.grid_columnconfigure(0, weight=1)
        
        # Initialize zoom level
        self.zoom_level = 1.0
        self.current_image = None
        self.canvas_image_id = None
        
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
        
        # Set placeholder
        self._set_placeholder_preview()
    
    def _set_placeholder_preview(self):
        """Set placeholder preview image."""
        placeholder = Image.new('RGB', (512, 512), color='#f0f0f0')
        self.current_image = placeholder
        self.preview_image = ImageTk.PhotoImage(placeholder)
        
        # Clear any existing image
        self.canvas.delete("all")
        
        # Create text on canvas
        self.canvas.create_text(
            256, 256,
            text="Select an image to preview",
            font=("Arial", 12),
            fill="#666666"
        )
        
        # Create image on canvas
        self.canvas_image_id = self.canvas.create_image(
            0, 0,
            anchor="nw",
            image=self.preview_image
        )
        
        # Reset zoom level
        self.zoom_level = 1.0
        
        # Configure canvas scrollregion
        self.canvas.config(scrollregion=self.canvas.bbox("all"))
    
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
                # Parse the date string into a datetime object
                try:
                    date_obj = datetime.fromisoformat(gen.generation_date)
                    date_str = date_obj.strftime("%Y-%m-%d %H:%M:%S")
                except (ValueError, TypeError):
                    date_str = gen.generation_date
                
                # Extract parameters
                params = gen.parameters or {}
                size = params.get("size", "")
                quality = params.get("quality", "")
                style = params.get("style", "")
                
                self.tree.insert(
                    "",
                    "end",
                    values=(
                        date_str,
                        gen.prompt_text[:50] + "..." if len(gen.prompt_text) > 50 else gen.prompt_text,
                        size,
                        quality,
                        style,
                        gen.user_rating or "Not rated",
                        gen.token_usage
                    ),
                    tags=(str(gen.id),)
                )
            
            # Update pagination
            self._update_pagination()
            
        except Exception as e:
            logger.error(f"Failed to load history: {str(e)}")
            raise DatabaseError("Failed to load generation history")
    
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
                # Load image
                image_path = self.file_manager.get_image_path(generation.image_path)
                image = Image.open(image_path)
                
                # Store original image
                self.current_image = image
                
                # Reset zoom level
                self.zoom_level = 1.0
                
                # Update image display
                self._update_image()
                
                # Update rating
                self.rating_var.set(str(generation.user_rating))
                
                # Display usage statistics
                self._display_usage_statistics(generation)
                
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
            
            # Delete from database and get image path
            image_path = self.db_manager.delete_generation(gen_id)
            
            # Delete the image file if path was returned
            if image_path:
                try:
                    self.file_manager.delete_image(image_path)
                    logger.info(f"Deleted image file: {image_path}")
                except Exception as e:
                    logger.warning(f"Could not delete image file: {str(e)}")
            
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

    def _zoom_in(self):
        """Zoom in on the image."""
        self.zoom_level *= 1.2
        self._update_image()

    def _zoom_out(self):
        """Zoom out on the image."""
        self.zoom_level /= 1.2
        self._update_image()

    def _zoom_fit(self):
        """Fit the image to the canvas."""
        self.zoom_level = 1.0
        self._update_image()

    def _update_image(self):
        """Update the displayed image based on zoom level."""
        if not self.current_image:
            return
            
        # Calculate new dimensions
        width, height = self.current_image.size
        new_width = int(width * self.zoom_level)
        new_height = int(height * self.zoom_level)
        
        # Resize image
        resized = self.current_image.resize((new_width, new_height), Image.LANCZOS)
        self.preview_image = ImageTk.PhotoImage(resized)
        
        # Clear canvas and display image
        self.canvas.delete("all")
        self.canvas_image_id = self.canvas.create_image(
            0, 0,
            anchor="nw",
            image=self.preview_image
        )
        
        # Configure canvas scroll region
        self.canvas.config(scrollregion=(0, 0, new_width, new_height))
        
        # Re-display usage statistics if we have a selected generation
        selection = self.tree.selection()
        if selection:
            try:
                gen_id = int(self.tree.item(selection[0])["tags"][0])
                generation = self.db_manager.get_generation(gen_id)
                if generation:
                    self._display_usage_statistics(generation)
            except Exception as e:
                logger.error(f"Failed to redisplay usage statistics: {str(e)}")

    def _display_usage_statistics(self, generation):
        """Display usage statistics for the selected generation.
        
        Args:
            generation: Generation object with usage data
        """
        if not generation:
            return
            
        # Clear any existing usage text
        self.canvas.delete("usage_stats")
        
        # Format usage information
        stats_text = "Usage Statistics:\n"
        
        # Add token usage
        if generation.token_usage:
            stats_text += f"Tokens: {generation.token_usage}\n"
        
        # Add parameters
        if generation.parameters:
            params = generation.parameters
            if "size" in params:
                stats_text += f"Size: {params['size']}\n"
            if "quality" in params:
                stats_text += f"Quality: {params['quality']}\n"
            if "style" in params:
                stats_text += f"Style: {params['style']}\n"
        
        # Add usage text to canvas
        self.canvas.create_text(
            10, 10,  # Position in top-left corner
            text=stats_text,
            fill="black",
            font=("Arial", 9),
            anchor="nw",
            tags="usage_stats"
        )
        
        logger.debug(f"Displayed usage statistics for generation {generation.id}")

    def _set_image(self, image):
        """Set the image to be displayed in the canvas."""
        self.current_image = image
        self._update_image()
