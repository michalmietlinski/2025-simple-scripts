"""Usage statistics dialog."""

import tkinter as tk
from tkinter import ttk, messagebox
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime

from ...utils.usage_tracker import UsageTracker
from ...utils.error_handler import handle_errors

logger = logging.getLogger(__name__)

class UsageDialog(tk.Toplevel):
    """Dialog for displaying usage statistics."""
    
    def __init__(
        self,
        parent: tk.Tk,
        usage_tracker: UsageTracker,
        error_handler: Any
    ):
        """Initialize usage dialog.
        
        Args:
            parent: Parent window
            usage_tracker: Usage tracker instance
            error_handler: Error handler instance
        """
        super().__init__(parent)
        self.usage_tracker = usage_tracker
        self.error_handler = error_handler
        
        # Configure window
        self.title("Usage Statistics")
        self.geometry("700x500")
        self.minsize(600, 400)
        self.transient(parent)
        self.grab_set()
        
        # Center on parent
        self.geometry("+%d+%d" % (
            parent.winfo_rootx() + parent.winfo_width()//2 - 350,
            parent.winfo_rooty() + parent.winfo_height()//2 - 250
        ))
        
        self._create_ui()
        self._load_data()
        logger.debug("Usage dialog initialized")
    
    def _create_ui(self):
        """Create dialog UI components."""
        # Main container with tabs
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Summary tab
        self.summary_frame = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(self.summary_frame, text="Summary")
        
        # Daily usage tab
        self.daily_frame = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(self.daily_frame, text="Daily Usage")
        
        # Distribution tab
        self.distribution_frame = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(self.distribution_frame, text="Distribution")
        
        # Create summary UI
        self._create_summary_ui()
        
        # Create daily usage UI
        self._create_daily_ui()
        
        # Create distribution UI
        self._create_distribution_ui()
        
        # Action buttons
        button_frame = ttk.Frame(self)
        button_frame.pack(fill="x", padx=10, pady=(0, 10))
        
        ttk.Button(
            button_frame,
            text="Close",
            command=self.destroy
        ).pack(side="right")
        
        ttk.Button(
            button_frame,
            text="Refresh",
            command=self._load_data
        ).pack(side="right", padx=(0, 10))
    
    def _create_summary_ui(self):
        """Create summary tab UI."""
        # Summary statistics
        stats_frame = ttk.LabelFrame(
            self.summary_frame,
            text="Usage Summary",
            padding=10
        )
        stats_frame.pack(fill="both", expand=True)
        
        # Create grid for statistics
        for i, (label, var_name) in enumerate([
            ("Total Images Generated:", "total_images"),
            ("Total Tokens Used:", "total_tokens"),
            ("Total Cost:", "total_cost"),
            ("Monthly Average Cost:", "monthly_avg_cost"),
            ("First Usage Date:", "first_date"),
            ("Last Usage Date:", "last_date")
        ]):
            ttk.Label(
                stats_frame,
                text=label,
                font=("Arial", 10, "bold")
            ).grid(row=i, column=0, sticky="w", padx=5, pady=5)
            
            # Create StringVar for each statistic
            var = tk.StringVar(value="Loading...")
            setattr(self, var_name, var)
            
            ttk.Label(
                stats_frame,
                textvariable=var,
                font=("Arial", 10)
            ).grid(row=i, column=1, sticky="w", padx=5, pady=5)
    
    def _create_daily_ui(self):
        """Create daily usage tab UI."""
        # Period selection
        period_frame = ttk.Frame(self.daily_frame)
        period_frame.pack(fill="x", pady=(0, 10))
        
        ttk.Label(
            period_frame,
            text="Period:",
            font=("Arial", 10, "bold")
        ).pack(side="left")
        
        self.period_var = tk.StringVar(value="30")
        period_combo = ttk.Combobox(
            period_frame,
            textvariable=self.period_var,
            values=["7", "30", "90", "365", "All"],
            width=10
        )
        period_combo.pack(side="left", padx=(5, 0))
        period_combo.bind("<<ComboboxSelected>>", self._on_period_change)
        
        # Daily usage table
        table_frame = ttk.Frame(self.daily_frame)
        table_frame.pack(fill="both", expand=True)
        
        # Create treeview
        columns = ("date", "images", "tokens", "cost")
        self.daily_tree = ttk.Treeview(
            table_frame,
            columns=columns,
            show="headings",
            selectmode="browse"
        )
        
        # Configure columns
        self.daily_tree.heading("date", text="Date")
        self.daily_tree.heading("images", text="Images")
        self.daily_tree.heading("tokens", text="Tokens")
        self.daily_tree.heading("cost", text="Cost")
        
        self.daily_tree.column("date", width=150)
        self.daily_tree.column("images", width=100)
        self.daily_tree.column("tokens", width=100)
        self.daily_tree.column("cost", width=100)
        
        # Add scrollbar
        scrollbar = ttk.Scrollbar(
            table_frame,
            orient="vertical",
            command=self.daily_tree.yview
        )
        self.daily_tree.configure(yscrollcommand=scrollbar.set)
        
        # Pack table components
        self.daily_tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
    
    def _create_distribution_ui(self):
        """Create distribution tab UI."""
        # Model distribution
        model_frame = ttk.LabelFrame(
            self.distribution_frame,
            text="Model Distribution",
            padding=10
        )
        model_frame.pack(fill="x", pady=(0, 10))
        
        self.model_frame_inner = ttk.Frame(model_frame)
        self.model_frame_inner.pack(fill="both", expand=True)
        
        # Size distribution
        size_frame = ttk.LabelFrame(
            self.distribution_frame,
            text="Size Distribution",
            padding=10
        )
        size_frame.pack(fill="x")
        
        self.size_frame_inner = ttk.Frame(size_frame)
        self.size_frame_inner.pack(fill="both", expand=True)
    
    @handle_errors()
    def _load_data(self):
        """Load usage data."""
        # Load summary data
        self._load_summary()
        
        # Load daily usage data
        self._load_daily_usage()
        
        # Load distribution data
        self._load_distribution()
    
    @handle_errors()
    def _load_summary(self):
        """Load summary statistics."""
        summary = self.usage_tracker.get_usage_summary()
        
        # Update summary variables
        self.total_images.set(f"{summary['total_images']:,}")
        self.total_tokens.set(f"{summary['total_tokens']:,}")
        self.total_cost.set(f"${summary['total_cost']:.2f}")
        self.monthly_avg_cost.set(f"${summary['monthly_avg_cost']:.2f}/month")
        
        # Format dates
        if summary['first_date']:
            first_date = datetime.fromisoformat(summary['first_date']).strftime("%Y-%m-%d")
            self.first_date.set(first_date)
        else:
            self.first_date.set("No data")
            
        if summary['last_date']:
            last_date = datetime.fromisoformat(summary['last_date']).strftime("%Y-%m-%d")
            self.last_date.set(last_date)
        else:
            self.last_date.set("No data")
    
    @handle_errors()
    def _load_daily_usage(self):
        """Load daily usage statistics."""
        # Get period
        period = self.period_var.get()
        days = None if period == "All" else int(period)
        
        # Get daily usage
        daily_stats = self.usage_tracker.get_daily_usage(days)
        
        # Update tree
        self.daily_tree.delete(*self.daily_tree.get_children())
        for stat in daily_stats:
            self.daily_tree.insert(
                "",
                "end",
                values=(
                    stat["date"],
                    stat["images"],
                    f"{stat['tokens']:,}",
                    stat["cost"]
                )
            )
    
    @handle_errors()
    def _load_distribution(self):
        """Load distribution statistics."""
        # Clear existing widgets
        for widget in self.model_frame_inner.winfo_children():
            widget.destroy()
        
        for widget in self.size_frame_inner.winfo_children():
            widget.destroy()
        
        # Get model distribution
        model_dist = self.usage_tracker.get_model_distribution()
        
        # Display model distribution
        if model_dist:
            total_models = sum(model_dist.values())
            
            for i, (model, count) in enumerate(model_dist.items()):
                percentage = (count / total_models) * 100
                
                ttk.Label(
                    self.model_frame_inner,
                    text=f"{model}:",
                    font=("Arial", 10, "bold")
                ).grid(row=i, column=0, sticky="w", padx=5, pady=2)
                
                ttk.Label(
                    self.model_frame_inner,
                    text=f"{count} ({percentage:.1f}%)"
                ).grid(row=i, column=1, sticky="w", padx=5, pady=2)
        else:
            ttk.Label(
                self.model_frame_inner,
                text="No data available"
            ).grid(row=0, column=0, sticky="w", padx=5, pady=5)
        
        # Get size distribution
        size_dist = self.usage_tracker.get_size_distribution()
        
        # Display size distribution
        if size_dist:
            total_sizes = sum(size_dist.values())
            for i, (size, count) in enumerate(size_dist.items()):
                percentage = (count / total_sizes) * 100
                
                ttk.Label(
                    self.size_frame_inner,
                    text=f"{size}:",
                    font=("Arial", 10, "bold")
                ).grid(row=i, column=0, sticky="w", padx=5, pady=2)
                
                ttk.Label(
                    self.size_frame_inner,
                    text=f"{count} ({percentage:.1f}%)"
                ).grid(row=i, column=1, sticky="w", padx=5, pady=2)
        else:
            ttk.Label(
                self.size_frame_inner,
                text="No data available"
            ).grid(row=0, column=0, sticky="w", padx=5, pady=5)
    
    def _on_period_change(self, event):
        """Handle period selection change."""
        self._load_daily_usage() 
