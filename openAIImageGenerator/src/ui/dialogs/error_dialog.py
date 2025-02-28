"""Enhanced error dialog for displaying detailed error information."""

import tkinter as tk
from tkinter import ttk
import logging
from typing import Dict, Any, Optional, Callable
import traceback
import webbrowser

from ...utils.error_handler import ErrorHandler, AppError

logger = logging.getLogger(__name__)

class ErrorDialog(tk.Toplevel):
    """Enhanced dialog for displaying detailed error information."""
    
    def __init__(
        self,
        parent: tk.Tk,
        error: Exception,
        error_handler: ErrorHandler,
        title: str = "Error",
        on_report: Optional[Callable] = None
    ):
        """Initialize error dialog.
        
        Args:
            parent: Parent window
            error: Exception to display
            error_handler: Error handler instance
            title: Dialog title
            on_report: Optional callback for reporting error
        """
        super().__init__(parent)
        self.error = error
        self.error_handler = error_handler
        self.on_report = on_report
        
        # Configure window
        self.title(title)
        self.geometry("600x400")
        self.minsize(500, 300)
        self.transient(parent)
        self.grab_set()
        
        # Center on parent
        self.geometry("+%d+%d" % (
            parent.winfo_rootx() + parent.winfo_width()//2 - 300,
            parent.winfo_rooty() + parent.winfo_height()//2 - 200
        ))
        
        # Get error details
        self.error_type = error.__class__.__name__
        self.error_message = str(error)
        self.error_traceback = "".join(traceback.format_exception(
            type(error),
            error,
            error.__traceback__
        ))
        
        # Get context if available
        self.error_context = {}
        if isinstance(error, AppError):
            self.error_context = error.context
        
        self._create_ui()
        logger.debug(f"Error dialog initialized for {self.error_type}")
    
    def _create_ui(self):
        """Create dialog UI components."""
        # Main container
        main_frame = ttk.Frame(self, padding="10")
        main_frame.pack(fill="both", expand=True)
        
        # Error icon and message
        header_frame = ttk.Frame(main_frame)
        header_frame.pack(fill="x", pady=(0, 10))
        
        # Error icon (using text as placeholder)
        ttk.Label(
            header_frame,
            text="⚠",
            font=("Arial", 24),
            foreground="#e74c3c"
        ).pack(side="left", padx=(0, 10))
        
        # Error message
        message_frame = ttk.Frame(header_frame)
        message_frame.pack(side="left", fill="x", expand=True)
        
        ttk.Label(
            message_frame,
            text=self.error_type,
            font=("Arial", 12, "bold")
        ).pack(anchor="w")
        
        ttk.Label(
            message_frame,
            text=self.error_message,
            wraplength=400
        ).pack(anchor="w", fill="x")
        
        # Notebook for details
        notebook = ttk.Notebook(main_frame)
        notebook.pack(fill="both", expand=True, pady=(0, 10))
        
        # Details tab
        details_frame = ttk.Frame(notebook, padding=5)
        notebook.add(details_frame, text="Details")
        
        # User-friendly explanation
        explanation = self.error_handler.get_error_message(self.error)
        ttk.Label(
            details_frame,
            text="What happened:",
            font=("Arial", 10, "bold")
        ).pack(anchor="w", pady=(0, 5))
        
        ttk.Label(
            details_frame,
            text=explanation,
            wraplength=550
        ).pack(anchor="w", fill="x")
        
        # Possible solutions
        ttk.Label(
            details_frame,
            text="Possible solutions:",
            font=("Arial", 10, "bold")
        ).pack(anchor="w", pady=(10, 5))
        
        solutions_text = self._get_solutions()
        ttk.Label(
            details_frame,
            text=solutions_text,
            wraplength=550
        ).pack(anchor="w", fill="x")
        
        # Technical tab
        technical_frame = ttk.Frame(notebook, padding=5)
        notebook.add(technical_frame, text="Technical Details")
        
        # Traceback
        ttk.Label(
            technical_frame,
            text="Error Traceback:",
            font=("Arial", 10, "bold")
        ).pack(anchor="w", pady=(0, 5))
        
        traceback_text = tk.Text(
            technical_frame,
            wrap="word",
            height=10,
            font=("Courier", 9)
        )
        traceback_text.pack(fill="both", expand=True)
        traceback_text.insert("1.0", self.error_traceback)
        traceback_text.config(state="disabled")
        
        # Add scrollbar
        scrollbar = ttk.Scrollbar(
            traceback_text,
            orient="vertical",
            command=traceback_text.yview
        )
        traceback_text.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        
        # Action buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill="x")
        
        ttk.Button(
            button_frame,
            text="Close",
            command=self.destroy
        ).pack(side="right")
        
        if self.on_report:
            ttk.Button(
                button_frame,
                text="Report Issue",
                command=self._report_issue
            ).pack(side="right", padx=(0, 10))
        
        ttk.Button(
            button_frame,
            text="Copy Details",
            command=self._copy_details
        ).pack(side="right", padx=(0, 10))
    
    def _get_solutions(self) -> str:
        """Get possible solutions based on error type.
        
        Returns:
            String with possible solutions
        """
        solutions = {
            "APIError": (
                "• Check your internet connection\n"
                "• Verify your API key in Settings\n"
                "• Check if you have sufficient credits in your OpenAI account\n"
                "• Try again later as the API might be temporarily unavailable"
            ),
            "DatabaseError": (
                "• Restart the application\n"
                "• Check if your disk has sufficient space\n"
                "• Ensure you have write permissions to the application directory"
            ),
            "FileError": (
                "• Check if the output directory exists and is writable\n"
                "• Ensure you have sufficient disk space\n"
                "• Close any other applications that might be using the file"
            ),
            "ValidationError": (
                "• Check your input for any invalid characters or formats\n"
                "• Ensure all required fields are filled correctly"
            ),
            "ConfigError": (
                "• Reset your settings to default values\n"
                "• Check if the configuration file is not corrupted"
            )
        }
        
        return solutions.get(self.error_type, "• Try restarting the application\n• Check the logs for more details")
    
    def _copy_details(self):
        """Copy error details to clipboard."""
        details = (
            f"Error Type: {self.error_type}\n"
            f"Error Message: {self.error_message}\n\n"
            f"Traceback:\n{self.error_traceback}"
        )
        
        self.clipboard_clear()
        self.clipboard_append(details)
        
        # Update button text temporarily
        for widget in self.winfo_children():
            if isinstance(widget, ttk.Frame):
                for child in widget.winfo_children():
                    if isinstance(child, ttk.Frame) and child.winfo_children():
                        for button in child.winfo_children():
                            if isinstance(button, ttk.Button) and button["text"] == "Copy Details":
                                original_text = button["text"]
                                button["text"] = "Copied!"
                                self.after(2000, lambda b=button, t=original_text: b.config(text=t))
    
    def _report_issue(self):
        """Report issue to developer."""
        if self.on_report:
            self.on_report(self.error)
        else:
            # Open GitHub issues page as fallback
            webbrowser.open("https://github.com/yourusername/openai-image-generator/issues/new") 
