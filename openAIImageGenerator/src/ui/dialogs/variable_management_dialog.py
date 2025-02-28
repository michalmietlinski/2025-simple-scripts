"""Dialog for managing template variables."""

import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import logging
from typing import Any, Dict, List, Optional
from ...core.data_models import TemplateVariable

logger = logging.getLogger(__name__)

class VariableManagementDialog(tk.Toplevel):
    """Dialog for managing template variables and their values."""
    
    def __init__(
        self,
        parent: tk.Widget,
        db_manager: Any,
        error_handler: Any,
        on_close: Optional[callable] = None
    ):
        """Initialize the dialog.
        
        Args:
            parent: Parent widget
            db_manager: Database manager instance
            error_handler: Error handler instance
            on_close: Optional callback for when dialog closes
        """
        super().__init__(parent)
        self.db_manager = db_manager
        self.error_handler = error_handler
        self.on_close = on_close
        
        # Set dialog properties
        self.title("Manage Template Variables")
        self.geometry("800x600")
        self.minsize(600, 400)
        
        # Initialize variables
        self.current_variable: Optional[TemplateVariable] = None
        self.variables: List[TemplateVariable] = []
        
        self._create_ui()
        self._load_variables()
        
        # Make dialog modal
        self.transient(parent)
        self.grab_set()
        
    def _create_ui(self):
        """Create the dialog UI."""
        # Main container with padding
        main_frame = ttk.Frame(self, padding="10")
        main_frame.pack(fill="both", expand=True)
        
        # Left side - Variable list
        left_frame = ttk.Frame(main_frame)
        left_frame.pack(side="left", fill="both", expand=True)
        
        # Search frame
        search_frame = ttk.Frame(left_frame)
        search_frame.pack(fill="x", pady=(0, 5))
        
        self.search_var = tk.StringVar()
        self.search_var.trace("w", self._filter_variables)
        
        search_entry = ttk.Entry(
            search_frame,
            textvariable=self.search_var,
            width=30
        )
        search_entry.pack(side="left", fill="x", expand=True)
        
        # Variable list
        list_frame = ttk.LabelFrame(left_frame, text="Variables", padding="5")
        list_frame.pack(fill="both", expand=True)
        
        # Scrollbar for variable list
        list_scroll = ttk.Scrollbar(list_frame)
        list_scroll.pack(side="right", fill="y")
        
        self.variable_list = tk.Listbox(
            list_frame,
            yscrollcommand=list_scroll.set,
            selectmode="single",
            font=("Arial", 10)
        )
        self.variable_list.pack(side="left", fill="both", expand=True)
        list_scroll.config(command=self.variable_list.yview)
        
        self.variable_list.bind("<<ListboxSelect>>", self._on_variable_select)
        
        # Variable buttons
        var_button_frame = ttk.Frame(left_frame)
        var_button_frame.pack(fill="x", pady=5)
        
        ttk.Button(
            var_button_frame,
            text="Add Variable",
            command=self._add_variable
        ).pack(side="left", padx=2)
        
        ttk.Button(
            var_button_frame,
            text="Delete Variable",
            command=self._delete_variable
        ).pack(side="left", padx=2)
        
        # Right side - Value editor
        right_frame = ttk.LabelFrame(
            main_frame,
            text="Values",
            padding="5"
        )
        right_frame.pack(side="right", fill="both", expand=True, padx=(10, 0))
        
        # Value list
        value_scroll = ttk.Scrollbar(right_frame)
        value_scroll.pack(side="right", fill="y")
        
        self.value_list = tk.Listbox(
            right_frame,
            yscrollcommand=value_scroll.set,
            selectmode="single",
            font=("Arial", 10)
        )
        self.value_list.pack(side="left", fill="both", expand=True)
        value_scroll.config(command=self.value_list.yview)
        
        # Value buttons
        value_button_frame = ttk.Frame(right_frame)
        value_button_frame.pack(fill="x", pady=5)
        
        ttk.Button(
            value_button_frame,
            text="Add Value",
            command=self._add_value
        ).pack(side="left", padx=2)
        
        ttk.Button(
            value_button_frame,
            text="Delete Value",
            command=self._delete_value
        ).pack(side="left", padx=2)
        
        # Bottom buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(side="bottom", fill="x", pady=(10, 0))
        
        ttk.Button(
            button_frame,
            text="Close",
            command=self._on_close
        ).pack(side="right", padx=5)
        
    def _load_variables(self):
        """Load variables from database."""
        try:
            self.variables = self.db_manager.get_template_variables()
            self._update_variable_list()
        except Exception as e:
            logger.error(f"Failed to load variables: {str(e)}")
            messagebox.showerror(
                "Error",
                f"Failed to load variables: {str(e)}"
            )
    
    def _update_variable_list(self):
        """Update the variable listbox."""
        self.variable_list.delete(0, tk.END)
        search_text = self.search_var.get().lower()
        
        for var in self.variables:
            if search_text in var.name.lower():
                self.variable_list.insert(tk.END, var.name)
    
    def _filter_variables(self, *args):
        """Filter variables based on search text."""
        self._update_variable_list()
    
    def _on_variable_select(self, event):
        """Handle variable selection."""
        selection = self.variable_list.curselection()
        if not selection:
            self.current_variable = None
            self.value_list.delete(0, tk.END)
            return
            
        var_name = self.variable_list.get(selection[0])
        self.current_variable = next(
            (var for var in self.variables if var.name == var_name),
            None
        )
        
        self._update_value_list()
    
    def _update_value_list(self):
        """Update the value listbox."""
        self.value_list.delete(0, tk.END)
        if not self.current_variable:
            return
            
        for value in self.current_variable.values:
            self.value_list.insert(tk.END, value)
    
    def _add_variable(self):
        """Add a new variable."""
        name = tk.simpledialog.askstring(
            "Add Variable",
            "Enter variable name:",
            parent=self
        )
        
        if not name:
            return
            
        if any(var.name == name for var in self.variables):
            messagebox.showerror(
                "Error",
                "A variable with this name already exists."
            )
            return
            
        try:
            var_id = self.db_manager.add_template_variable(name, [])
            self._load_variables()
            
            # Select the new variable
            idx = next(
                (i for i, var in enumerate(self.variables) if var.name == name),
                None
            )
            if idx is not None:
                self.variable_list.selection_clear(0, tk.END)
                self.variable_list.selection_set(idx)
                self.variable_list.see(idx)
                self._on_variable_select(None)
                
        except Exception as e:
            logger.error(f"Failed to add variable: {str(e)}")
            messagebox.showerror(
                "Error",
                f"Failed to add variable: {str(e)}"
            )
    
    def _delete_variable(self):
        """Delete the selected variable."""
        if not self.current_variable:
            return
            
        if not messagebox.askyesno(
            "Confirm Delete",
            f"Delete variable '{self.current_variable.name}' and all its values?"
        ):
            return
            
        try:
            self.db_manager.delete_template_variable(self.current_variable.id)
            self._load_variables()
            self.current_variable = None
            self.value_list.delete(0, tk.END)
        except Exception as e:
            logger.error(f"Failed to delete variable: {str(e)}")
            messagebox.showerror(
                "Error",
                f"Failed to delete variable: {str(e)}"
            )
    
    def _add_value(self):
        """Add a new value to the current variable."""
        if not self.current_variable:
            messagebox.showinfo(
                "Info",
                "Please select a variable first."
            )
            return
            
        value = tk.simpledialog.askstring(
            "Add Value",
            f"Enter value for {self.current_variable.name}:",
            parent=self
        )
        
        if not value:
            return
            
        if value in self.current_variable.values:
            messagebox.showerror(
                "Error",
                "This value already exists."
            )
            return
            
        try:
            values = self.current_variable.values + [value]
            self.db_manager.save_template_variable(
                self.current_variable.name,
                values
            )
            self._load_variables()
            
            # Reselect the current variable
            idx = next(
                (i for i, var in enumerate(self.variables)
                 if var.name == self.current_variable.name),
                None
            )
            if idx is not None:
                self.variable_list.selection_clear(0, tk.END)
                self.variable_list.selection_set(idx)
                self.variable_list.see(idx)
                self._on_variable_select(None)
                
        except Exception as e:
            logger.error(f"Failed to add value: {str(e)}")
            messagebox.showerror(
                "Error",
                f"Failed to add value: {str(e)}"
            )
    
    def _delete_value(self):
        """Delete the selected value."""
        if not self.current_variable:
            return
            
        selection = self.value_list.curselection()
        if not selection:
            return
            
        value = self.value_list.get(selection[0])
        
        if not messagebox.askyesno(
            "Confirm Delete",
            f"Delete value '{value}' from variable '{self.current_variable.name}'?"
        ):
            return
            
        try:
            values = [v for v in self.current_variable.values if v != value]
            self.db_manager.save_template_variable(
                self.current_variable.name,
                values
            )
            self._load_variables()
            
            # Reselect the current variable
            idx = next(
                (i for i, var in enumerate(self.variables)
                 if var.name == self.current_variable.name),
                None
            )
            if idx is not None:
                self.variable_list.selection_clear(0, tk.END)
                self.variable_list.selection_set(idx)
                self.variable_list.see(idx)
                self._on_variable_select(None)
                
        except Exception as e:
            logger.error(f"Failed to delete value: {str(e)}")
            messagebox.showerror(
                "Error",
                f"Failed to delete value: {str(e)}"
            )
    
    def _on_close(self):
        """Handle dialog close."""
        if self.on_close:
            self.on_close()
        self.destroy() 
