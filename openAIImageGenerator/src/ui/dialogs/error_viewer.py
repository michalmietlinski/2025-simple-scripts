"""Error report viewer dialog."""

import tkinter as tk
from tkinter import ttk, messagebox
import logging
from typing import Dict, Any, List
from datetime import datetime
import json
from pathlib import Path

from ...utils.error_handler import ErrorHandler

logger = logging.getLogger(__name__)

class ErrorReportViewer(tk.Toplevel):
    """Dialog for viewing error reports."""
    
    def __init__(
        self,
        parent: tk.Tk,
        error_handler: ErrorHandler
    ):
        """Initialize error report viewer.
        
        Args:
            parent: Parent window
            error_handler: Error handler instance
        """
        super().__init__(parent)
        self.error_handler = error_handler
        
        # Configure window
        self.title("Error Reports")
        self.geometry("800x600")
        self.minsize(600, 400)
        self.transient(parent)
        self.grab_set()
        
        # Center on parent
        self.geometry("+%d+%d" % (
            parent.winfo_rootx() + parent.winfo_width()//2 - 400,
            parent.winfo_rooty() + parent.winfo_height()//2 - 300
        ))
        
        self._create_ui()
        self._load_reports()
        logger.debug("Error report viewer initialized")
    
    def _create_ui(self):
        """Create dialog UI components."""
        # Main container
        main_frame = ttk.Frame(self, padding="10")
        main_frame.pack(fill="both", expand=True)
        
        # Left side - Report list
        list_frame = ttk.LabelFrame(
            main_frame,
            text="Error Reports",
            padding="5"
        )
        list_frame.pack(side="left", fill="both", expand=True)
        
        # Create treeview
        columns = ("date", "type", "message")
        self.tree = ttk.Treeview(
            list_frame,
            columns=columns,
            show="headings",
            selectmode="browse"
        )
        
        # Configure columns
        self.tree.heading("date", text="Date")
        self.tree.heading("type", text="Type")
        self.tree.heading("message", text="Message")
        
        self.tree.column("date", width=150)
        self.tree.column("type", width=100)
        self.tree.column("message", width=300)
        
        # Add scrollbar
        scrollbar = ttk.Scrollbar(
            list_frame,
            orient="vertical",
            command=self.tree.yview
        )
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        # Pack list components
        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Bind selection event
        self.tree.bind("<<TreeviewSelect>>", self._on_select)
        
        # Right side - Details
        details_frame = ttk.LabelFrame(
            main_frame,
            text="Error Details",
            padding="5"
        )
        details_frame.pack(side="right", fill="both", expand=True, padx=(10, 0))
        
        # Details text
        self.details_text = tk.Text(
            details_frame,
            wrap="word",
            font=("Consolas", 10),
            state="disabled"
        )
        self.details_text.pack(fill="both", expand=True)
        
        # Action buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill="x", pady=(10, 0))
        
        ttk.Button(
            button_frame,
            text="Delete Selected",
            command=self._delete_selected,
            style="Danger.TButton"
        ).pack(side="left", padx=5)
        
        ttk.Button(
            button_frame,
            text="Clean Old Reports",
            command=self._cleanup_reports
        ).pack(side="left", padx=5)
        
        ttk.Button(
            button_frame,
            text="Close",
            command=self.destroy
        ).pack(side="right", padx=5)
    
    def _load_reports(self):
        """Load error reports into tree."""
        try:
            # Clear existing items
            self.tree.delete(*self.tree.get_children())
            
            # Load reports
            reports = []
            for report_file in self.error_handler.error_dir.glob("error_*.json"):
                try:
                    data = json.loads(report_file.read_text())
                    reports.append((data, report_file))
                except Exception as e:
                    logger.error(f"Failed to load report {report_file}: {str(e)}")
            
            # Sort by timestamp (newest first)
            reports.sort(
                key=lambda x: x[0]["timestamp"],
                reverse=True
            )
            
            # Add to tree
            for data, file in reports:
                timestamp = datetime.fromisoformat(data["timestamp"])
                self.tree.insert(
                    "",
                    "end",
                    values=(
                        timestamp.strftime("%Y-%m-%d %H:%M:%S"),
                        data["error_type"],
                        data["message"][:50] + "..." if len(data["message"]) > 50 else data["message"]
                    ),
                    tags=(str(file),)
                )
            
        except Exception as e:
            logger.error(f"Failed to load error reports: {str(e)}")
            messagebox.showerror(
                "Error",
                "Failed to load error reports."
            )
    
    def _on_select(self, event):
        """Handle report selection."""
        selection = self.tree.selection()
        if not selection:
            return
        
        try:
            # Get report file from tags
            report_file = Path(self.tree.item(selection[0])["tags"][0])
            
            # Load report data
            data = json.loads(report_file.read_text())
            
            # Format details
            details = [
                f"Timestamp: {datetime.fromisoformat(data['timestamp']).strftime('%Y-%m-%d %H:%M:%S')}",
                f"Error Type: {data['error_type']}",
                f"Message: {data['message']}",
                "\nContext:",
                json.dumps(data['context'], indent=2),
                "\nTraceback:",
                data['traceback']
            ]
            
            # Update text widget
            self.details_text.config(state="normal")
            self.details_text.delete("1.0", "end")
            self.details_text.insert("1.0", "\n".join(details))
            self.details_text.config(state="disabled")
            
        except Exception as e:
            logger.error(f"Failed to load report details: {str(e)}")
            self.details_text.config(state="normal")
            self.details_text.delete("1.0", "end")
            self.details_text.insert("1.0", "Failed to load report details.")
            self.details_text.config(state="disabled")
    
    def _delete_selected(self):
        """Delete selected report."""
        selection = self.tree.selection()
        if not selection:
            return
        
        if not messagebox.askyesno(
            "Confirm Delete",
            "Are you sure you want to delete this error report?"
        ):
            return
        
        try:
            # Get report file from tags
            report_file = Path(self.tree.item(selection[0])["tags"][0])
            
            # Delete file
            report_file.unlink()
            
            # Refresh display
            self._load_reports()
            self.details_text.config(state="normal")
            self.details_text.delete("1.0", "end")
            self.details_text.config(state="disabled")
            
        except Exception as e:
            logger.error(f"Failed to delete report: {str(e)}")
            messagebox.showerror(
                "Error",
                "Failed to delete error report."
            )
    
    def _cleanup_reports(self):
        """Clean up old error reports."""
        if not messagebox.askyesno(
            "Confirm Cleanup",
            "Are you sure you want to clean up old error reports?"
        ):
            return
        
        try:
            self.error_handler.cleanup_old_reports()
            self._load_reports()
            messagebox.showinfo(
                "Success",
                "Old error reports cleaned up successfully."
            )
        except Exception as e:
            logger.error(f"Failed to cleanup reports: {str(e)}")
            messagebox.showerror(
                "Error",
                "Failed to clean up error reports."
            ) 
