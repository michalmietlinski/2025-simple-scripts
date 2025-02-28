"""Reusable scrollable frame component."""

import tkinter as tk
from tkinter import ttk

class ScrollableFrame(ttk.Frame):
    """A frame that can scroll its contents."""
    
    def __init__(self, container, *args, **kwargs):
        """Initialize scrollable frame.
        
        Args:
            container: Parent widget
            *args: Additional positional arguments for ttk.Frame
            **kwargs: Additional keyword arguments for ttk.Frame
        """
        super().__init__(container, *args, **kwargs)
        
        # Create canvas and scrollbar
        self.canvas = tk.Canvas(self)
        self.scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        
        # Create inner frame for content
        self.scrollable_frame = ttk.Frame(self.canvas)
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )
        
        # Add inner frame to canvas
        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        
        # Pack widgets
        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")
        
        # Bind mouse wheel
        self.bind_mouse_wheel()
    
    def bind_mouse_wheel(self):
        """Bind mouse wheel to scrolling."""
        def _on_mousewheel(event):
            self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        
        self.canvas.bind_all("<MouseWheel>", _on_mousewheel)
    
    def unbind_mouse_wheel(self):
        """Unbind mouse wheel when frame is not visible."""
        self.canvas.unbind_all("<MouseWheel>") 
