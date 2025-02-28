"""Main window for the DALL-E Image Generator application."""

import tkinter as tk
from tkinter import ttk, messagebox
import logging
from pathlib import Path
from typing import Optional, Dict, Any
import threading
import time

from ..core.openai_client import OpenAIImageClient
from ..core.database import DatabaseManager
from ..core.file_manager import FileManager
from ..core.data_models import Generation, Prompt
from ..utils.settings_manager import SettingsManager
from ..utils.error_handler import ErrorHandler, handle_errors, APIError, FileError, DatabaseError
from ..utils.usage_tracker import UsageTracker
from .tabs.generation_tab import GenerationTab
from .tabs.history_tab import HistoryTab
from .dialogs.settings_dialog import SettingsDialog
from .dialogs.error_viewer import ErrorReportViewer
from .dialogs.template_dialog import TemplateDialog
from .dialogs.usage_dialog import UsageDialog

logger = logging.getLogger(__name__)

class MainWindow:
    """Main application window."""
    
    def __init__(
        self,
        root: tk.Tk,
        openai_client: OpenAIImageClient,
        db_manager: DatabaseManager,
        file_manager: FileManager,
        settings_manager: SettingsManager,
        error_handler: ErrorHandler
    ):
        """Initialize main window.
        
        Args:
            root: Root Tkinter window
            openai_client: OpenAI client instance
            db_manager: Database manager instance
            file_manager: File manager instance
            settings_manager: Settings manager instance
            error_handler: Error handler instance
        """
        self.root = root
        self.openai_client = openai_client
        self.db_manager = db_manager
        self.file_manager = file_manager
        self.settings_manager = settings_manager
        self.error_handler = error_handler
        
        # Initialize usage tracker
        self.usage_tracker = UsageTracker(db_manager)
        
        # Configure root window
        self.root.title("DALL-E Image Generator")
        
        # Restore window geometry
        geometry = settings_manager.get_window_geometry()
        if geometry:
            self.root.geometry(geometry)
        else:
            self.root.geometry("1200x800")
        self.root.minsize(800, 600)
        
        # Save geometry on window changes
        self.root.bind("<Configure>", self._on_window_configure)
        
        # Initialize UI components
        self.notebook: Optional[ttk.Notebook] = None
        self.generation_tab: Optional[GenerationTab] = None
        self.history_tab: Optional[HistoryTab] = None
        
        # Set up UI
        self._setup_styles()
        self._create_menu()
        self._setup_main_ui()
        self._setup_status_bar()
        
        # Verify API key
        self._update_api_status()
        
        logger.info("Main window initialized")
    
    def _on_window_configure(self, event: tk.Event):
        """Handle window configuration changes."""
        if event.widget == self.root:
            self.settings_manager.set_window_geometry(self.root.geometry())
    
    def _setup_styles(self):
        """Configure ttk styles."""
        style = ttk.Style()
        
        # Configure notebook style
        style.configure(
            "Custom.TNotebook",
            background="#f0f0f0",
            padding=5
        )
        style.configure(
            "Custom.TNotebook.Tab",
            padding=[10, 5],
            font=("Arial", 10, "bold")
        )
        
        # Configure button styles
        style.configure(
            "Primary.TButton",
            padding=5,
            font=("Arial", 10, "bold")
        )
        style.configure(
            "Danger.TButton",
            padding=5,
            font=("Arial", 10, "bold"),
            foreground="red"
        )
        
        logger.debug("UI styles configured")
    
    def _create_menu(self):
        """Create main menu bar."""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Settings", command=self._show_settings)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit)
        
        # Tools menu
        tools_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Tools", menu=tools_menu)
        tools_menu.add_command(label="Verify API Key", command=self._verify_api_key)
        tools_menu.add_command(label="Clean Old Files", command=self._cleanup_files)
        tools_menu.add_command(label="Manage Templates", command=self._show_template_manager)
        tools_menu.add_command(label="Usage Statistics", command=self._show_usage_stats)
        tools_menu.add_separator()
        tools_menu.add_command(label="View Error Reports", command=self._show_error_reports)
        
        # Help menu
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="Documentation", command=self._show_docs)
        help_menu.add_command(label="About", command=self._show_about)
        
        logger.debug("Menu bar created")
    
    def _setup_main_ui(self):
        """Set up main UI components."""
        # Header
        header = tk.Frame(self.root)
        header.pack(fill="x", padx=10, pady=5)
        
        tk.Label(
            header,
            text="DALL-E Image Generator",
            font=("Arial", 16, "bold")
        ).pack(side="left")
        
        # Button to open output folder
        ttk.Button(
            header,
            text="Open Output Folder",
            command=self._open_output_folder
        ).pack(side="right", padx=(0, 10))
        
        # API status indicator
        self.api_status_label = tk.Label(
            header,
            text="Checking API status...",
            font=("Arial", 10)
        )
        self.api_status_label.pack(side="right")
        self.root.after(100, self._update_api_status)
        
        # Notebook for tabs
        self.notebook = ttk.Notebook(
            self.root,
            style="Custom.TNotebook"
        )
        self.notebook.pack(fill="both", expand=True, padx=10, pady=5)
        
        # Create tabs
        self.generation_tab = GenerationTab(
            self.notebook,
            self._handle_generation,
            error_handler=self.error_handler,
            db_manager=self.db_manager
        )
        self.history_tab = HistoryTab(
            self.notebook,
            self.db_manager,
            self.file_manager,
            error_handler=self.error_handler
        )
        
        self.notebook.add(self.generation_tab, text="Generate")
        self.notebook.add(self.history_tab, text="History")
        
        logger.debug("Main UI framework created")
    
    def _setup_status_bar(self):
        """Set up status bar."""
        status_bar = ttk.Frame(self.root)
        status_bar.pack(fill="x", side="bottom")
        
        self.status_label = ttk.Label(
            status_bar,
            text="Ready",
            font=("Arial", 9)
        )
        self.status_label.pack(side="left", padx=5)
        
        logger.debug("Status bar created")
    
    def _update_api_status(self):
        """Update the API status label after a short delay."""
        try:
            is_valid = self.openai_client.validate_api_key()
            if is_valid:
                self.api_status_label.config(text="API: Connected", foreground="green")
            else:
                self.api_status_label.config(text="API: Invalid Key", foreground="red")
        except Exception as e:
            self.api_status_label.config(text="API: Error", foreground="red")
            logger.error(f"Error validating API key: {e}")
    
    @handle_errors()
    def _handle_generation(self, prompt: str, settings: Dict[str, Any]):
        """Handle image generation request.
        
        Args:
            prompt: Generation prompt
            settings: Generation settings
        """
        try:
            self.set_status("Generating image...")
            
            # Generate image
            images, usage_info = self.openai_client.generate_image(
                prompt=prompt,
                size=settings["size"],
                quality=settings["quality"],
                style=settings["style"]
            )
            
            if not images:
                raise APIError("No images generated")
            
            # Save first image
            image_path = self.file_manager.save_image(
                images[0],
                prompt=prompt
            )
            
            if not image_path:
                raise FileError("Failed to save image")
            
            # Create prompt record
            prompt_obj = Prompt(prompt_text=prompt)
            prompt_id = self.db_manager.add_prompt(prompt_obj)
            
            # Create generation record
            generation = Generation(
                prompt_id=prompt_id,
                image_path=str(image_path.relative_to(self.file_manager.output_dir)),
                parameters=settings,
                token_usage=usage_info["estimated_tokens"],
                cost=0.0,  # TODO: Calculate actual cost
                prompt_text=prompt
            )
            self.db_manager.add_generation(generation)
            
            # Record usage
            self.usage_tracker.record_usage(
                tokens=usage_info["estimated_tokens"],
                model=usage_info.get("model", "unknown"),
                size=settings["size"]
            )
            
            # Update preview
            self.generation_tab.set_preview_image(images[0])
            
            # Refresh history
            self.history_tab._load_history()
            
            self.set_status("Image generated successfully")
            
        except Exception as e:
            self.set_status("Generation failed")
            raise
    
    @handle_errors()
    def _verify_api_key(self):
        """Verify the API key and update status."""
        try:
            if self.openai_client.validate_api_key():
                self.api_status_label.config(
                    text="API: Connected ✓",
                    foreground="green"
                )
            else:
                self.api_status_label.config(
                    text="API: Invalid Key ✗",
                    foreground="red"
                )
        except Exception as e:
            self.api_status_label.config(
                text="API: Error ✗",
                foreground="red"
            )
            logger.error(f"API key validation failed: {str(e)}")
    
    @handle_errors()
    def _cleanup_files(self):
        """Clean up old files."""
        settings = self.settings_manager.get_settings()
        if settings["cleanup_enabled"]:
            if self.file_manager.cleanup_old_files(settings["cleanup_days"]):
                messagebox.showinfo(
                    "Success",
                    "Old files cleaned up successfully."
                )
            else:
                raise FileError("Some files could not be cleaned up")
        else:
            messagebox.showinfo(
                "Info",
                "Automatic cleanup is disabled. Enable it in settings."
            )
    
    @handle_errors()
    def _show_settings(self):
        """Show settings dialog."""
        dialog = SettingsDialog(
            self.root,
            self.settings_manager.get_settings(),
            self._handle_settings_update,
            error_handler=self.error_handler
        )
        dialog.focus()
    
    @handle_errors()
    def _show_template_manager(self):
        """Show template management dialog."""
        dialog = TemplateDialog(
            self.root,
            self.db_manager,
            error_handler=self.error_handler
        )
        dialog.focus()
    
    @handle_errors()
    def _show_usage_stats(self):
        """Show usage statistics dialog."""
        dialog = UsageDialog(
            self.root,
            self.usage_tracker,
            self.error_handler
        )
        dialog.focus()
    
    @handle_errors()
    def _handle_settings_update(self, new_settings: Dict[str, Any]):
        """Handle settings update from dialog.
        
        Args:
            new_settings: New settings values
        """
        # Update settings
        self.settings_manager.update_settings(new_settings)
        
        # Update components
        self.openai_client.api_key = new_settings["api_key"]
        self.file_manager.output_dir = Path(new_settings["output_dir"])
        self.history_tab.page_size = new_settings["page_size"]
        
        # Refresh UI
        self._update_api_status()
        self.history_tab._load_history()
        
        logger.info("Settings applied successfully")
    
    def _show_docs(self):
        """Show documentation."""
        messagebox.showinfo(
            "Documentation",
            "Documentation will be available in the next update."
        )
    
    def _show_about(self):
        """Show about dialog."""
        messagebox.showinfo(
            "About",
            "DALL-E Image Generator\nVersion 2.0.0\n\n"
            "A powerful tool for generating images using OpenAI's DALL-E."
        )
    
    def _show_error_reports(self):
        """Show error reports dialog."""
        ErrorReportViewer(self.root, self.error_handler)
    
    def _open_output_folder(self):
        """Open the output folder in the system file explorer."""
        try:
            self.file_manager.open_output_folder()
        except Exception as e:
            messagebox.showerror("Error", f"Could not open output folder: {str(e)}")
            logger.error(f"Error opening output folder: {e}")
    
    def set_status(self, message: str):
        """Update status bar message.
        
        Args:
            message: Status message to display
        """
        self.status_label.config(text=message)
        logger.debug(f"Status updated: {message}")
    
    def run(self):
        """Start the main event loop."""
        self.root.mainloop() 
