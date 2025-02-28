"""Template management dialog."""

import tkinter as tk
from tkinter import ttk, messagebox
import logging
import re
from typing import Dict, Any, List, Optional, Callable
from datetime import datetime

from ...core.database import DatabaseManager
from ...utils.error_handler import handle_errors, ValidationError

logger = logging.getLogger(__name__)

class TemplateDialog(tk.Toplevel):
    """Dialog for managing templates."""
    
    def __init__(
        self,
        parent: tk.Tk,
        db_manager: DatabaseManager,
        on_select: Optional[Callable[[str, List[str]], None]] = None,
        error_handler: Any = None
    ):
        """Initialize template dialog.
        
        Args:
            parent: Parent window
            db_manager: Database manager instance
            on_select: Optional callback when template is selected
            error_handler: Error handler instance
        """
        super().__init__(parent)
        self.db_manager = db_manager
        self.on_select = on_select
        self.error_handler = error_handler
        
        # Configure window
        self.title("Template Manager")
        self.geometry("800x600")
        self.minsize(600, 400)
        self.transient(parent)
        self.grab_set()
        
        # Center on parent
        self.geometry("+%d+%d" % (
            parent.winfo_rootx() + parent.winfo_width()//2 - 400,
            parent.winfo_rooty() + parent.winfo_height()//2 - 300
        ))
        
        # Initialize variables
        self.current_template_id = None
        self.templates = []
        self.variables = []
        
        self._create_ui()
        self._load_templates()
        self._load_variables()
        logger.debug("Template dialog initialized")
    
    def _create_ui(self):
        """Create dialog UI components."""
        # Main container
        main_frame = ttk.Frame(self, padding="10")
        main_frame.pack(fill="both", expand=True)
        
        # Split into left and right panes
        paned_window = ttk.PanedWindow(main_frame, orient=tk.HORIZONTAL)
        paned_window.pack(fill="both", expand=True)
        
        # Left side - Template list
        list_frame = ttk.LabelFrame(
            paned_window,
            text="Templates",
            padding="5"
        )
        paned_window.add(list_frame, weight=1)
        
        # Template list controls
        controls_frame = ttk.Frame(list_frame)
        controls_frame.pack(fill="x", pady=(0, 5))
        
        ttk.Button(
            controls_frame,
            text="New Template",
            command=self._new_template
        ).pack(side="left", padx=5)
        
        ttk.Button(
            controls_frame,
            text="Delete",
            command=self._delete_template
        ).pack(side="left", padx=5)
        
        ttk.Button(
            controls_frame,
            text="Refresh",
            command=self._load_templates
        ).pack(side="right", padx=5)
        
        # Template listbox with scrollbar
        list_container = ttk.Frame(list_frame)
        list_container.pack(fill="both", expand=True)
        
        scrollbar = ttk.Scrollbar(list_container)
        scrollbar.pack(side="right", fill="y")
        
        self.template_listbox = tk.Listbox(
            list_container,
            yscrollcommand=scrollbar.set,
            font=("Arial", 10)
        )
        self.template_listbox.pack(side="left", fill="both", expand=True)
        scrollbar.config(command=self.template_listbox.yview)
        
        # Bind selection event
        self.template_listbox.bind("<<ListboxSelect>>", self._on_template_select)
        
        # Right side - Template editor
        editor_frame = ttk.LabelFrame(
            paned_window,
            text="Template Editor",
            padding="5"
        )
        paned_window.add(editor_frame, weight=2)
        
        # Template text
        ttk.Label(
            editor_frame,
            text="Template Text:",
            font=("Arial", 10, "bold")
        ).pack(anchor="w")
        
        self.template_text = tk.Text(
            editor_frame,
            height=10,
            wrap="word",
            font=("Arial", 10)
        )
        self.template_text.pack(fill="x", pady=(0, 10))
        
        # Variables section
        variables_frame = ttk.LabelFrame(
            editor_frame,
            text="Template Variables",
            padding="5"
        )
        variables_frame.pack(fill="both", expand=True)
        
        # Variables list
        var_list_frame = ttk.Frame(variables_frame)
        var_list_frame.pack(side="left", fill="both", expand=True)
        
        ttk.Label(
            var_list_frame,
            text="Detected Variables:"
        ).pack(anchor="w")
        
        self.variables_listbox = tk.Listbox(
            var_list_frame,
            height=6,
            font=("Arial", 10)
        )
        self.variables_listbox.pack(fill="both", expand=True, pady=(5, 0))
        
        # Variable values
        var_values_frame = ttk.Frame(variables_frame)
        var_values_frame.pack(side="right", fill="both", expand=True, padx=(10, 0))
        
        ttk.Label(
            var_values_frame,
            text="Variable Values:"
        ).pack(anchor="w")
        
        self.values_listbox = tk.Listbox(
            var_values_frame,
            height=6,
            font=("Arial", 10)
        )
        self.values_listbox.pack(fill="both", expand=True, pady=(5, 0))
        
        # Bind variable selection
        self.variables_listbox.bind("<<ListboxSelect>>", self._on_variable_select)
        
        # Action buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill="x", pady=(10, 0))
        
        ttk.Button(
            button_frame,
            text="Save Template",
            command=self._save_template,
            style="Primary.TButton"
        ).pack(side="left", padx=5)
        
        ttk.Button(
            button_frame,
            text="Use Template",
            command=self._use_template
        ).pack(side="left", padx=5)
        
        ttk.Button(
            button_frame,
            text="Close",
            command=self.destroy
        ).pack(side="right", padx=5)
    
    @handle_errors()
    def _load_templates(self):
        """Load templates from database."""
        try:
            # Clear listbox
            self.template_listbox.delete(0, tk.END)
            
            # Get templates
            self.templates = self.db_manager.get_template_history()
            
            # Add to listbox
            for template in self.templates:
                # Use first line as display name
                display_name = template["text"].split("\n")[0][:50]
                if len(display_name) < len(template["text"].split("\n")[0]):
                    display_name += "..."
                
                self.template_listbox.insert(tk.END, display_name)
            
            logger.debug(f"Loaded {len(self.templates)} templates")
            
        except Exception as e:
            logger.error(f"Failed to load templates: {str(e)}")
            messagebox.showerror(
                "Error",
                "Failed to load templates."
            )
    
    @handle_errors()
    def _load_variables(self):
        """Load template variables from database."""
        try:
            # Get variables
            self.variables = self.db_manager.get_template_variables()
            logger.debug(f"Loaded {len(self.variables)} template variables")
            
        except Exception as e:
            logger.error(f"Failed to load template variables: {str(e)}")
    
    def _on_template_select(self, event):
        """Handle template selection."""
        selection = self.template_listbox.curselection()
        if not selection:
            return
        
        try:
            # Get selected template
            template = self.templates[selection[0]]
            self.current_template_id = template["id"]
            
            # Update text
            self.template_text.delete("1.0", tk.END)
            self.template_text.insert("1.0", template["text"])
            
            # Update variables
            self._update_variables()
            
        except Exception as e:
            logger.error(f"Failed to select template: {str(e)}")
    
    def _on_variable_select(self, event):
        """Handle variable selection."""
        selection = self.variables_listbox.curselection()
        if not selection:
            return
        
        try:
            # Get selected variable name
            var_name = self.variables_listbox.get(selection[0])
            
            # Clear values listbox
            self.values_listbox.delete(0, tk.END)
            
            # Find variable in database
            for var in self.variables:
                if var["name"] == var_name:
                    # Add values to listbox
                    for value in var["values"]:
                        self.values_listbox.insert(tk.END, value)
                    break
            
        except Exception as e:
            logger.error(f"Failed to select variable: {str(e)}")
    
    def _update_variables(self):
        """Update variables list based on current template text."""
        try:
            # Clear variables listbox
            self.variables_listbox.delete(0, tk.END)
            
            # Get template text
            template_text = self.template_text.get("1.0", tk.END)
            
            # Extract variables
            variables = self._extract_variables(template_text)
            
            # Add to listbox
            for var in variables:
                self.variables_listbox.insert(tk.END, var)
            
        except Exception as e:
            logger.error(f"Failed to update variables: {str(e)}")
    
    def _extract_variables(self, template_text: str) -> List[str]:
        """Extract variable names from template text.
        
        Args:
            template_text: Template text
            
        Returns:
            List of variable names
        """
        # Find all occurrences of {{variable_name}}
        pattern = r'\{\{([^{}]+)\}\}'
        matches = re.findall(pattern, template_text)
        
        # Return unique variable names
        return list(set(matches))
    
    @handle_errors()
    def _new_template(self):
        """Create a new template."""
        # Clear current template
        self.current_template_id = None
        self.template_text.delete("1.0", tk.END)
        self.variables_listbox.delete(0, tk.END)
        self.values_listbox.delete(0, tk.END)
    
    @handle_errors()
    def _save_template(self):
        """Save current template."""
        try:
            # Get template text
            template_text = self.template_text.get("1.0", tk.END).strip()
            
            if not template_text:
                raise ValidationError("Template text cannot be empty")
            
            # Extract variables
            variables = self._extract_variables(template_text)
            
            if self.current_template_id:
                # Update existing template
                success = self.db_manager.update_template(
                    self.current_template_id,
                    template_text,
                    variables
                )
                
                if success:
                    messagebox.showinfo(
                        "Success",
                        "Template updated successfully."
                    )
                else:
                    raise ValidationError("Failed to update template")
            else:
                # Create new template
                template_id = self.db_manager.add_template(template_text, variables)
                
                if template_id:
                    self.current_template_id = template_id
                    messagebox.showinfo(
                        "Success",
                        "Template created successfully."
                    )
                else:
                    raise ValidationError("Failed to create template")
            
            # Refresh templates
            self._load_templates()
            
        except ValidationError as e:
            messagebox.showerror("Validation Error", str(e))
        except Exception as e:
            logger.error(f"Failed to save template: {str(e)}")
            messagebox.showerror(
                "Error",
                "Failed to save template."
            )
    
    @handle_errors()
    def _delete_template(self):
        """Delete current template."""
        if not self.current_template_id:
            messagebox.showinfo(
                "Info",
                "No template selected."
            )
            return
        
        if not messagebox.askyesno(
            "Confirm Delete",
            "Are you sure you want to delete this template?"
        ):
            return
        
        try:
            success = self.db_manager.delete_template(self.current_template_id)
            
            if success:
                messagebox.showinfo(
                    "Success",
                    "Template deleted successfully."
                )
                
                # Clear current template
                self.current_template_id = None
                self.template_text.delete("1.0", tk.END)
                self.variables_listbox.delete(0, tk.END)
                self.values_listbox.delete(0, tk.END)
                
                # Refresh templates
                self._load_templates()
            else:
                raise ValidationError("Failed to delete template")
            
        except ValidationError as e:
            messagebox.showerror("Validation Error", str(e))
        except Exception as e:
            logger.error(f"Failed to delete template: {str(e)}")
            messagebox.showerror(
                "Error",
                "Failed to delete template."
            )
    
    @handle_errors()
    def _use_template(self):
        """Use current template."""
        if not self.current_template_id:
            messagebox.showinfo(
                "Info",
                "No template selected."
            )
            return
        
        try:
            # Get template text
            template_text = self.template_text.get("1.0", tk.END).strip()
            
            # Extract variables
            variables = self._extract_variables(template_text)
            
            # Call callback if provided
            if self.on_select:
                self.on_select(template_text, variables)
                self.destroy()
            
        except Exception as e:
            logger.error(f"Failed to use template: {str(e)}")
            messagebox.showerror(
                "Error",
                "Failed to use template."
            ) 
