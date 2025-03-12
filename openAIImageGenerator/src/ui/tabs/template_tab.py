"""Tab for managing templates and variables."""

import tkinter as tk
from tkinter import ttk, messagebox
import logging
from typing import Dict, List, Any, Optional, Callable

from ...utils.error_handler import handle_errors, ValidationError
from ...utils.template_utils import TemplateProcessor

logger = logging.getLogger(__name__)

class TemplateTab(ttk.Frame):
    """Tab for template management and variable handling."""
    
    def __init__(
        self,
        parent: ttk.Notebook,
        db_manager: Any,
        on_generate: Callable[[List[str]], None],
        error_handler: Any = None
    ):
        """Initialize template tab.
        
        Args:
            parent: Parent notebook widget
            db_manager: Database manager instance
            on_generate: Callback for generation requests
            error_handler: Error handler instance
        """
        super().__init__(parent)
        self.db_manager = db_manager
        self.on_generate = on_generate
        self.error_handler = error_handler
        
        # Initialize variables
        self.current_template = None
        self.variable_entries = {}  # Will store {var_name: listbox}
        self.status_var = tk.StringVar(value="Ready")
        self.use_random_var = tk.BooleanVar(value=False)
        
        self._create_ui()
        self._load_templates()
        logger.debug("Template tab initialized")
    
    def _create_ui(self):
        """Create tab UI components."""
        # Main container with padding
        main_frame = ttk.Frame(self, padding="10")
        main_frame.pack(fill="both", expand=True)
        
        # Left side - Template List
        templates_frame = ttk.LabelFrame(
            main_frame,
            text="Templates",
            padding="5"
        )
        templates_frame.pack(side="left", fill="y", padx=(0, 10))
        
        # Template list with scrollbar
        template_list_frame = ttk.Frame(templates_frame)
        template_list_frame.pack(fill="both", expand=True)
        
        self.template_list = tk.Listbox(
            template_list_frame,
            width=30,
            selectmode="single"
        )
        template_scrollbar = ttk.Scrollbar(
            template_list_frame,
            orient="vertical",
            command=self.template_list.yview
        )
        
        self.template_list.configure(yscrollcommand=template_scrollbar.set)
        self.template_list.pack(side="left", fill="both", expand=True)
        template_scrollbar.pack(side="right", fill="y")
        
        # Template buttons
        template_buttons = ttk.Frame(templates_frame)
        template_buttons.pack(fill="x", pady=(5, 0))
        
        ttk.Button(
            template_buttons,
            text="New",
            command=self._new_template
        ).pack(side="left", padx=2)
        
        ttk.Button(
            template_buttons,
            text="Edit",
            command=self._edit_template
        ).pack(side="left", padx=2)
        
        ttk.Button(
            template_buttons,
            text="Delete",
            command=self._delete_template
        ).pack(side="left", padx=2)
        
        # Right side - Template Content
        content_frame = ttk.Frame(main_frame)
        content_frame.pack(side="left", fill="both", expand=True)
        
        # Template preview
        preview_frame = ttk.LabelFrame(
            content_frame,
            text="Template Preview",
            padding="5"
        )
        preview_frame.pack(fill="x", pady=(0, 10))
        
        self.preview_text = tk.Text(
            preview_frame,
            height=4,
            wrap="word",
            font=("Arial", 10)
        )
        self.preview_text.pack(fill="x")
        
        # Variables section
        variables_frame = ttk.LabelFrame(
            content_frame,
            text="Variable Values",
            padding="5"
        )
        variables_frame.pack(fill="both", expand=True)
        
        # Create scrollable frame for variables
        canvas = tk.Canvas(variables_frame)
        scrollbar = ttk.Scrollbar(variables_frame, orient="vertical", command=canvas.yview)
        self.scrollable_frame = ttk.Frame(canvas)
        
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Pack canvas and scrollbar
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Configure canvas scrolling
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        canvas.bind_all("<MouseWheel>", _on_mousewheel)
        
        # Bottom section
        bottom_frame = ttk.Frame(content_frame)
        bottom_frame.pack(fill="x", pady=(10, 0))
        
        # Random values option
        random_frame = ttk.Frame(bottom_frame)
        random_frame.pack(fill="x", pady=(0, 10))
        
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
            text="Generate Selected",
            command=self._process_template_selected,
            style="Primary.TButton"
        ).pack(side="right", padx=5)

        ttk.Button(
            right_buttons,
            text="Generate All",
            command=self._process_template_combinations
        ).pack(side="right", padx=5)
        
        # Status bar
        status_frame = ttk.Frame(content_frame)
        status_frame.pack(side="bottom", fill="x", pady=(5, 0))
        
        ttk.Separator(status_frame, orient="horizontal").pack(fill="x")
        
        ttk.Label(
            status_frame,
            textvariable=self.status_var,
            font=("Arial", 9)
        ).pack(side="left", pady=5)
        
        # Bind template selection
        self.template_list.bind('<<ListboxSelect>>', self._on_template_selected)
    
    @handle_errors()
    def _load_templates(self):
        """Load templates from database."""
        try:
            self.status_var.set("Loading templates...")
            
            # Clear list
            self.template_list.delete(0, tk.END)
            
            # Get templates
            templates = self.db_manager.get_templates()
            
            # Add to list
            for template in templates:
                self.template_list.insert(tk.END, template.name)
            
            self.status_var.set("Ready")
            logger.debug("Templates loaded")
            
        except Exception as e:
            error_msg = f"Failed to load templates: {str(e)}"
            self.status_var.set(error_msg)
            logger.error(error_msg)
            messagebox.showerror("Error", error_msg)
    
    def _on_template_selected(self, event):
        """Handle template selection."""
        try:
            # Get selected template
            selection = self.template_list.curselection()
            if not selection:
                return
                
            template_name = self.template_list.get(selection[0])
            template = self.db_manager.get_template_by_name(template_name)
            
            if not template:
                return
                
            self.current_template = template
            
            # Update preview
            self.preview_text.config(state="normal")
            self.preview_text.delete("1.0", tk.END)
            self.preview_text.insert("1.0", template.text)
            self.preview_text.config(state="disabled")
            
            # Clear variable frame
            for widget in self.scrollable_frame.winfo_children():
                widget.destroy()
            
            self.variable_entries.clear()
            
            # Create variable entries
            for var_name in template.variables:
                var_frame = ttk.LabelFrame(
                    self.scrollable_frame,
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
            
            # Load variable values
            self._load_variable_data()
            
        except Exception as e:
            error_msg = f"Failed to load template: {str(e)}"
            self.status_var.set(error_msg)
            logger.error(error_msg)
            messagebox.showerror("Error", error_msg)
    
    @handle_errors()
    def _load_variable_data(self):
        """Load variable data from database."""
        try:
            self.status_var.set("Loading variable values...")
            
            # Get all variables
            variables = self.db_manager.get_template_variables()
            
            # Update listboxes with values
            for var_name, listbox in self.variable_entries.items():
                # Clear existing items
                listbox.delete(0, tk.END)
                
                # Find matching variable
                for var in variables:
                    if var.name == var_name:
                        # Add values
                        for value in var.values:
                            listbox.insert(tk.END, value)
                        break
            
            self.status_var.set("Ready")
            logger.debug("Variable data loaded")
            
        except Exception as e:
            error_msg = f"Failed to load variable data: {str(e)}"
            self.status_var.set(error_msg)
            logger.error(error_msg)
            messagebox.showerror("Error", error_msg)
    
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
    
    @handle_errors()
    def _process_template_selected(self):
        """Process template with selected variable values."""
        if not self.current_template:
            messagebox.showinfo("Info", "Please select a template first")
            return
            
        try:
            self.status_var.set("Processing selected combinations...")
            
            # Get selected values for each variable
            values_combinations = []
            for var_name, listbox in self.variable_entries.items():
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
            processor = TemplateProcessor(self.db_manager)
            
            total_combinations = len(all_combinations)
            for i, values in enumerate(all_combinations, 1):
                self.status_var.set(f"Processing combination {i}/{total_combinations}...")
                self.update()  # Force UI update
                
                processed_text = processor.substitute_variables(
                    self.current_template.text,
                    values,
                    self.use_random_var.get()
                )
                processed_texts.append(processed_text)
            
            # Call generation callback
            self.status_var.set("Generating images...")
            self.on_generate(processed_texts)
            
            self.status_var.set("Ready")
            
        except Exception as e:
            error_msg = f"Failed to process template: {str(e)}"
            self.status_var.set(error_msg)
            logger.error(error_msg)
            messagebox.showerror("Error", error_msg)
    
    @handle_errors()
    def _process_template_combinations(self):
        """Process template with all possible combinations."""
        if not self.current_template:
            messagebox.showinfo("Info", "Please select a template first")
            return
            
        try:
            self.status_var.set("Processing all combinations...")
            
            processor = TemplateProcessor(self.db_manager)
            
            # Get all combinations
            combinations = processor.create_variable_combinations(
                self.current_template.variables,
                limit=10  # Limit to 10 combinations to avoid too many generations
            )
            
            # Process each combination
            processed_texts = []
            total_combinations = len(combinations)
            for i, values in enumerate(combinations, 1):
                self.status_var.set(f"Processing combination {i}/{total_combinations}...")
                self.update()  # Force UI update
                
                processed_text = processor.substitute_variables(
                    self.current_template.text,
                    values,
                    self.use_random_var.get()
                )
                processed_texts.append(processed_text)
            
            # Call generation callback
            self.status_var.set("Generating images...")
            self.on_generate(processed_texts)
            
            self.status_var.set("Ready")
            
        except Exception as e:
            error_msg = f"Failed to process template combinations: {str(e)}"
            self.status_var.set(error_msg)
            logger.error(error_msg)
            messagebox.showerror("Error", error_msg)
    
    def _new_template(self):
        """Create new template."""
        # TODO: Implement template creation dialog
        pass
    
    def _edit_template(self):
        """Edit selected template."""
        # TODO: Implement template editing dialog
        pass
    
    def _delete_template(self):
        """Delete selected template."""
        # TODO: Implement template deletion with confirmation
        pass
    
    def _show_variable_manager(self):
        """Show variable management dialog."""
        from ..dialogs.variable_management_dialog import VariableManagementDialog
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
