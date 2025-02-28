"""Generation tab for creating new images."""

import tkinter as tk
from tkinter import ttk, messagebox
import logging
from typing import Callable, Dict, Any, Optional, List
from PIL import Image, ImageTk

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
        
        self.preview_label = ttk.Label(preview_frame)
        self.preview_label.pack(fill="both", expand=True)
        
        # Add placeholder image
        self._set_placeholder_preview()
    
    def _set_placeholder_preview(self):
        """Set placeholder preview image."""
        # Create a gray placeholder
        placeholder = Image.new('RGB', (512, 512), color='#f0f0f0')
        self.preview_image = ImageTk.PhotoImage(placeholder)
        self.preview_label.config(image=self.preview_image)
        
        # Add text overlay
        self.preview_label.config(
            text="Generated image will appear here",
            compound="center"
        )
    
    @handle_errors()
    def _handle_generate(self):
        """Handle generate button click."""
        prompt = self.prompt_text.get("1.0", "end-1c").strip()
        
        if not prompt:
            raise ValidationError("Please enter a prompt for image generation.")
        
        # Prepare settings
        settings = {
            "size": self.size_var.get(),
            "quality": self.quality_var.get(),
            "style": self.style_var.get()
        }
        
        try:
            # Disable controls during generation
            self._set_controls_state("disabled")
            self.preview_label.config(text="Generating...")
            
            # Call generation callback
            self.on_generate(prompt, settings)
            
        finally:
            # Re-enable controls
            self._set_controls_state("normal")
    
    def _set_controls_state(self, state: str):
        """Set state of all control widgets.
        
        Args:
            state: Widget state ('normal' or 'disabled')
        """
        self.prompt_text.config(state=state)
        for child in self.winfo_children():
            if isinstance(child, (ttk.Button, ttk.OptionMenu)):
                child.config(state=state)
    
    @handle_errors()
    def set_preview_image(self, image: Image.Image):
        """Update preview with new image.
        
        Args:
            image: PIL Image to display
        """
        # Resize image to fit preview area
        preview_size = (512, 512)
        image.thumbnail(preview_size, Image.Resampling.LANCZOS)
        
        # Update preview
        self.preview_image = ImageTk.PhotoImage(image)
        self.preview_label.config(
            image=self.preview_image,
            text=""  # Clear placeholder text
        )
        logger.debug("Preview image updated")
    
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
