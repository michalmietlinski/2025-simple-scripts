"""Dialog for template variable input."""

import tkinter as tk
from tkinter import ttk, messagebox
import logging
from typing import Dict, List, Any, Optional, Callable

from ...utils.error_handler import handle_errors, ValidationError
from .variable_management_dialog import VariableManagementDialog

logger = logging.getLogger(__name__)

class VariableInputDialog(tk.Toplevel):
    """Dialog for entering template variable values."""
    
    def __init__(
        self,
        parent: tk.Tk,
        template_text: str,
        variables: List[str],
        db_manager: Any,
        on_submit: Callable[[List[str]], None],
        error_handler: Any = None
    ):
        """Initialize variable input dialog.
        
        Args:
            parent: Parent window
            template_text: Template text
            variables: List of variable names
            db_manager: Database manager instance
            on_submit: Callback for submitting processed templates
            error_handler: Error handler instance
        """
        super().__init__(parent)
        self.template_text = template_text
        self.variables = variables
        self.db_manager = db_manager
        self.on_submit = on_submit
        self.error_handler = error_handler
        
        # Initialize UI elements
        self.variable_entries = {}  # Will store {var_name: listbox}
        
        # Configure window
        self.title("Template Variables")
        self.geometry("600x550")  # Increased height for status bar
        self.minsize(500, 450)  # Increased minimum height
        self.transient(parent)
        self.grab_set()
        
        # Center on parent
        self.geometry("+%d+%d" % (
            parent.winfo_rootx() + parent.winfo_width()//2 - 300,
            parent.winfo_rooty() + parent.winfo_height()//2 - 275
        ))
        
        # Initialize variables
        self.variable_values = {}
        self.variable_data = {}
        self.status_var = tk.StringVar(value="Ready")
        
        self._create_ui()
        self._load_variable_data()
        logger.debug("Variable input dialog initialized")
    
    def _create_ui(self):
        """Create dialog UI components."""
        # Main container
        main_frame = ttk.Frame(self)
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Status bar - pack FIRST
        status_frame = ttk.Frame(main_frame)
        status_frame.pack(side="bottom", fill="x")
        
        ttk.Separator(status_frame, orient="horizontal").pack(fill="x", pady=5)
        
        self.status_label = ttk.Label(
            status_frame,
            textvariable=self.status_var,
            font=("Arial", 9)
        )
        self.status_label.pack(side="left")
        
        # Bottom frame for buttons - pack SECOND
        bottom_frame = ttk.Frame(main_frame)
        bottom_frame.pack(side="bottom", fill="x", pady=(0, 5))
        
        # Random values option
        random_frame = ttk.Frame(bottom_frame)
        random_frame.pack(fill="x", pady=(0, 10))
        
        self.use_random_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(
            random_frame,
            text="Use random values for empty fields",
            variable=self.use_random_var
        ).pack(side="left")
        
        # Action buttons
        button_frame = ttk.Frame(bottom_frame)
        button_frame.pack(fill="x")
        
        # Left side buttons
        left_buttons = ttk.Frame(button_frame)
        left_buttons.pack(side="left")

        ttk.Button(
            left_buttons,
            text="Manage Variables",
            command=self._show_variable_manager
        ).pack(side="left", padx=5)

        # Right side buttons
        right_buttons = ttk.Frame(button_frame)
        right_buttons.pack(side="right")

        ttk.Button(
            right_buttons,
            text="Cancel",
            command=self.destroy
        ).pack(side="right", padx=5)

        ttk.Button(
            right_buttons,
            text="Generate Selected",
            command=self._process_template_selected,
            style="Primary.TButton"
        ).pack(side="right", padx=5)

        ttk.Button(
            right_buttons,
            text="Generate All",
            command=self._process_template_combinations
        ).pack(side="right", padx=5)

        # Content frame - pack LAST
        content_frame = ttk.Frame(main_frame)
        content_frame.pack(fill="both", expand=True)
        
        # Template preview
        preview_frame = ttk.LabelFrame(
            content_frame,
            text="Template Preview",
            padding="5"
        )
        preview_frame.pack(fill="x", pady=(0, 10))
        
        preview_text = tk.Text(
            preview_frame,
            height=4,
            wrap="word",
            font=("Arial", 10)
        )
        preview_text.pack(fill="x")
        preview_text.insert("1.0", self.template_text)
        preview_text.config(state="disabled")
        
        # Variables section
        variables_frame = ttk.LabelFrame(
            content_frame,
            text="Variable Values",
            padding="5"
        )
        variables_frame.pack(fill="both", expand=True)
        
        # Create scrollable frame for variables
        canvas = tk.Canvas(variables_frame, height=200)  # Reduced height
        scrollbar = ttk.Scrollbar(variables_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Pack canvas and scrollbar
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Create variable entries
        for var_name in self.variables:
            var_frame = ttk.LabelFrame(
                scrollable_frame,
                text=var_name,
                padding="5"
            )
            var_frame.pack(fill="x", pady=2, padx=5)
            
            # Selection helper buttons
            select_frame = ttk.Frame(var_frame)
            select_frame.pack(fill="x", pady=(0, 5))
            
            ttk.Button(
                select_frame,
                text="Select All",
                command=lambda name=var_name: self._select_all_values(name),
                width=10
            ).pack(side="left", padx=2)
            
            ttk.Button(
                select_frame,
                text="Clear",
                command=lambda name=var_name: self._clear_selection(name),
                width=8
            ).pack(side="left", padx=2)
            
            # Create listbox for values
            listbox = tk.Listbox(
                var_frame,
                selectmode="multiple",
                height=4
            )
            listbox.pack(fill="x", expand=True)
            
            # Add scrollbar for listbox
            listbox_scrollbar = ttk.Scrollbar(var_frame, orient="vertical", command=listbox.yview)
            listbox_scrollbar.pack(side="right", fill="y")
            listbox.configure(yscrollcommand=listbox_scrollbar.set)
            
            # Store listbox reference
            self.variable_entries[var_name] = listbox
        
        # Configure canvas scrolling
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        canvas.bind_all("<MouseWheel>", _on_mousewheel)
    
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
            self.status_var.set("Loading variable values...")
            
            # Get all variables
            variables = self.db_manager.get_template_variables()
            
            # Store variable data
            for var in variables:
                self.variable_data[var.name] = var
            
            # Update listboxes with values
            for var_name in self.variables:
                if var_name in self.variable_data:
                    listbox = self.variable_entries[var_name]
                    
                    # Clear existing items
                    listbox.delete(0, tk.END)
                    
                    # Add new values
                    for value in self.variable_data[var_name].values:
                        listbox.insert(tk.END, value)
            
            self.status_var.set("Ready")
            logger.debug("Variable data loaded")
            
        except Exception as e:
            error_msg = f"Failed to load variable data: {str(e)}"
            self.status_var.set(error_msg)
            logger.error(error_msg)
            messagebox.showerror("Error", error_msg)
    
    @handle_errors()
    def _process_template_selected(self):
        """Process template with selected variable values."""
        try:
            self.status_var.set("Processing selected combinations...")
            
            # Get selected values for each variable
            values_combinations = []
            for var_name in self.variables:
                listbox = self.variable_entries[var_name]
                selected_indices = listbox.curselection()
                selected_values = [listbox.get(i) for i in selected_indices]
                
                if not selected_values:
                    # If nothing selected, use empty string
                    values_combinations.append((var_name, [""]))
                else:
                    values_combinations.append((var_name, selected_values))
            
            # Generate all combinations of selected values
            from itertools import product
            value_lists = [values for _, values in values_combinations]
            var_names = [name for name, _ in values_combinations]
            
            all_combinations = []
            for combination in product(*value_lists):
                values_dict = dict(zip(var_names, combination))
                all_combinations.append(values_dict)
            
            # Process each combination
            processed_texts = []
            from ...utils.template_utils import TemplateProcessor
            processor = TemplateProcessor(self.db_manager)
            
            total_combinations = len(all_combinations)
            for i, values in enumerate(all_combinations, 1):
                self.status_var.set(f"Processing combination {i}/{total_combinations}...")
                self.update()  # Force UI update
                
                processed_text = processor.substitute_variables(
                    self.template_text,
                    values,
                    self.use_random_var.get()
                )
                processed_texts.append(processed_text)
            
            # Call callback with all processed texts
            self.status_var.set("Generating images...")
            self.on_submit(processed_texts)
            self.destroy()
            
        except Exception as e:
            error_msg = f"Failed to process template: {str(e)}"
            self.status_var.set(error_msg)
            logger.error(error_msg)
            messagebox.showerror("Error", error_msg)
    
    @handle_errors()
    def _process_template_combinations(self):
        """Process template with all possible combinations."""
        try:
            self.status_var.set("Processing all combinations...")
            
            from ...utils.template_utils import TemplateProcessor
            processor = TemplateProcessor(self.db_manager)
            
            # Get all combinations
            combinations = processor.create_variable_combinations(
                self.variables,
                limit=10  # Limit to 10 combinations to avoid too many generations
            )
            
            # Process each combination
            processed_texts = []
            total_combinations = len(combinations)
            for i, values in enumerate(combinations, 1):
                self.status_var.set(f"Processing combination {i}/{total_combinations}...")
                self.update()  # Force UI update
                
                processed_text = processor.substitute_variables(
                    self.template_text,
                    values,
                    self.use_random_var.get()
                )
                processed_texts.append(processed_text)
            
            # Call callback with all processed texts
            self.status_var.set("Generating images...")
            self.on_submit(processed_texts)
            self.destroy()
            
        except Exception as e:
            error_msg = f"Failed to process template combinations: {str(e)}"
            self.status_var.set(error_msg)
            logger.error(error_msg)
            messagebox.showerror("Error", error_msg)
    
    def _show_variable_manager(self):
        """Show the variable management dialog."""
        dialog = VariableManagementDialog(
            self,
            self.db_manager,
            self.error_handler,
            self._on_variables_updated
        )
        dialog.focus()
    
    def _on_variables_updated(self):
        """Handle variable updates."""
        self._load_variable_data()
        # Refresh only the variable entries
        for var_name in self.variables:
            for widget in self.winfo_children()[0].winfo_children():
                if isinstance(widget, ttk.LabelFrame) and widget.cget("text") == var_name:
                    # Get the listbox
                    listbox = widget.winfo_children()[-1]
                    
                    # Clear existing items
                    listbox.delete(0, tk.END)
                    
                    # Add new values
                    for value in self.variable_data[var_name].values:
                        listbox.insert(tk.END, value)
    
    def _select_all_values(self, var_name):
        """Select all values for a variable."""
        if var_name in self.variable_entries:
            listbox = self.variable_entries[var_name]
            listbox.select_set(0, tk.END)
    
    def _clear_selection(self, var_name):
        """Clear all selections for a variable."""
        if var_name in self.variable_entries:
            listbox = self.variable_entries[var_name]
            listbox.selection_clear(0, tk.END)
