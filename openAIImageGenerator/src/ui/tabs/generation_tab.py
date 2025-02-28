"""Generation tab for creating new images."""

import tkinter as tk
from tkinter import ttk, messagebox
import logging
from typing import Callable, Dict, Any, Optional, List
from PIL import Image, ImageTk
import os

from ...utils.error_handler import handle_errors, ValidationError
from ..dialogs.template_dialog import TemplateDialog
from ..dialogs.variable_input_dialog import VariableInputDialog

logger = logging.getLogger(__name__)

class GenerationTab(ttk.Frame):
    """Tab for image generation interface."""
    
    def __init__(
        self,
        parent: ttk.Notebook,
        on_generate: Callable[[str, Dict[str, Any]], None],
        error_handler: Any,
        db_manager: Any = None
    ):
        """Initialize generation tab.
        
        Args:
            parent: Parent notebook widget
            on_generate: Callback for generation requests
            error_handler: Error handler instance
            db_manager: Database manager instance
        """
        super().__init__(parent)
        self.on_generate = on_generate
        self.error_handler = error_handler
        self.db_manager = db_manager
        
        # Initialize variables
        self.preview_image: Optional[ImageTk.PhotoImage] = None
        self.prompt_var = tk.StringVar()
        self.size_var = tk.StringVar(value="1024x1024")
        self.quality_var = tk.StringVar(value="standard")
        self.style_var = tk.StringVar(value="vivid")
        
        self._create_ui()
        logger.debug("Generation tab initialized")
    
    def _create_ui(self):
        """Create tab UI components."""
        # Main container with padding
        main_frame = ttk.Frame(self, padding="10")
        main_frame.pack(fill="both", expand=True)
        
        # Left side - Controls
        controls_frame = ttk.LabelFrame(
            main_frame,
            text="Generation Controls",
            padding="5"
        )
        controls_frame.pack(side="left", fill="both", expand=True)
        
        # Prompt input
        prompt_frame = ttk.Frame(controls_frame)
        prompt_frame.pack(fill="x", pady=5)
        
        prompt_header = ttk.Frame(prompt_frame)
        prompt_header.pack(fill="x")
        
        ttk.Label(
            prompt_header,
            text="Prompt:",
            font=("Arial", 10, "bold")
        ).pack(side="left")
        
        # Template buttons
        template_frame = ttk.Frame(prompt_header)
        template_frame.pack(side="right")
        
        ttk.Button(
            template_frame,
            text="Templates",
            command=self._show_templates
        ).pack(side="left", padx=2)
        
        ttk.Button(
            template_frame,
            text="Save as Template",
            command=self._save_as_template
        ).pack(side="left", padx=2)
        
        self.prompt_text = tk.Text(
            prompt_frame,
            height=5,
            wrap="word",
            font=("Arial", 10)
        )
        self.prompt_text.pack(fill="x", pady=2)
        
        # Settings frame
        settings_frame = ttk.LabelFrame(
            controls_frame,
            text="Settings",
            padding="5"
        )
        settings_frame.pack(fill="x", pady=10)
        
        # Size selection
        size_frame = ttk.Frame(settings_frame)
        size_frame.pack(fill="x", pady=2)
        
        ttk.Label(
            size_frame,
            text="Size:",
            width=10
        ).pack(side="left")
        
        sizes = ["1024x1024", "1792x1024", "1024x1792"]
        size_menu = ttk.OptionMenu(
            size_frame,
            self.size_var,
            sizes[0],
            *sizes
        )
        size_menu.pack(side="left", fill="x", expand=True)
        
        # Quality selection
        quality_frame = ttk.Frame(settings_frame)
        quality_frame.pack(fill="x", pady=2)
        
        ttk.Label(
            quality_frame,
            text="Quality:",
            width=10
        ).pack(side="left")
        
        qualities = ["standard", "hd"]
        quality_menu = ttk.OptionMenu(
            quality_frame,
            self.quality_var,
            qualities[0],
            *qualities
        )
        quality_menu.pack(side="left", fill="x", expand=True)
        
        # Style selection
        style_frame = ttk.Frame(settings_frame)
        style_frame.pack(fill="x", pady=2)
        
        ttk.Label(
            style_frame,
            text="Style:",
            width=10
        ).pack(side="left")
        
        styles = ["vivid", "natural"]
        style_menu = ttk.OptionMenu(
            style_frame,
            self.style_var,
            styles[0],
            *styles
        )
        style_menu.pack(side="left", fill="x", expand=True)
        
        # Generate button
        generate_button = ttk.Button(
            controls_frame,
            text="Generate Image",
            command=self._handle_generate,
            style="Primary.TButton"
        )
        generate_button.pack(fill="x", pady=10)
        
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
        
        # Add save and copy buttons
        self.save_button = ttk.Button(
            preview_controls,
            text="Save",
            command=self._save_image,
            state="disabled"
        )
        self.save_button.pack(side="right", padx=5)
        
        self.copy_button = ttk.Button(
            preview_controls,
            text="Copy",
            command=self._copy_to_clipboard,
            state="disabled"
        )
        self.copy_button.pack(side="right", padx=5)
        
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
        
        # Add placeholder image
        self._set_placeholder_preview()
    
    def _set_placeholder_preview(self):
        """Set placeholder preview image."""
        # Create a gray placeholder
        placeholder = Image.new('RGB', (512, 512), color='#f0f0f0')
        self.preview_image = ImageTk.PhotoImage(placeholder)
        
        # Clear canvas
        self.canvas.delete("all")
        
        # Add placeholder image
        self.canvas.create_image(
            0, 0,
            anchor="nw",
            image=self.preview_image
        )
        
        # Add text overlay
        self.canvas.create_text(
            256, 256,
            text="Generated image will appear here",
            fill="gray",
            font=("Arial", 12, "bold"),
            anchor="center"
        )
        
        # Configure canvas scrollregion
        self.canvas.config(scrollregion=self.canvas.bbox("all"))
    
    @handle_errors()
    def _handle_generate(self):
        """Handle generate button click."""
        # Get prompt text
        prompt = self.prompt_text.get("1.0", tk.END).strip()
        
        if not prompt:
            raise ValidationError("Please enter a prompt")
        
        try:
            # Get settings
            settings = {
                "size": self.size_var.get(),
                "quality": self.quality_var.get(),
                "style": self.style_var.get()
            }
            
            # Disable controls during generation
            self._set_controls_state("disabled")
            
            # Show generating message
            self.canvas.delete("all")
            self.canvas.create_text(
                256, 256,
                text="Generating...",
                fill="gray",
                font=("Arial", 14, "bold"),
                anchor="center"
            )
            
            # Call generation callback
            self.on_generate(prompt, settings)
            
        except Exception as e:
            # Re-enable controls on error
            self._set_controls_state("normal")
            raise
    
    def _set_controls_state(self, state: str):
        """Set state of all control widgets.
        
        Args:
            state: Widget state ('normal' or 'disabled')
        """
        self.prompt_text.config(state=state)
        for child in self.winfo_children():
            if isinstance(child, (ttk.Button, ttk.OptionMenu)):
                child.config(state=state)
    
    def set_preview_image(self, image_path: str = None, image: Image.Image = None):
        """Set the preview image from a file path or PIL Image."""
        if image_path and os.path.exists(image_path):
            self.current_image = Image.open(image_path)
            self.current_image_path = image_path
        elif image:
            self.current_image = image
            self.current_image_path = None
        else:
            self._set_placeholder_preview()
            return
            
        # Reset zoom level
        self.zoom_level = 1.0
        
        # Update the image display
        self._update_image()
        
        # Enable save and copy buttons
        self.save_button.config(state="normal")
        self.copy_button.config(state="normal")
        
        # Enable controls
        self._set_controls_state("normal")
    
    @handle_errors()
    def _show_templates(self):
        """Show template management dialog."""
        if not self.db_manager:
            messagebox.showerror(
                "Error",
                "Database manager not available."
            )
            return
        
        dialog = TemplateDialog(
            self.winfo_toplevel(),
            self.db_manager,
            self._use_template,
            self.error_handler
        )
        dialog.focus()
    
    @handle_errors()
    def _save_as_template(self):
        """Save current prompt as template."""
        if not self.db_manager:
            messagebox.showerror(
                "Error",
                "Database manager not available."
            )
            return
        
        # Get current prompt
        prompt_text = self.prompt_text.get("1.0", "end-1c").strip()
        
        if not prompt_text:
            messagebox.showinfo(
                "Info",
                "Please enter a prompt to save as template."
            )
            return
        
        # Extract variables
        from ...utils.template_utils import TemplateProcessor
        processor = TemplateProcessor()
        variables = processor.extract_variables(prompt_text)
        
        # Save template
        try:
            template_id = self.db_manager.add_template(prompt_text, variables)
            
            if template_id:
                messagebox.showinfo(
                    "Success",
                    "Prompt saved as template successfully."
                )
            else:
                raise ValidationError("Failed to save template")
                
        except Exception as e:
            logger.error(f"Failed to save template: {str(e)}")
            messagebox.showerror(
                "Error",
                f"Failed to save template: {str(e)}"
            )
    
    @handle_errors()
    def _use_template(self, template_text: str, variables: List[str]):
        """Use selected template.
        
        Args:
            template_text: Template text
            variables: List of variable names
        """
        if not variables:
            # No variables, use template directly
            self.prompt_text.delete("1.0", tk.END)
            self.prompt_text.insert("1.0", template_text)
            return
        
        # Show variable input dialog
        dialog = VariableInputDialog(
            self.winfo_toplevel(),
            template_text,
            variables,
            self.db_manager,
            self._set_processed_template,
            self.error_handler
        )
        dialog.focus()
    
    def _set_processed_template(self, processed_text: str):
        """Set processed template as prompt.
        
        Args:
            processed_text: Processed template text
        """
        self.prompt_text.delete("1.0", tk.END)
        self.prompt_text.insert("1.0", processed_text)
    
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
    
    @handle_errors()
    def _save_image(self):
        """Save the current image to a file."""
        if not hasattr(self, 'current_image') or self.current_image is None:
            return
            
        # Get prompt text for filename
        prompt = self.prompt_text.get("1.0", tk.END).strip()
        
        # If we already have a path, use that
        if hasattr(self, 'current_image_path') and self.current_image_path:
            messagebox.showinfo(
                "Image Saved",
                f"Image already saved at:\n{self.current_image_path}"
            )
            return
            
        # Get save location from user
        from tkinter import filedialog
        file_path = filedialog.asksaveasfilename(
            defaultextension=".png",
            filetypes=[
                ("PNG files", "*.png"),
                ("JPEG files", "*.jpg"),
                ("All files", "*.*")
            ],
            title="Save Image As"
        )
        
        if file_path:
            try:
                self.current_image.save(file_path)
                self.current_image_path = file_path
                messagebox.showinfo(
                    "Success",
                    f"Image saved to:\n{file_path}"
                )
                logger.info(f"Image saved to: {file_path}")
            except Exception as e:
                logger.error(f"Failed to save image: {str(e)}")
                messagebox.showerror(
                    "Error",
                    f"Failed to save image: {str(e)}"
                )
    
    @handle_errors()
    def _copy_to_clipboard(self):
        """Copy the current image to clipboard."""
        if not hasattr(self, 'current_image') or self.current_image is None:
            return
            
        try:
            import io
            import pyperclip
            from PIL import ImageGrab
            
            # Create a temporary file
            import tempfile
            import os
            
            with tempfile.NamedTemporaryFile(delete=False, suffix='.png') as temp_file:
                temp_filename = temp_file.name
                
            # Save image to temporary file
            self.current_image.save(temp_filename, format='PNG')
            
            # Use platform-specific methods to copy to clipboard
            import platform
            system = platform.system()
            
            if system == 'Windows':
                # Windows approach
                import subprocess
                subprocess.run(['powershell', '-command', 
                               f"Add-Type -AssemblyName System.Windows.Forms; " +
                               f"[System.Windows.Forms.Clipboard]::SetImage(" +
                               f"[System.Drawing.Image]::FromFile('{temp_filename}'))"])
            elif system == 'Darwin':  # macOS
                subprocess.run(['osascript', '-e', 
                               f'set the clipboard to (read (POSIX file "{temp_filename}") as JPEG picture)'])
            else:  # Linux
                subprocess.run(['xclip', '-selection', 'clipboard', '-t', 'image/png', '-i', temp_filename])
            
            # Clean up the temporary file
            try:
                os.unlink(temp_filename)
            except:
                pass
                
            messagebox.showinfo(
                "Success",
                "Image copied to clipboard"
            )
            logger.info("Image copied to clipboard")
        except Exception as e:
            logger.error(f"Failed to copy image: {str(e)}")
            messagebox.showerror(
                "Error",
                f"Failed to copy to clipboard: {str(e)}"
            )
    
    def _update_image(self):
        """Update the displayed image based on current zoom level."""
        if not hasattr(self, 'current_image') or self.current_image is None:
            return
            
        # Clear canvas
        self.canvas.delete("all")
        
        # Calculate new size based on zoom
        width = int(self.current_image.width * self.zoom_level)
        height = int(self.current_image.height * self.zoom_level)
        
        # Resize image
        if self.zoom_level == 1.0:
            display_image = self.current_image.copy()
        else:
            display_image = self.current_image.resize((width, height), Image.Resampling.LANCZOS)
        
        # Convert to PhotoImage and store reference
        self.preview_image = ImageTk.PhotoImage(display_image)
        
        # Add image to canvas
        self.canvas_image_id = self.canvas.create_image(
            0, 0,
            anchor="nw",
            image=self.preview_image,
            tags="image"
        )
        
        # Update canvas scroll region
        self.canvas.config(scrollregion=self.canvas.bbox("all"))
        
        logger.debug(f"Image updated with zoom level: {self.zoom_level:.2f}")
