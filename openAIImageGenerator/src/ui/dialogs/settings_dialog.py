"""Settings dialog for application configuration."""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import logging
from typing import Dict, Any, Callable
from pathlib import Path

from ...utils.error_handler import handle_errors, ValidationError

logger = logging.getLogger(__name__)

class SettingsDialog(tk.Toplevel):
    """Dialog for managing application settings."""
    
    def __init__(
        self,
        parent: tk.Tk,
        current_settings: Dict[str, Any],
        on_save: Callable[[Dict[str, Any]], None],
        error_handler: Any
    ):
        """Initialize settings dialog.
        
        Args:
            parent: Parent window
            current_settings: Current settings values
            on_save: Callback for saving settings
            error_handler: Error handler instance
        """
        super().__init__(parent)
        self.current_settings = current_settings.copy()
        self.on_save = on_save
        self.error_handler = error_handler
        
        # Configure window
        self.title("Settings")
        self.geometry("500x400")
        self.minsize(400, 300)
        self.transient(parent)
        self.grab_set()
        
        # Center on parent
        self.geometry("+%d+%d" % (
            parent.winfo_rootx() + parent.winfo_width()//2 - 250,
            parent.winfo_rooty() + parent.winfo_height()//2 - 200
        ))
        
        self._create_ui()
        self._load_current_settings()
        logger.debug("Settings dialog initialized")

    @handle_errors()
    def _create_ui(self):
        """Create dialog UI components."""
        # Main container
        main_frame = ttk.Frame(self, padding="10")
        main_frame.pack(fill="both", expand=True)
        
        # API settings
        api_frame = ttk.LabelFrame(
            main_frame,
            text="API Settings",
            padding="5"
        )
        api_frame.pack(fill="x", pady=(0, 10))
        
        ttk.Label(api_frame, text="API Key:").pack(fill="x")
        self.api_key_var = tk.StringVar()
        self.api_key_entry = ttk.Entry(
            api_frame,
            textvariable=self.api_key_var,
            show="*"
        )
        self.api_key_entry.pack(fill="x")
        
        # Output settings
        output_frame = ttk.LabelFrame(
            main_frame,
            text="Output Settings",
            padding="5"
        )
        output_frame.pack(fill="x", pady=(0, 10))
        
        ttk.Label(output_frame, text="Output Directory:").pack(fill="x")
        dir_frame = ttk.Frame(output_frame)
        dir_frame.pack(fill="x")
        
        self.output_dir_var = tk.StringVar()
        ttk.Entry(
            dir_frame,
            textvariable=self.output_dir_var,
            state="readonly"
        ).pack(side="left", fill="x", expand=True)
        
        ttk.Button(
            dir_frame,
            text="Browse",
            command=self._browse_output_dir
        ).pack(side="right", padx=(5, 0))
        
        # Cleanup settings
        cleanup_frame = ttk.LabelFrame(
            main_frame,
            text="Cleanup Settings",
            padding="5"
        )
        cleanup_frame.pack(fill="x", pady=(0, 10))
        
        self.cleanup_enabled_var = tk.BooleanVar()
        ttk.Checkbutton(
            cleanup_frame,
            text="Enable automatic cleanup of old files",
            variable=self.cleanup_enabled_var
        ).pack(fill="x")
        
        days_frame = ttk.Frame(cleanup_frame)
        days_frame.pack(fill="x", pady=(5, 0))
        
        ttk.Label(days_frame, text="Keep files for:").pack(side="left")
        self.cleanup_days_var = tk.StringVar()
        ttk.Entry(
            days_frame,
            textvariable=self.cleanup_days_var,
            width=5
        ).pack(side="left", padx=(5, 0))
        ttk.Label(days_frame, text="days").pack(side="left", padx=(5, 0))
        
        # Display settings
        display_frame = ttk.LabelFrame(
            main_frame,
            text="Display Settings",
            padding="5"
        )
        display_frame.pack(fill="x", pady=(0, 10))
        
        page_frame = ttk.Frame(display_frame)
        page_frame.pack(fill="x")
        
        ttk.Label(page_frame, text="Items per page:").pack(side="left")
        self.page_size_var = tk.StringVar()
        ttk.Entry(
            page_frame,
            textvariable=self.page_size_var,
            width=5
        ).pack(side="left", padx=(5, 0))
        
        # Action buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill="x", pady=(10, 0))
        
        ttk.Button(
            button_frame,
            text="Save",
            command=self._save_settings,
            style="Primary.TButton"
        ).pack(side="right", padx=(5, 0))
        
        ttk.Button(
            button_frame,
            text="Cancel",
            command=self.destroy
        ).pack(side="right")

    @handle_errors()
    def _load_current_settings(self):
        """Load current settings into UI."""
        self.api_key_var.set(self.current_settings.get("api_key", ""))
        self.output_dir_var.set(str(self.current_settings.get("output_dir", "")))
        self.cleanup_enabled_var.set(self.current_settings.get("cleanup_enabled", False))
        self.cleanup_days_var.set(str(self.current_settings.get("cleanup_days", 30)))
        self.page_size_var.set(str(self.current_settings.get("page_size", 10)))

    @handle_errors()
    def _browse_output_dir(self):
        """Show directory browser dialog."""
        current_dir = self.output_dir_var.get()
        new_dir = filedialog.askdirectory(
            initialdir=current_dir if current_dir else None,
            title="Select Output Directory"
        )
        
        if new_dir:
            self.output_dir_var.set(new_dir)

    @handle_errors()
    def _save_settings(self):
        """Validate and save settings."""
        try:
            # Validate API key
            api_key = self.api_key_var.get().strip()
            if not api_key:
                raise ValidationError("API key is required")
            
            # Validate output directory
            output_dir = self.output_dir_var.get().strip()
            if not output_dir:
                raise ValidationError("Output directory is required")
            
            # Validate cleanup days
            try:
                cleanup_days = int(self.cleanup_days_var.get())
                if cleanup_days < 1:
                    raise ValueError()
            except ValueError:
                raise ValidationError("Cleanup days must be a positive number")
            
            # Validate page size
            try:
                page_size = int(self.page_size_var.get())
                if page_size < 1:
                    raise ValueError()
            except ValueError:
                raise ValidationError("Page size must be a positive number")
            
            # Prepare settings
            new_settings = {
                "api_key": api_key,
                "output_dir": output_dir,
                "cleanup_enabled": self.cleanup_enabled_var.get(),
                "cleanup_days": cleanup_days,
                "page_size": page_size
            }
            
            # Save settings
            self.on_save(new_settings)
            self.destroy()
            
        except ValidationError as e:
            messagebox.showerror("Validation Error", str(e))
        except Exception as e:
            logger.error(f"Failed to save settings: {str(e)}")
            raise 
