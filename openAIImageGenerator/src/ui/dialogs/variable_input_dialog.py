"""Dialog for template variable input."""

import tkinter as tk
from tkinter import ttk, messagebox
import logging
from typing import Dict, List, Any, Optional, Callable

from ...utils.error_handler import handle_errors, ValidationError

logger = logging.getLogger(__name__)

class VariableInputDialog(tk.Toplevel):
    """Dialog for entering template variable values."""
    
    def __init__(
        self,
        parent: tk.Tk,
        template_text: str,
        variables: List[str],
        db_manager: Any,
        on_submit: Callable[[str], None],
        error_handler: Any = None
    ):
        """Initialize variable input dialog.
        
        Args:
            parent: Parent window
            template_text: Template text
            variables: List of variable names
            db_manager: Database manager instance
            on_submit: Callback for submitting processed template
            error_handler: Error handler instance
        """
        super().__init__(parent)
        self.template_text = template_text
        self.variables = variables
        self.db_manager = db_manager
        self.on_submit = on_submit
        self.error_handler = error_handler
        
        # Configure window
        self.title("Template Variables")
        self.geometry("500x400")
        self.minsize(400, 300)
        self.transient(parent)
        self.grab_set()
        
        # Center on parent
        self.geometry("+%d+%d" % (
            parent.winfo_rootx() + parent.winfo_width()//2 - 250,
            parent.winfo_rooty() + parent.winfo_height()//2 - 200
        ))
        
        # Initialize variables
        self.variable_entries = {}
        self.variable_values = {}
        self.variable_data = {}
        
        self._create_ui()
        self._load_variable_data()
        logger.debug("Variable input dialog initialized")
    
    def _create_ui(self):
        """Create dialog UI components."""
        # Main container
        main_frame = ttk.Frame(self, padding="10")
        main_frame.pack(fill="both", expand=True)
        
        # Template preview
        preview_frame = ttk.LabelFrame(
            main_frame,
            text="Template Preview",
            padding="5"
        )
        preview_frame.pack(fill="x", pady=(0, 10))
        
        preview_text = tk.Text(
            preview_frame,
            height=5,
            wrap="word",
            font=("Arial", 10)
        )
        preview_text.pack(fill="x")
        preview_text.insert("1.0", self.template_text)
        preview_text.config(state="disabled")
        
        # Variables section
        variables_frame = ttk.LabelFrame(
            main_frame,
            text="Variable Values",
            padding="5"
        )
        variables_frame.pack(fill="both", expand=True)
        
        # Create scrollable frame for variables
        canvas = tk.Canvas(variables_frame)
        scrollbar = ttk.Scrollbar(variables_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Create entry fields for each variable
        for var_name in self.variables:
            var_frame = ttk.Frame(scrollable_frame)
            var_frame.pack(fill="x", pady=5)
            
            ttk.Label(
                var_frame,
                text=f"{var_name}:",
                width=15
            ).pack(side="left")
            
            # Create variable with default value
            self.variable_values[var_name] = tk.StringVar(value="")
            
            # Create combobox for variable
            combo = ttk.Combobox(
                var_frame,
                textvariable=self.variable_values[var_name]
            )
            combo.pack(side="left", fill="x", expand=True)
            
            # Add right-click context menu for paste
            self._add_context_menu(combo)
            
            # Store reference to entry
            self.variable_entries[var_name] = combo
        
        # Random values option
        random_frame = ttk.Frame(main_frame)
        random_frame.pack(fill="x", pady=(10, 0))
        
        self.use_random_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(
            random_frame,
            text="Use random values for empty fields",
            variable=self.use_random_var
        ).pack(side="left")
        
        # Action buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill="x", pady=(10, 0))
        
        ttk.Button(
            button_frame,
            text="Submit",
            command=self._process_template,
            style="Primary.TButton"
        ).pack(side="right", padx=(5, 0))
        
        ttk.Button(
            button_frame,
            text="Cancel",
            command=self.destroy
        ).pack(side="right")
    
    def _add_context_menu(self, widget):
        """Add right-click context menu to widget.
        
        Args:
            widget: Widget to add context menu to
        """
        context_menu = tk.Menu(widget, tearoff=0)
        context_menu.add_command(label="Paste", command=lambda: self._paste_to_widget(widget))
        
        # Bind right-click to show context menu
        widget.bind("<Button-3>", lambda e: self._show_context_menu(e, context_menu))
        
        # Also bind Ctrl+V for paste
        widget.bind("<Control-v>", lambda e: self._paste_to_widget(widget))
    
    def _show_context_menu(self, event, menu):
        """Show context menu at event position.
        
        Args:
            event: Event that triggered context menu
            menu: Context menu to show
        """
        try:
            menu.tk_popup(event.x_root, event.y_root)
        finally:
            menu.grab_release()
    
    def _paste_to_widget(self, widget):
        """Paste clipboard content to widget.
        
        Args:
            widget: Widget to paste to
        """
        try:
            # Get clipboard content
            clipboard = self.clipboard_get()
            
            # Insert at cursor position or replace selection
            if isinstance(widget, ttk.Combobox):
                widget.set(clipboard)
            else:
                widget.insert(tk.INSERT, clipboard)
                
            logger.debug("Pasted from clipboard")
            
        except Exception as e:
            logger.error(f"Failed to paste from clipboard: {str(e)}")
    
    @handle_errors()
    def _load_variable_data(self):
        """Load variable data from database."""
        try:
            # Get all variables
            variables = self.db_manager.get_template_variables()
            
            # Store variable data
            for var in variables:
                self.variable_data[var["name"]] = var
            
            # Update comboboxes
            for var_name, combo in self.variable_entries.items():
                if var_name in self.variable_data:
                    combo["values"] = self.variable_data[var_name]["values"]
            
            logger.debug("Variable data loaded")
            
        except Exception as e:
            logger.error(f"Failed to load variable data: {str(e)}")
    
    @handle_errors()
    def _process_template(self):
        """Process template with variable values."""
        try:
            # Get variable values
            values = {}
            missing_variables = []
            
            for var_name, var in self.variable_values.items():
                value = var.get().strip()
                if value:
                    values[var_name] = value
                else:
                    missing_variables.append(var_name)
            
            # Check if any variables are missing and random values are not enabled
            if missing_variables and not self.use_random_var.get():
                missing_vars_str = ", ".join(missing_variables)
                if not messagebox.askyesno(
                    "Missing Variables",
                    f"The following variables have no values: {missing_vars_str}\n\n"
                    "Do you want to continue with empty values?"
                ):
                    return
            
            # Import here to avoid circular imports
            from ...utils.template_utils import TemplateProcessor
            
            # Process template
            processor = TemplateProcessor(self.db_manager)
            processed_text = processor.substitute_variables(
                self.template_text,
                values,
                self.use_random_var.get()
            )
            
            # Validate that all variables were substituted
            if "{{" in processed_text and "}}" in processed_text:
                if not messagebox.askyesno(
                    "Unresolved Variables",
                    "Some variables could not be resolved. Do you want to continue anyway?"
                ):
                    return
            
            # Call callback
            self.on_submit(processed_text)
            self.destroy()
            
        except Exception as e:
            logger.error(f"Failed to process template: {str(e)}")
            messagebox.showerror(
                "Error",
                "Failed to process template."
            ) 
