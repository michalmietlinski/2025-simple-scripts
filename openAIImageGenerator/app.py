import os
import logging
import tkinter as tk
from tkinter import messagebox, Text, Frame, Label, Button, StringVar, OptionMenu, filedialog, simpledialog
import tkinter.ttk as ttk
from PIL import Image, ImageTk
from io import BytesIO
from dotenv import load_dotenv
from utils.openai_client import OpenAIClient
from utils.file_manager import FileManager
from utils.usage_tracker import UsageTracker
from utils.database_manager import DatabaseManager
from utils.data_models import Prompt, Generation
from config import APP_CONFIG, ensure_directories
from datetime import datetime
import json
import sqlite3

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("app.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

class DALLEGeneratorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("DALL-E Image Generator")
        self.root.geometry("1400x1000")
        
        # Check for API key
        self.api_key = os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            self.show_api_key_dialog()
        
        # Setup main UI components
        self.setup_ui()
    
    def setup_ui(self):
        # Placeholder for UI setup
        main_label = tk.Label(self.root, text="DALL-E Image Generator", font=("Arial", 24))
        main_label.pack(pady=20)
        
        # API key status
        if self.api_key:
            status_label = tk.Label(self.root, text="API Key: ✓ Connected", fg="green", font=("Arial", 10))
        else:
            status_label = tk.Label(self.root, text="API Key: ✗ Not Found", fg="red", font=("Arial", 10))
        status_label.pack()
        
        # Create notebook for tabs
        self.notebook = self.create_styled_notebook(
            self.root,
            selected_bg_color="#4CAF50",
            selected_fg_color="white",
            font=("Arial", 10, "bold")
        )
        self.notebook.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Create tabs
        self.generation_tab = tk.Frame(self.notebook)
        self.history_tab = tk.Frame(self.notebook)
        
        self.notebook.add(self.generation_tab, text="Generate Images")
        self.notebook.add(self.history_tab, text="History")
        
        # Setup image generation UI in the generation tab
        self.setup_image_generation_ui()
        
        # Setup history UI in the history tab
        self.setup_history_ui()
    
    def show_api_key_dialog(self):
        dialog = tk.Toplevel(self.root)
        dialog.title("API Key Required")
        dialog.geometry("400x200")
        dialog.transient(self.root)
        
        tk.Label(dialog, text="Please enter your OpenAI API Key:", font=("Arial", 12)).pack(pady=10)
        
        api_key_var = tk.StringVar()
        entry = tk.Entry(dialog, textvariable=api_key_var, width=40, show="*")
        entry.pack(pady=10)
        
        def save_key():
            key = api_key_var.get().strip()
            if key:
                # Save to .env file
                with open(".env", "w") as f:
                    f.write(f"OPENAI_API_KEY={key}")
                self.api_key = key
                dialog.destroy()
                messagebox.showinfo("Success", "API Key saved successfully!")
                # Reload environment variables
                load_dotenv()
            else:
                messagebox.showerror("Error", "API Key cannot be empty")
        
        tk.Button(dialog, text="Save", command=save_key).pack(pady=10)
        
        # Make dialog modal
        dialog.grab_set()
        dialog.focus_set()

    def test_api_key(self):
        """Test if the API key is valid."""
        try:
            client = OpenAIClient()
            if client.validate_api_key():
                messagebox.showinfo("Success", "API key is valid!")
            else:
                messagebox.showerror("Error", "API key validation failed.")
        except Exception as e:
            messagebox.showerror("Error", f"Error testing API key: {str(e)}")

    def run_verification(self, structure_label, config_label, utils_label):
        """Run basic verification checks."""
        # Check project structure
        if os.path.isdir("utils") and os.path.isdir("outputs") and os.path.isdir("data"):
            structure_label.config(text="Project Structure: ✓ Verified", fg="green")
        else:
            structure_label.config(text="Project Structure: ✗ Issues found", fg="red")
        
        # Check configuration
        try:
            ensure_directories()
            config_label.config(text="Configuration: ✓ Verified", fg="green")
        except Exception as e:
            config_label.config(text="Configuration: ✗ Error - " + str(e), fg="red")
        
        # Check utility modules
        try:
            utils_label.config(text="Utility Modules: ✓ Verified", fg="green")
        except Exception as e:
            utils_label.config(text="Utility Modules: ✗ Error - " + str(e), fg="red")

    def setup_image_generation_ui(self):
        """Set up the image generation UI components."""
        # Create a frame for image generation
        generation_frame = Frame(self.generation_tab, padx=20, pady=20)
        generation_frame.pack(fill="both", expand=True)
        
        # Prompt input
        Label(generation_frame, text="Enter your prompt:", font=("Arial", 12)).pack(anchor="w", pady=(0, 5))
        self.prompt_text = Text(generation_frame, height=5, width=60)
        self.prompt_text.pack(fill="x", pady=(0, 10))
        
        # Image size selection
        size_frame = Frame(generation_frame)
        size_frame.pack(fill="x", pady=(0, 10))
        
        Label(size_frame, text="Image Size:", font=("Arial", 10)).pack(side="left", padx=(0, 10))
        
        self.size_var = StringVar(value=APP_CONFIG["default_image_size"])
        # Initialize with default sizes
        self.sizes = ["256x256", "512x512", "1024x1024"]
        self.size_menu = self.create_styled_dropdown(size_frame, self.size_var, self.sizes)
        self.size_menu.pack(side="left", padx=(0, 20))
        
        # Quality and style options (will be shown/hidden based on model)
        self.quality_frame = Frame(size_frame)
        self.quality_frame.pack(side="left", padx=(0, 10))
        
        self.quality_label = Label(self.quality_frame, text="Quality:", font=("Arial", 10))
        self.quality_var = StringVar(value=APP_CONFIG["default_image_quality"])
        self.quality_menu = self.create_styled_dropdown(self.quality_frame, self.quality_var, ["standard", "hd"])
        
        self.style_frame = Frame(size_frame)
        self.style_frame.pack(side="left")
        
        self.style_label = Label(self.style_frame, text="Style:", font=("Arial", 10))
        self.style_var = StringVar(value=APP_CONFIG["default_image_style"])
        self.style_menu = self.create_styled_dropdown(self.style_frame, self.style_var, ["vivid", "natural"])
        
        # Model info label
        self.model_label = Label(size_frame, text="Detecting model...", font=("Arial", 10, "italic"))
        self.model_label.pack(side="left", padx=(10, 0))
        
        # Generate button
        generate_btn = self.create_styled_button(
            generation_frame, 
            text="Generate Image", 
            command=self.generate_image, 
            bg_color="#4CAF50", 
            fg_color="white", 
            font=("Arial", 12, "bold"), 
            padx=20, 
            pady=10
        )
        generate_btn.pack(pady=20)
        
        # Image preview area - increase size to 800x800
        self.preview_frame = Frame(generation_frame, bg="#f0f0f0", width=800, height=800)
        self.preview_frame.pack(pady=20)
        self.preview_frame.pack_propagate(False)  # Prevent frame from shrinking
        
        self.preview_label = Label(self.preview_frame, text="Image preview will appear here", bg="#f0f0f0")
        self.preview_label.pack(expand=True)
        
        # Add note about auto-saving
        auto_save_note = Label(generation_frame, text="Images are automatically saved to the outputs folder", font=("Arial", 10, "italic"), fg="gray")
        auto_save_note.pack(pady=(0, 20))
        
        # Initialize clients
        self.openai_client = None
        self.file_manager = None
        self.usage_tracker = None
        self.db_manager = None
        self.current_image = None
        
        # Initialize clients if API key is available
        if self.api_key:
            try:
                self.openai_client = OpenAIClient()
                self.file_manager = FileManager()
                self.usage_tracker = UsageTracker()
                self.db_manager = DatabaseManager()
                # Update UI based on model capabilities
                self.update_ui_for_model()
            except Exception as e:
                logger.error(f"Failed to initialize clients: {str(e)}")

    def update_ui_for_model(self):
        """Update UI elements based on the detected model capabilities."""
        if not self.openai_client:
            return
        
        try:
            # Get model capabilities
            capabilities = self.openai_client.get_model_capabilities()
            model = self.openai_client.model
            
            # Update model label
            self.model_label.config(text=f"Using {model}")
            
            # Update size options
            self.size_var.set(capabilities["max_size"])
            
            # Remove old size menu and create new one with updated sizes
            self.size_menu.destroy()
            self.size_menu = self.create_styled_dropdown(self.size_menu.master, self.size_var, capabilities["sizes"])
            self.size_menu.pack(side="left", padx=(0, 20))
            
            # Show/hide quality and style options based on model capabilities
            if capabilities["supports_quality"]:
                self.quality_label.pack(side="left", padx=(0, 5))
                self.quality_menu.pack(side="left", padx=(0, 10))
            else:
                self.quality_label.pack_forget()
                self.quality_menu.pack_forget()
                
            if capabilities["supports_style"]:
                self.style_label.pack(side="left", padx=(0, 5))
                self.style_menu.pack(side="left")
            else:
                self.style_label.pack_forget()
                self.style_menu.pack_forget()
                
        except Exception as e:
            logger.error(f"Error updating UI for model: {str(e)}")
            self.model_label.config(text="Error detecting model")

    def generate_image(self):
        """Generate an image based on the prompt."""
        # Get prompt from text area
        prompt = self.prompt_text.get("1.0", "end-1c").strip()
        
        if not prompt:
            messagebox.showerror("Error", "Please enter a prompt")
            return
        
        # Check if clients are initialized
        if not self.openai_client:
            try:
                self.openai_client = OpenAIClient()
                self.file_manager = FileManager()
                self.usage_tracker = UsageTracker()
                self.db_manager = DatabaseManager()
                # Update UI based on model capabilities
                self.update_ui_for_model()
            except Exception as e:
                messagebox.showerror("Error", f"Failed to initialize OpenAI client: {str(e)}")
                return
        
        # Get parameters
        size = self.size_var.get()
        
        # Get quality and style if supported by the model
        capabilities = self.openai_client.get_model_capabilities()
        quality = self.quality_var.get() if capabilities["supports_quality"] else None
        style = self.style_var.get() if capabilities["supports_style"] else None
        
        # Update UI to show loading state
        self.preview_label.config(text="Generating image... Please wait.")
        self.root.update()
        
        # Add prompt to database
        try:
            prompt_id = self.db_manager.add_prompt(prompt)
            logger.info(f"Added prompt to database with ID: {prompt_id}")
        except Exception as e:
            logger.error(f"Error adding prompt to database: {str(e)}")
            prompt_id = None
        
        # Generate image
        try:
            image_data, usage_info = self.openai_client.generate_image(
                prompt, 
                size=size,
                quality=quality,
                style=style
            )
            
            if image_data and usage_info:
                # Check if this is a billing error
                if usage_info.get("model") == "billing_error":
                    messagebox.showwarning(
                        "Billing Error", 
                        "Your OpenAI account has reached its billing limit.\n\n"
                        "To fix this:\n"
                        "1. Go to platform.openai.com\n"
                        "2. Check your billing settings\n"
                        "3. Add a payment method or increase limits"
                    )
                
                # Record usage
                self.usage_tracker.record_usage(
                    usage_info["estimated_tokens"],
                    cost=usage_info["estimated_tokens"] * 0.00002
                )
                
                # Display image
                self.display_image(image_data)
                
                # Store current image
                self.current_image = {
                    "data": image_data,
                    "prompt": prompt
                }
                
                # Auto-save the image
                try:
                    logger.info("Auto-saving image after generation...")
                    # Ensure file manager is initialized
                    if not self.file_manager:
                        self.file_manager = FileManager()
                    
                    # Create a timestamp for the filename
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    
                    # Save the image with a default description including timestamp
                    output_path = self.file_manager.save_image(
                        image_data,
                        prompt,
                        f"auto_saved_{timestamp}"
                    )
                    
                    if output_path and os.path.exists(output_path):
                        file_size = os.path.getsize(output_path)
                        logger.info(f"Image auto-saved successfully to {output_path}, size: {file_size} bytes")
                        
                        # Record generation in database
                        if prompt_id is not None and self.db_manager:
                            try:
                                # Prepare parameters for database
                                parameters = {
                                    "size": size,
                                    "model": usage_info.get("model", "unknown")
                                }
                                if quality:
                                    parameters["quality"] = quality
                                if style:
                                    parameters["style"] = style
                                
                                # Add generation to database
                                generation_id = self.db_manager.add_generation(
                                    prompt_id=prompt_id,
                                    image_path=output_path,
                                    parameters=parameters,
                                    token_usage=usage_info["estimated_tokens"],
                                    cost=usage_info["estimated_tokens"] * 0.00002,
                                    description=f"auto_saved_{timestamp}"
                                )
                                logger.info(f"Added generation to database with ID: {generation_id}")
                            except Exception as e:
                                logger.error(f"Error recording generation in database: {str(e)}")
                        
                        # Show success message with the saved path
                        messagebox.showinfo("Success", f"Image generated and saved to:\n{output_path}")
                        
                        # Open the containing folder
                        try:
                            os.startfile(os.path.dirname(output_path))
                        except Exception as e:
                            logger.error(f"Failed to open containing folder: {str(e)}")
                    else:
                        logger.error("Failed to auto-save image")
                        messagebox.showinfo("Success", "Image generated successfully, but could not be saved automatically.")
                except Exception as e:
                    logger.error(f"Error during auto-save: {str(e)}")
                    import traceback
                    logger.error(f"Auto-save traceback: {traceback.format_exc()}")
                    messagebox.showinfo("Success", "Image generated successfully, but could not be saved automatically.")
            else:
                messagebox.showerror("Error", "Failed to generate image")
        except Exception as e:
            messagebox.showerror("Error", f"Error generating image: {str(e)}")
            logger.error(f"Error generating image: {str(e)}")

    def display_image(self, image_data):
        """Display the generated image in the preview area."""
        try:
            # Clear previous content
            for widget in self.preview_frame.winfo_children():
                widget.destroy()
            
            # Convert bytes to PIL Image
            image = Image.open(BytesIO(image_data))
            
            # Get the actual frame dimensions
            preview_width = self.preview_frame.winfo_width()
            preview_height = self.preview_frame.winfo_height()
            
            # If the frame hasn't been properly sized yet, use default values
            if preview_width < 50:  # Arbitrary small value indicating the frame isn't properly sized yet
                preview_width = 580
            if preview_height < 50:
                preview_height = 580
            
            # Calculate scaling factor to fit image within preview
            width_ratio = preview_width / image.width
            height_ratio = preview_height / image.height
            scale_factor = min(width_ratio, height_ratio, 1.0)  # Don't upscale small images
            
            new_width = int(image.width * scale_factor)
            new_height = int(image.height * scale_factor)
            
            # Resize image for display
            resized_image = image.resize((new_width, new_height), Image.LANCZOS)
            
            # Convert to PhotoImage for Tkinter
            tk_image = ImageTk.PhotoImage(resized_image)
            
            # Create a container frame for the image and buttons
            container_frame = Frame(self.preview_frame, bg="#f0f0f0")
            container_frame.pack(expand=True, fill="both")
            
            # Create label to display image
            image_label = Label(container_frame, image=tk_image)
            image_label.image = tk_image  # Keep a reference to prevent garbage collection
            image_label.pack(expand=True, pady=(0, 10))
            
            # Store original image for full resolution view
            self.original_image = image
            
            # Create buttons frame
            buttons_frame = Frame(container_frame, bg="#f0f0f0")
            buttons_frame.pack(pady=(0, 10))
            
            # Add button to view in original resolution
            view_original_btn = self.create_styled_button(
                buttons_frame, 
                text="View Full Resolution", 
                command=self.view_original_resolution,
                bg_color="#4CAF50", 
                fg_color="white", 
                font=("Arial", 10, "bold"),
                padx=10
            )
            view_original_btn.pack(side="left", padx=5)
            
            # Add button to open output directory
            open_dir_btn = self.create_styled_button(
                buttons_frame, 
                text="Open Output Folder", 
                command=self.open_output_directory,
                bg_color="#2196F3", 
                fg_color="white", 
                font=("Arial", 10, "bold"),
                padx=10
            )
            open_dir_btn.pack(side="left", padx=5)
            
        except Exception as e:
            logger.error(f"Error displaying image: {str(e)}")
            Label(self.preview_frame, text=f"Error displaying image: {str(e)}", bg="#f0f0f0").pack(expand=True)
    
    def view_original_resolution(self):
        """Display the image in its original resolution in a new window."""
        if not hasattr(self, 'original_image'):
            messagebox.showerror("Error", "No image available")
            return
        
        try:
            # Create a new top-level window
            top = tk.Toplevel(self.root)
            top.title("Full Resolution Image")
            
            # Get screen dimensions
            screen_width = top.winfo_screenwidth()
            screen_height = top.winfo_screenheight()
            
            # Calculate window size (80% of screen size)
            window_width = int(screen_width * 0.8)
            window_height = int(screen_height * 0.8)
            
            # Set window size and position
            top.geometry(f"{window_width}x{window_height}+{int(screen_width*0.1)}+{int(screen_height*0.1)}")
            
            # Create a canvas with scrollbars
            canvas_frame = Frame(top)
            canvas_frame.pack(fill="both", expand=True, padx=10, pady=10)
            
            h_scrollbar = tk.Scrollbar(canvas_frame, orient="horizontal")
            v_scrollbar = tk.Scrollbar(canvas_frame)
            
            canvas = tk.Canvas(
                canvas_frame, 
                xscrollcommand=h_scrollbar.set,
                yscrollcommand=v_scrollbar.set
            )
            
            h_scrollbar.config(command=canvas.xview)
            v_scrollbar.config(command=canvas.yview)
            
            h_scrollbar.pack(side="bottom", fill="x")
            v_scrollbar.pack(side="right", fill="y")
            canvas.pack(side="left", fill="both", expand=True)
            
            # Convert PIL Image to PhotoImage
            tk_image = ImageTk.PhotoImage(self.original_image)
            
            # Add image to canvas
            canvas.create_image(0, 0, image=tk_image, anchor="nw")
            canvas.image = tk_image  # Keep a reference
            
            # Configure canvas scroll region
            canvas.config(scrollregion=canvas.bbox("all"))
            
            # Add close button
            close_btn = self.create_styled_button(
                top, 
                text="Close", 
                command=top.destroy, 
                bg_color="#f44336", 
                fg_color="white", 
                font=("Arial", 10, "bold"),
                padx=20,
                pady=8
            )
            close_btn.pack(pady=10)
            
        except Exception as e:
            logger.error(f"Error displaying original resolution: {str(e)}")
            messagebox.showerror("Error", f"Failed to display image: {str(e)}")
    
    def open_output_directory(self):
        """Open the output directory in file explorer."""
        try:
            if not self.file_manager:
                self.file_manager = FileManager()
            
            # Get today's output directory
            today_dir = self.file_manager.ensure_directories()
            
            # Open the directory
            if os.path.exists(today_dir):
                os.startfile(today_dir)
            else:
                messagebox.showerror("Error", "Output directory not found")
        except Exception as e:
            logger.error(f"Failed to open output directory: {str(e)}")
            messagebox.showerror("Error", f"Failed to open output directory: {str(e)}")

    def save_image(self):
        """Save the current image."""
        if not self.current_image:
            messagebox.showerror("Error", "No image to save")
            return
        
        try:
            # Ensure output directories exist
            if not self.file_manager:
                self.file_manager = FileManager()
            
            # Force recreation of output directories
            today_dir = self.file_manager.ensure_directories()
            logger.info(f"Ensuring output directory exists: {today_dir}")
            
            # Debug the current image data
            image_data = self.current_image["data"]
            if isinstance(image_data, str) and image_data.startswith('http'):
                # We have a URL instead of binary data
                logger.info(f"Image data is a URL: {image_data[:50]}...")
                messagebox.showerror("Error", "Cannot save image from URL in this version. Please try again with b64_json format.")
                return
            
            # Check if we have valid image data
            if not image_data or not isinstance(image_data, bytes):
                logger.error(f"Invalid image data type: {type(image_data)}")
                messagebox.showerror("Error", f"Invalid image data type: {type(image_data)}")
                return
            
            # Log image data size
            logger.info(f"Image data size: {len(image_data)} bytes")
            
            # Verify image data is valid by trying to open it
            try:
                test_image = Image.open(BytesIO(image_data))
                logger.info(f"Image data is valid: {test_image.format} image, size {test_image.width}x{test_image.height}")
            except Exception as e:
                logger.error(f"Image data is not a valid image: {str(e)}")
                messagebox.showerror("Error", f"Image data is not valid: {str(e)}")
                return
            
            # Ask for description
            description = simpledialog.askstring("Image Description", "Enter a description for this image (optional):")
            
            # Create a backup of the image data in case saving fails
            backup_path = os.path.join(os.getcwd(), "backup_image.png")
            try:
                with open(backup_path, "wb") as f:
                    f.write(image_data)
                logger.info(f"Created backup image at {backup_path}")
            except Exception as e:
                logger.warning(f"Failed to create backup image: {str(e)}")
            
            # Save image
            logger.info(f"Attempting to save image with prompt: {self.current_image['prompt'][:30]}...")
            output_path = self.file_manager.save_image(
                image_data, 
                self.current_image["prompt"],
                description
            )
            
            if output_path:
                # Verify the file was actually created
                if os.path.exists(output_path):
                    file_size = os.path.getsize(output_path)
                    logger.info(f"Image saved successfully. File size: {file_size} bytes")
                    
                    # No success message - removed
                else:
                    # Try to use the backup
                    backup_dir = os.path.dirname(output_path)
                    backup_filename = os.path.basename(output_path)
                    new_path = os.path.join(backup_dir, "backup_" + backup_filename)
                    
                    try:
                        # Ensure directory exists
                        os.makedirs(backup_dir, exist_ok=True)
                        # Copy backup to outputs folder
                        import shutil
                        shutil.copy2(backup_path, new_path)
                        logger.info(f"Used backup image to save to: {new_path}")
                        
                        # No success message - removed
                    except Exception as e:
                        messagebox.showerror("Error", f"Failed to save image. File not found at: {output_path}")
                        logger.error(f"File not found after save attempt: {output_path}")
                        logger.error(f"Backup save also failed: {str(e)}")
            else:
                messagebox.showerror("Error", "Failed to save image")
        except Exception as e:
            messagebox.showerror("Error", f"Error saving image: {str(e)}")
            logger.error(f"Error saving image: {str(e)}")
            # Log the full exception traceback
            import traceback
            logger.error(f"Exception traceback: {traceback.format_exc()}")

    def setup_history_ui(self):
        """Set up the history UI components for prompt and generation history."""
        # Create a frame for history
        history_frame = Frame(self.history_tab, padx=20, pady=20)
        history_frame.pack(fill="both", expand=True)
        
        # Create sub-tabs for prompt history and generation history
        history_notebook = self.create_styled_notebook(
            history_frame,
            selected_bg_color="#2196F3",
            selected_fg_color="white",
            font=("Arial", 10)
        )
        history_notebook.pack(fill="both", expand=True)
        
        # Create sub-tabs
        prompt_history_tab = Frame(history_notebook)
        generation_history_tab = Frame(history_notebook)
        template_management_tab = Frame(history_notebook)
        
        history_notebook.add(prompt_history_tab, text="Prompt History")
        history_notebook.add(generation_history_tab, text="Generation History")
        history_notebook.add(template_management_tab, text="Template Management")
        
        # Setup prompt history UI
        self.setup_prompt_history_ui(prompt_history_tab)
        
        # Setup generation history UI
        self.setup_generation_history_ui(generation_history_tab)
        
        # Setup template management UI
        self.setup_template_management_ui(template_management_tab)
    
    def setup_prompt_history_ui(self, parent_frame):
        """Set up the prompt history UI components."""
        # Create a frame for controls
        controls_frame = Frame(parent_frame, padx=10, pady=10)
        controls_frame.pack(fill="x")
        
        # Search box
        Label(controls_frame, text="Search:", font=("Arial", 10)).pack(side="left", padx=(0, 5))
        self.prompt_search_var = StringVar()
        search_entry = tk.Entry(controls_frame, textvariable=self.prompt_search_var, width=30)
        search_entry.pack(side="left", padx=(0, 10))
        
        # Search button
        search_btn = self.create_styled_button(
            controls_frame, 
            text="Search", 
            command=self.search_prompts,
            bg_color="#2196F3",
            fg_color="white"
        )
        search_btn.pack(side="left", padx=(0, 20))
        
        # Favorites only checkbox
        self.favorites_only_var = tk.BooleanVar(value=False)
        favorites_check = tk.Checkbutton(controls_frame, text="Favorites Only", variable=self.favorites_only_var, command=self.search_prompts)
        favorites_check.pack(side="left", padx=(0, 20))
        
        # Clear all prompts button
        clear_all_btn = self.create_styled_button(
            controls_frame, 
            text="Clear All", 
            command=self.clear_all_prompts, 
            bg_color="#ff6b6b", 
            fg_color="white"
        )
        clear_all_btn.pack(side="right", padx=(10, 0))
        
        # Refresh button
        refresh_btn = self.create_styled_button(
            controls_frame, 
            text="Refresh", 
            command=self.search_prompts,
            bg_color="#9e9e9e",
            fg_color="white"
        )
        refresh_btn.pack(side="right")
        
        # Create a frame for the prompt list
        list_frame = Frame(parent_frame, padx=10, pady=10)
        list_frame.pack(fill="both", expand=True)
        
        # Create a listbox with scrollbar
        scrollbar = tk.Scrollbar(list_frame)
        scrollbar.pack(side="right", fill="y")
        
        self.prompt_listbox = tk.Listbox(list_frame, yscrollcommand=scrollbar.set, font=("Arial", 10), height=15)
        self.prompt_listbox.pack(side="left", fill="both", expand=True)
        scrollbar.config(command=self.prompt_listbox.yview)
        
        # Bind selection event
        self.prompt_listbox.bind('<<ListboxSelect>>', self.on_prompt_selected)
        
        # Create a frame for prompt details
        details_frame = Frame(parent_frame, padx=10, pady=10)
        details_frame.pack(fill="x")
        
        # Prompt text
        Label(details_frame, text="Prompt:", font=("Arial", 10, "bold")).pack(anchor="w")
        self.selected_prompt_text = Text(details_frame, height=3, width=60, wrap="word")
        self.selected_prompt_text.pack(fill="x", pady=(0, 10))
        
        # Action buttons
        buttons_frame = Frame(details_frame)
        buttons_frame.pack(fill="x")
        
        use_btn = self.create_styled_button(
            buttons_frame, 
            text="Use Prompt", 
            command=self.use_selected_prompt,
            bg_color="#4CAF50",
            fg_color="white"
        )
        use_btn.pack(side="left", padx=(0, 10))
        
        favorite_btn = self.create_styled_button(
            buttons_frame, 
            text="Toggle Favorite", 
            command=self.toggle_favorite_prompt,
            bg_color="#FFC107",
            fg_color="black"
        )
        favorite_btn.pack(side="left", padx=(0, 10))
        
        delete_btn = self.create_styled_button(
            buttons_frame, 
            text="Delete", 
            command=self.delete_selected_prompt, 
            bg_color="#ff6b6b", 
            fg_color="white"
        )
        delete_btn.pack(side="left", padx=(0, 10))
        
        # Load initial prompts
        self.search_prompts()
    
    def setup_generation_history_ui(self, parent_frame):
        """Set up the generation history UI components."""
        # Create a frame for controls
        controls_frame = Frame(parent_frame, padx=10, pady=10)
        controls_frame.pack(fill="x")
        
        # Date range
        Label(controls_frame, text="From:", font=("Arial", 10)).pack(side="left", padx=(0, 5))
        self.date_from_var = StringVar()
        date_from_entry = tk.Entry(controls_frame, textvariable=self.date_from_var, width=10)
        date_from_entry.pack(side="left", padx=(0, 10))
        
        Label(controls_frame, text="To:", font=("Arial", 10)).pack(side="left", padx=(0, 5))
        self.date_to_var = StringVar()
        date_to_entry = tk.Entry(controls_frame, textvariable=self.date_to_var, width=10)
        date_to_entry.pack(side="left", padx=(0, 10))
        
        # Search button
        search_btn = self.create_styled_button(
            controls_frame, 
            text="Search", 
            command=self.search_generations,
            bg_color="#2196F3",
            fg_color="white"
        )
        search_btn.pack(side="left", padx=(0, 20))
        
        # Clear all generations button
        clear_all_btn = self.create_styled_button(
            controls_frame, 
            text="Clear All", 
            command=self.clear_all_generations, 
            bg_color="#ff6b6b", 
            fg_color="white"
        )
        clear_all_btn.pack(side="right", padx=(10, 0))
        
        # Refresh button
        refresh_btn = self.create_styled_button(
            controls_frame, 
            text="Refresh", 
            command=self.search_generations,
            bg_color="#9e9e9e",
            fg_color="white"
        )
        refresh_btn.pack(side="right")
        
        # Create a frame for the generation list
        list_frame = Frame(parent_frame, padx=10, pady=10)
        list_frame.pack(fill="both", expand=True)
        
        # Create a listbox with scrollbar
        scrollbar = tk.Scrollbar(list_frame)
        scrollbar.pack(side="right", fill="y")
        
        self.generation_listbox = tk.Listbox(list_frame, yscrollcommand=scrollbar.set, font=("Arial", 10), height=15)
        self.generation_listbox.pack(side="left", fill="both", expand=True)
        scrollbar.config(command=self.generation_listbox.yview)
        
        # Bind selection event
        self.generation_listbox.bind('<<ListboxSelect>>', self.on_generation_selected)
        
        # Create a frame for generation details
        details_frame = Frame(parent_frame, padx=10, pady=10)
        details_frame.pack(fill="x")
        
        # Generation details
        Label(details_frame, text="Details:", font=("Arial", 10, "bold")).pack(anchor="w")
        self.generation_details_text = Text(details_frame, height=5, width=60, wrap="word")
        self.generation_details_text.pack(fill="x", pady=(0, 10))
        
        # Action buttons
        buttons_frame = Frame(details_frame)
        buttons_frame.pack(fill="x")
        
        view_btn = self.create_styled_button(
            buttons_frame, 
            text="View Image", 
            command=self.view_selected_generation,
            bg_color="#4CAF50",
            fg_color="white"
        )
        view_btn.pack(side="left", padx=(0, 10))
        
        use_prompt_btn = self.create_styled_button(
            buttons_frame, 
            text="Use Prompt", 
            command=self.use_selected_generation_prompt,
            bg_color="#2196F3",
            fg_color="white"
        )
        use_prompt_btn.pack(side="left", padx=(0, 10))
        
        delete_btn = self.create_styled_button(
            buttons_frame, 
            text="Delete", 
            command=self.delete_selected_generation, 
            bg_color="#ff6b6b", 
            fg_color="white"
        )
        delete_btn.pack(side="left", padx=(0, 10))
        
        # Load initial generations
        self.search_generations()
    
    def search_prompts(self):
        """Search for prompts based on current filters."""
        if not self.db_manager:
            try:
                self.db_manager = DatabaseManager()
            except Exception as e:
                messagebox.showerror("Error", f"Failed to initialize database: {str(e)}")
                return
        
        try:
            # Get search parameters
            search_term = self.prompt_search_var.get().strip()
            favorites_only = self.favorites_only_var.get()
            
            # Get prompts from database
            prompts = self.db_manager.get_prompt_history(
                limit=50,
                search=search_term if search_term else None,
                favorites_only=favorites_only
            )
            
            # Clear listbox
            self.prompt_listbox.delete(0, tk.END)
            
            # Store prompt IDs in a list for reference
            self.prompt_ids = []
            
            # Add prompts to listbox
            for prompt in prompts:
                # Format display text
                display_text = f"{prompt['prompt_text'][:50]}{'...' if len(prompt['prompt_text']) > 50 else ''}"
                if prompt['favorite']:
                    display_text = "★ " + display_text
                
                # Store the prompt ID in our list
                self.prompt_ids.append(prompt['id'])
                
                # Add to listbox
                self.prompt_listbox.insert(tk.END, display_text)
            
            if not prompts:
                self.prompt_listbox.insert(tk.END, "No prompts found")
                self.prompt_ids = []
        except Exception as e:
            logger.error(f"Error searching prompts: {str(e)}")
            messagebox.showerror("Error", f"Failed to search prompts: {str(e)}")
    
    def on_prompt_selected(self, event):
        """Handle prompt selection event."""
        if not self.db_manager or not hasattr(self, 'prompt_ids'):
            return
        
        # Get selected index
        selection = self.prompt_listbox.curselection()
        if not selection or not self.prompt_ids:
            return
        
        # Get prompt ID from our list
        try:
            index = selection[0]
            if index >= len(self.prompt_ids):
                return
            
            prompt_id = self.prompt_ids[index]
            
            # Get prompt from database
            prompts = self.db_manager.get_prompt_history(limit=1, prompt_id=prompt_id)
            if not prompts:
                return
            
            prompt = prompts[0]
            
            # Update prompt text
            self.selected_prompt_text.delete("1.0", tk.END)
            self.selected_prompt_text.insert("1.0", prompt['prompt_text'])
            
            # Store selected prompt ID
            self.selected_prompt_id = prompt['id']
        except Exception as e:
            logger.error(f"Error getting prompt details: {str(e)}")
    
    def use_selected_prompt(self):
        """Use the selected prompt for image generation."""
        # Get prompt text
        prompt_text = self.selected_prompt_text.get("1.0", "end-1c").strip()
        if not prompt_text:
            return
        
        # Set prompt in generation tab
        self.notebook.select(0)  # Switch to generation tab
        self.prompt_text.delete("1.0", tk.END)
        self.prompt_text.insert("1.0", prompt_text)
    
    def toggle_favorite_prompt(self):
        """Toggle favorite status of the selected prompt."""
        if not hasattr(self, 'selected_prompt_id') or not self.db_manager:
            return
        
        try:
            # Get current prompt
            prompts = self.db_manager.get_prompt_history(limit=1, prompt_id=self.selected_prompt_id)
            if not prompts:
                return
            
            prompt = prompts[0]
            
            # Toggle favorite status
            new_favorite = not prompt['favorite']
            
            # Update in database
            self.db_manager.update_prompt(self.selected_prompt_id, favorite=new_favorite)
            
            # Refresh prompt list
            self.search_prompts()
            
            # Show confirmation
            status = "added to" if new_favorite else "removed from"
            messagebox.showinfo("Success", f"Prompt {status} favorites")
        except Exception as e:
            logger.error(f"Error toggling favorite: {str(e)}")
            messagebox.showerror("Error", f"Failed to update favorite status: {str(e)}")
    
    def search_generations(self):
        """Search for generations based on current filters."""
        if not self.db_manager:
            try:
                self.db_manager = DatabaseManager()
            except Exception as e:
                messagebox.showerror("Error", f"Failed to initialize database: {str(e)}")
                return
        
        try:
            # Get date parameters
            date_from = self.date_from_var.get().strip()
            date_to = self.date_to_var.get().strip()
            
            # Get generations from database
            generations = self.db_manager.get_generation_history(
                limit=50,
                date_from=date_from if date_from else None,
                date_to=date_to if date_to else None
            )
            
            # Clear listbox
            self.generation_listbox.delete(0, tk.END)
            
            # Store generation IDs in a list for reference
            self.generation_ids = []
            
            # Add generations to listbox
            for gen in generations:
                # Format display text
                date_str = gen['generation_date'].split('T')[0]
                prompt_text = gen['prompt_text'] if gen['prompt_text'] else "Unknown prompt"
                display_text = f"{date_str}: {prompt_text[:50]}{'...' if len(prompt_text) > 50 else ''}"
                
                # Store the generation ID in our list
                self.generation_ids.append(gen['id'])
                
                # Add to listbox
                self.generation_listbox.insert(tk.END, display_text)
            
            if not generations:
                self.generation_listbox.insert(tk.END, "No generations found")
                self.generation_ids = []
        except Exception as e:
            logger.error(f"Error searching generations: {str(e)}")
            messagebox.showerror("Error", f"Failed to search generations: {str(e)}")
    
    def on_generation_selected(self, event):
        """Handle generation selection event."""
        if not self.db_manager or not hasattr(self, 'generation_ids'):
            return
        
        # Get selected index
        selection = self.generation_listbox.curselection()
        if not selection or not self.generation_ids:
            return
        
        # Get generation ID from our list
        try:
            index = selection[0]
            if index >= len(self.generation_ids):
                return
            
            generation_id = self.generation_ids[index]
            
            # Get generation from database
            generations = self.db_manager.get_generation_history(limit=1, generation_id=generation_id)
            if not generations:
                return
            
            generation = generations[0]
            
            # Update generation details
            self.generation_details_text.delete("1.0", tk.END)
            
            # Format details
            details = f"Date: {generation['generation_date']}\n"
            details += f"Prompt: {generation['prompt_text']}\n"
            details += f"Image: {generation['image_path']}\n"
            
            if generation['parameters']:
                params = generation['parameters']
                details += f"Size: {params.get('size', 'Unknown')}\n"
                details += f"Model: {params.get('model', 'Unknown')}\n"
                if 'quality' in params:
                    details += f"Quality: {params['quality']}\n"
                if 'style' in params:
                    details += f"Style: {params['style']}\n"
            
            details += f"Tokens: {generation['token_usage']}\n"
            details += f"Cost: ${generation['cost']:.4f}\n"
            
            self.generation_details_text.insert("1.0", details)
            
            # Store selected generation
            self.selected_generation = generation
        except Exception as e:
            logger.error(f"Error getting generation details: {str(e)}")
    
    def view_selected_generation(self):
        """View the selected generation's image."""
        if not hasattr(self, 'selected_generation'):
            return
        
        image_path = self.selected_generation['image_path']
        if not image_path or not os.path.exists(image_path):
            messagebox.showerror("Error", "Image file not found")
            return
        
        try:
            # Open the image with the default image viewer
            os.startfile(image_path)
        except Exception as e:
            logger.error(f"Error opening image: {str(e)}")
            messagebox.showerror("Error", f"Failed to open image: {str(e)}")
    
    def use_selected_generation_prompt(self):
        """Use the prompt from the selected generation for a new image."""
        if not hasattr(self, 'selected_generation'):
            return
        
        prompt_text = self.selected_generation['prompt_text']
        if not prompt_text:
            messagebox.showerror("Error", "No prompt text available")
            return
        
        # Set prompt in generation tab
        self.notebook.select(0)  # Switch to generation tab
        self.prompt_text.delete("1.0", tk.END)
        self.prompt_text.insert("1.0", prompt_text)

    def delete_selected_prompt(self):
        """Delete the selected prompt from the database."""
        if not hasattr(self, 'selected_prompt_id') or not self.db_manager:
            return
        
        try:
            # Confirm deletion
            if not messagebox.askyesno("Confirm Delete", "Are you sure you want to delete this prompt?"):
                return
            
            # Delete from database
            success = self.db_manager.delete_prompt(self.selected_prompt_id)
            
            if success:
                # Refresh prompt list
                self.search_prompts()
                
                # Clear selection
                self.selected_prompt_text.delete("1.0", tk.END)
                if hasattr(self, 'selected_prompt_id'):
                    delattr(self, 'selected_prompt_id')
                
                # Show confirmation
                messagebox.showinfo("Success", "Prompt deleted successfully")
            else:
                messagebox.showerror("Error", "Failed to delete prompt")
        except Exception as e:
            logger.error(f"Error deleting prompt: {str(e)}")
            messagebox.showerror("Error", f"Failed to delete prompt: {str(e)}")
    
    def clear_all_prompts(self):
        """Clear all prompts from the database."""
        if not self.db_manager:
            return
        
        try:
            # Confirm deletion
            if not messagebox.askyesno("Confirm Delete All", 
                                      "Are you sure you want to delete ALL prompts?\n\nThis action cannot be undone!",
                                      icon='warning'):
                return
            
            # Delete all prompts
            success = self.db_manager.clear_all_prompts()
            
            if success:
                # Refresh prompt list
                self.search_prompts()
                
                # Clear selection
                self.selected_prompt_text.delete("1.0", tk.END)
                if hasattr(self, 'selected_prompt_id'):
                    delattr(self, 'selected_prompt_id')
                
                # Show confirmation
                messagebox.showinfo("Success", "All prompts deleted successfully")
            else:
                messagebox.showerror("Error", "Failed to delete prompts")
        except Exception as e:
            logger.error(f"Error deleting all prompts: {str(e)}")
            messagebox.showerror("Error", f"Failed to delete all prompts: {str(e)}")
    
    def delete_selected_generation(self):
        """Delete the selected generation from the database."""
        if not hasattr(self, 'selected_generation') or not self.db_manager:
            return
        
        try:
            # Confirm deletion
            if not messagebox.askyesno("Confirm Delete", "Are you sure you want to delete this generation?"):
                return
            
            # Delete from database
            success = self.db_manager.delete_generation(self.selected_generation['id'])
            
            if success:
                # Refresh generation list
                self.search_generations()
                
                # Clear selection
                self.generation_details_text.delete("1.0", tk.END)
                if hasattr(self, 'selected_generation'):
                    delattr(self, 'selected_generation')
                
                # Show confirmation
                messagebox.showinfo("Success", "Generation deleted successfully")
            else:
                messagebox.showerror("Error", "Failed to delete generation")
        except Exception as e:
            logger.error(f"Error deleting generation: {str(e)}")
            messagebox.showerror("Error", f"Failed to delete generation: {str(e)}")
    
    def clear_all_generations(self):
        """Clear all generations from the database."""
        if not self.db_manager:
            return
        
        try:
            # Confirm deletion
            if not messagebox.askyesno("Confirm Delete All", 
                                      "Are you sure you want to delete ALL generations?\n\nThis action cannot be undone!",
                                      icon='warning'):
                return
            
            # Delete all generations
            success = self.db_manager.clear_all_generations()
            
            if success:
                # Refresh generation list
                self.search_generations()
                
                # Clear selection
                self.generation_details_text.delete("1.0", tk.END)
                if hasattr(self, 'selected_generation'):
                    delattr(self, 'selected_generation')
                
                # Show confirmation
                messagebox.showinfo("Success", "All generations deleted successfully")
            else:
                messagebox.showerror("Error", "Failed to delete generations")
        except Exception as e:
            logger.error(f"Error deleting all generations: {str(e)}")
            messagebox.showerror("Error", f"Failed to delete all generations: {str(e)}")

    def create_styled_button(self, parent, text, command, bg_color="#4CAF50", fg_color="white", hover_color=None, font=("Arial", 10), padx=10, pady=5, width=None, height=None, border_radius=5):
        """Create a styled button with hover effect.
        
        Args:
            parent: Parent widget
            text: Button text
            command: Button command
            bg_color: Background color
            fg_color: Foreground (text) color
            hover_color: Color when hovered (defaults to darker version of bg_color)
            font: Button font
            padx: Horizontal padding
            pady: Vertical padding
            width: Button width
            height: Button height
            border_radius: Border radius for rounded corners
            
        Returns:
            Button widget
        """
        if hover_color is None:
            # Create a darker version of the background color for hover
            r, g, b = parent.winfo_rgb(bg_color)
            r = max(0, int(r / 65535 * 0.8 * 65535))
            g = max(0, int(g / 65535 * 0.8 * 65535))
            b = max(0, int(b / 65535 * 0.8 * 65535))
            hover_color = f"#{r:04x}{g:04x}{b:04x}"
        
        button = Button(parent, text=text, command=command, bg=bg_color, fg=fg_color, 
                       font=font, padx=padx, pady=pady, width=width, height=height,
                       relief="flat", borderwidth=0)
        
        # Add hover effect
        def on_enter(e):
            button['background'] = hover_color
            
        def on_leave(e):
            button['background'] = bg_color
            
        button.bind("<Enter>", on_enter)
        button.bind("<Leave>", on_leave)
        
        return button

    def create_styled_dropdown(self, parent, variable, options, bg_color="#FFFFFF", fg_color="#333333", 
                              hover_color="#F0F0F0", font=("Arial", 10), width=None, padx=5, pady=2):
        """Create a styled dropdown (OptionMenu) with hover effect.
        
        Args:
            parent: Parent widget
            variable: StringVar to store the selected value
            options: List of options for the dropdown
            bg_color: Background color
            fg_color: Foreground (text) color
            hover_color: Color when hovered
            font: Dropdown font
            width: Dropdown width
            padx: Horizontal padding
            pady: Vertical padding
            
        Returns:
            OptionMenu widget
        """
        # Create the OptionMenu
        dropdown = OptionMenu(parent, variable, *options)
        
        # Configure the dropdown style
        dropdown.config(
            font=font,
            bg=bg_color,
            fg=fg_color,
            activebackground=hover_color,
            activeforeground=fg_color,
            relief="flat",
            borderwidth=1,
            highlightthickness=1,
            highlightbackground="#CCCCCC",
            padx=padx,
            pady=pady,
            width=width
        )
        
        # Configure the dropdown menu style
        dropdown["menu"].config(
            bg=bg_color,
            fg=fg_color,
            activebackground=hover_color,
            activeforeground=fg_color,
            relief="flat",
            borderwidth=0,
            font=font
        )
        
        return dropdown
        
    def create_styled_notebook(self, parent, tab_bg_color="#f0f0f0", tab_fg_color="#333333", 
                              selected_bg_color="#4CAF50", selected_fg_color="white", 
                              font=("Arial", 10)):
        """Create a styled notebook (tabbed interface)."""
        # Create a simple notebook
        notebook = ttk.Notebook(parent)
        
        # Configure the style
        style = ttk.Style()
        
        # Configure tab appearance with high contrast colors
        style.configure('TNotebook', background='white')
        style.configure('TNotebook.Tab', 
                       background=tab_bg_color,
                       foreground='black',  # Force black text for visibility
                       font=font, 
                       padding=[10, 5],
                       borderwidth=1)
        
        # Map states to different appearances with high contrast
        style.map('TNotebook.Tab',
                 background=[("selected", selected_bg_color)],
                 foreground=[("selected", "black")],  # Force black text for visibility
                 expand=[("selected", [1, 1, 1, 0])])
        
        return notebook

    def setup_template_management_ui(self, parent):
        """Set up the template management UI.
        
        Args:
            parent (tk.Frame): The parent frame
        """
        # Create main frame
        template_frame = ttk.Frame(parent)
        template_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Split into left and right panels
        left_panel = ttk.Frame(template_frame)
        left_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))
        
        right_panel = ttk.Frame(template_frame)
        right_panel.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(5, 0))
        
        # Left panel - Template list
        ttk.Label(left_panel, text="Available Templates", font=("Arial", 12, "bold")).pack(anchor=tk.W, pady=(0, 5))
        
        # Template list with scrollbar
        template_list_frame = ttk.Frame(left_panel)
        template_list_frame.pack(fill=tk.BOTH, expand=True)
        
        template_scrollbar = ttk.Scrollbar(template_list_frame)
        template_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.template_list = tk.Listbox(template_list_frame, yscrollcommand=template_scrollbar.set, 
                                        font=("Arial", 10), selectmode=tk.SINGLE, height=10)
        self.template_list.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        template_scrollbar.config(command=self.template_list.yview)
        
        # Bind selection event
        self.template_list.bind('<<ListboxSelect>>', self.on_template_selected)
        
        # Template actions buttons
        template_actions_frame = ttk.Frame(left_panel)
        template_actions_frame.pack(fill=tk.X, pady=5)
        
        self.edit_template_btn = ttk.Button(template_actions_frame, text="Edit", state=tk.DISABLED,
                                           command=self.edit_selected_template)
        self.edit_template_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        self.delete_template_btn = ttk.Button(template_actions_frame, text="Delete", state=tk.DISABLED,
                                             command=self.delete_selected_template)
        self.delete_template_btn.pack(side=tk.LEFT, padx=5)
        
        self.use_template_btn = ttk.Button(template_actions_frame, text="Use Template", state=tk.DISABLED,
                                          command=self.use_selected_template)
        self.use_template_btn.pack(side=tk.LEFT, padx=5)
        
        # Right panel - Template editor
        ttk.Label(right_panel, text="Template Editor", font=("Arial", 12, "bold")).pack(anchor=tk.W, pady=(0, 5))
        
        # Template name
        name_frame = ttk.Frame(right_panel)
        name_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(name_frame, text="Template Name:").pack(side=tk.LEFT)
        self.template_name_entry = ttk.Entry(name_frame, width=30)
        self.template_name_entry.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        
        # Template text
        ttk.Label(right_panel, text="Template Text (use {{variable_name}} for variables):").pack(anchor=tk.W, pady=(5, 0))
        
        text_frame = ttk.Frame(right_panel)
        text_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        text_scrollbar = ttk.Scrollbar(text_frame)
        text_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.template_text = tk.Text(text_frame, height=8, width=40, yscrollcommand=text_scrollbar.set)
        self.template_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        text_scrollbar.config(command=self.template_text.yview)
        
        # Template actions
        template_btn_frame = ttk.Frame(right_panel)
        template_btn_frame.pack(fill=tk.X, pady=5)
        
        ttk.Button(template_btn_frame, text="Save Template", command=self.save_template).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(template_btn_frame, text="Clear", command=self.clear_template_editor).pack(side=tk.LEFT)
        
        # Variable management
        ttk.Label(right_panel, text="Variable Management", font=("Arial", 12, "bold")).pack(anchor=tk.W, pady=(10, 5))
        
        # Variable list with scrollbar
        var_list_frame = ttk.Frame(right_panel)
        var_list_frame.pack(fill=tk.X, pady=5)
        
        var_scrollbar = ttk.Scrollbar(var_list_frame)
        var_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.variable_list = tk.Listbox(var_list_frame, yscrollcommand=var_scrollbar.set, 
                                       font=("Arial", 10), selectmode=tk.SINGLE, height=5)
        self.variable_list.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        var_scrollbar.config(command=self.variable_list.yview)
        
        # Bind selection event
        self.variable_list.bind('<<ListboxSelect>>', self.on_variable_selected)
        
        # Variable actions
        var_btn_frame = ttk.Frame(right_panel)
        var_btn_frame.pack(fill=tk.X, pady=5)
        
        ttk.Button(var_btn_frame, text="Add Variable", command=self.add_template_variable).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(var_btn_frame, text="Edit", command=self.edit_selected_variable).pack(side=tk.LEFT, padx=5)
        ttk.Button(var_btn_frame, text="Delete", command=self.delete_selected_variable).pack(side=tk.LEFT, padx=5)
        
        # Variable editor
        var_editor_frame = ttk.Frame(right_panel)
        var_editor_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(var_editor_frame, text="Variable Name:").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.variable_name_entry = ttk.Entry(var_editor_frame, width=20)
        self.variable_name_entry.grid(row=0, column=1, sticky=tk.W+tk.E, pady=2, padx=5)
        
        ttk.Label(var_editor_frame, text="Values (one per line):").grid(row=1, column=0, sticky=tk.W, pady=2)
        
        values_frame = ttk.Frame(var_editor_frame)
        values_frame.grid(row=1, column=1, sticky=tk.W+tk.E, pady=2, padx=5)
        
        values_scrollbar = ttk.Scrollbar(values_frame)
        values_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.variable_values_text = tk.Text(values_frame, height=4, width=30, yscrollcommand=values_scrollbar.set)
        self.variable_values_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        values_scrollbar.config(command=self.variable_values_text.yview)
        
        # Variable save/clear buttons
        var_action_frame = ttk.Frame(var_editor_frame)
        var_action_frame.grid(row=2, column=1, sticky=tk.E, pady=5)
        
        ttk.Button(var_action_frame, text="Save Variable", command=self.save_variable).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(var_action_frame, text="Clear", command=self.clear_variable_editor).pack(side=tk.LEFT)
        
        # Initialize
        self.selected_variable_id = None
        self.selected_template_id = None
        
        # Load templates
        self.load_templates()
        
        # Load template variables
        self.load_template_variables()

    def load_template_variables(self):
        """Load template variables from the database."""
        if not self.db_manager:
            try:
                self.db_manager = DatabaseManager()
            except Exception as e:
                messagebox.showerror("Error", f"Failed to initialize database: {str(e)}")
                return
        
        try:
            # Get variables from database
            variables = self.db_manager.get_template_variables()
            
            # Clear listbox
            self.variable_list.delete(0, tk.END)
            
            # Store variable IDs in a list for reference
            self.variable_ids = []
            
            # Add variables to listbox
            for var in variables:
                # Format display text
                display_text = f"{var['name']} ({len(var['values'])} values)"
                
                # Store the variable ID in our list
                self.variable_ids.append(var['id'])
                
                # Add to listbox
                self.variable_list.insert(tk.END, display_text)
            
            if not variables:
                self.variable_list.insert(tk.END, "No variables defined")
                self.variable_ids = []
        except Exception as e:
            logger.error(f"Error loading template variables: {str(e)}")
            messagebox.showerror("Error", f"Failed to load template variables: {str(e)}")
    
    def on_variable_selected(self, event):
        """Handle variable selection event."""
        if not self.db_manager or not hasattr(self, 'variable_ids'):
            return
        
        # Get selected index
        selection = self.variable_list.curselection()
        if not selection or not self.variable_ids:
            return
        
        # Get variable ID from our list
        try:
            index = selection[0]
            if index >= len(self.variable_ids):
                return
            
            variable_id = self.variable_ids[index]
            
            # Get variable from database
            variables = self.db_manager.get_template_variables()
            variable = next((v for v in variables if v['id'] == variable_id), None)
            
            if not variable:
                return
            
            # Store selected variable
            self.selected_variable = variable
            
        except Exception as e:
            logger.error(f"Error getting variable details: {str(e)}")
    
    def add_template_variable(self):
        """Add a new template variable to the database."""
        if not self.db_manager:
            try:
                self.db_manager = DatabaseManager()
            except Exception as e:
                messagebox.showerror("Error", f"Failed to initialize database: {str(e)}")
                return
        
        try:
            # Get variable name
            var_name = self.variable_name_entry.get().strip()
            if not var_name:
                messagebox.showerror("Error", "Variable name cannot be empty")
                return
            
            # Get variable values
            values_text = self.variable_values_text.get("1.0", "end-1c").strip()
            if not values_text:
                messagebox.showerror("Error", "Variable must have at least one value")
                return
            
            # Split values by line
            values = [v.strip() for v in values_text.split('\n') if v.strip()]
            
            # Add variable to database
            variable_id = self.db_manager.add_template_variable(var_name, values)
            
            if variable_id:
                # Clear inputs
                self.clear_variable_editor()
                
                # Refresh variable list
                self.load_template_variables()
                
                # Show confirmation
                messagebox.showinfo("Success", f"Variable '{var_name}' added successfully")
            else:
                messagebox.showerror("Error", "Failed to add variable")
        except Exception as e:
            logger.error(f"Error adding template variable: {str(e)}")
            messagebox.showerror("Error", f"Failed to add variable: {str(e)}")
    
    def edit_selected_variable(self):
        """Edit the selected variable."""
        if not hasattr(self, 'selected_variable'):
            messagebox.showinfo("Info", "Please select a variable to edit")
            return
        
        try:
            # Load variable data into editor
            self.variable_name_entry.delete(0, tk.END)
            self.variable_name_entry.insert(0, self.selected_variable['name'])
            
            # Load values
            self.variable_values_text.delete("1.0", tk.END)
            values_text = '\n'.join(self.selected_variable['values'])
            self.variable_values_text.insert("1.0", values_text)
            
            # Show confirmation
            messagebox.showinfo("Info", f"Loaded variable '{self.selected_variable['name']}' for editing. Make changes and click 'Add Variable' to update.")
        except Exception as e:
            logger.error(f"Error loading variable for editing: {str(e)}")
            messagebox.showerror("Error", f"Failed to load variable: {str(e)}")
    
    def delete_selected_variable(self):
        """Delete the selected variable."""
        if not hasattr(self, 'selected_variable') or not self.db_manager:
            return
        
        try:
            # Confirm deletion
            if not messagebox.askyesno("Confirm Delete", f"Are you sure you want to delete the variable '{self.selected_variable['name']}'?"):
                return
            
            # Delete from database
            success = self.db_manager.delete_template_variable(self.selected_variable['id'])
            
            if success:
                # Refresh variable list
                self.load_template_variables()
                
                # Clear selection
                if hasattr(self, 'selected_variable'):
                    delattr(self, 'selected_variable')
                
                # Show confirmation
                messagebox.showinfo("Success", "Variable deleted successfully")
            else:
                messagebox.showerror("Error", "Failed to delete variable")
        except Exception as e:
            logger.error(f"Error deleting variable: {str(e)}")
            messagebox.showerror("Error", f"Failed to delete variable: {str(e)}")
    
    def clear_variable_editor(self):
        """Clear the variable editor fields."""
        self.variable_name_entry.delete(0, tk.END)
        self.variable_values_text.delete("1.0", tk.END)
    
    def save_template(self):
        """Save a template prompt to the database."""
        # Get template name and text
        template_name = self.template_name_entry.get().strip()
        template_text = self.template_text.get("1.0", tk.END).strip()
        
        if not template_name or not template_text:
            messagebox.showerror("Error", "Template name and text are required")
            return
        
        # Extract variable names from template
        variables = self.extract_template_variables(template_text)
        
        if not variables:
            messagebox.showwarning("Warning", "No variables found in template. Variables should be in format {{variable_name}}")
            return
        
        try:
            # Save template to database
            template_id = self.db_manager.add_prompt(
                prompt_text=template_name,
                is_template=True,
                template_variables=json.dumps(variables)
            )
            
            if template_id:
                messagebox.showinfo("Success", f"Template '{template_name}' saved successfully")
                self.clear_template_editor()
                self.load_templates()  # Refresh template list
            else:
                messagebox.showerror("Error", "Failed to save template")
        except Exception as e:
            logger.error(f"Error saving template: {str(e)}")
            messagebox.showerror("Error", f"Failed to save template: {str(e)}")
    
    def clear_template_editor(self):
        """Clear the template editor fields."""
        self.template_name_entry.delete(0, tk.END)
        self.template_text.delete("1.0", tk.END)

    def get_templates(self):
        """Load templates from the database and return them.
        
        Returns:
            list: List of template dictionaries
        """
        try:
            # Use db_manager instead of direct cursor access
            # Get all prompts and filter for templates
            prompts = self.db_manager.get_prompt_history(limit=100)
            # Filter to only include templates
            templates = [p for p in prompts if p.get('is_template', 0) == 1]
            return templates
        except Exception as e:
            logger.error(f"Error loading templates: {str(e)}")
            return []

    def load_templates(self):
        """Load templates from the database and populate the template list."""
        # Clear the current list
        self.template_list.delete(0, tk.END)
        
        # Get templates from the database
        templates = self.get_templates()
        
        # Add templates to the list
        for template in templates:
            # Format: Template Name (# variables)
            var_count = len(template['template_variables']) if template['template_variables'] else 0
            display_text = f"{template['prompt_text'][:30]}... ({var_count} vars)"
            
            # Insert into list with the template ID as the value
            self.template_list.insert(tk.END, display_text)
            # Store the template ID in the list item
            self.template_list.itemconfig(tk.END, {'template_id': template['id']})
        
        if not templates:
            self.template_list.insert(tk.END, "No templates found")
            
        logger.info(f"Loaded {len(templates)} templates")

    def extract_template_variables(self, template_text):
        """Extract variable names from a template text.
        
        Variables are identified by {{variable_name}} pattern.
        
        Args:
            template_text (str): The template text
            
        Returns:
            list: List of unique variable names
        """
        import re
        
        # Find all occurrences of {{variable_name}}
        pattern = r'\{\{([^{}]+)\}\}'
        matches = re.findall(pattern, template_text)
        
        # Return unique variable names
        return list(set(matches))

    def on_template_selected(self, event=None):
        """Handle template selection from the list."""
        # Get selected index
        selection = self.template_list.curselection()
        if not selection:
            return
        
        # Get template ID from the selected item
        try:
            template_id = self.template_list.itemcget(selection[0], 'template_id')
            if not template_id:
                return
                
            # Get template from database
            templates = self.db_manager.get_prompt_history(prompt_id=template_id)
            if not templates:
                messagebox.showerror("Error", "Template not found")
                return
                
            template = templates[0]
            
            # Load template data into editor
            self.template_name_entry.delete(0, tk.END)
            self.template_name_entry.insert(0, template['prompt_text'])
            
            # Load template variables
            variables = json.loads(template['template_variables']) if template['template_variables'] else []
            
            # Update variable list
            self.variable_list.delete(0, tk.END)
            for var in variables:
                self.variable_list.insert(tk.END, var)
                
            # Store the selected template ID
            self.selected_template_id = template['id']
            
            # Enable edit/delete buttons
            self.edit_template_btn.config(state=tk.NORMAL)
            self.delete_template_btn.config(state=tk.NORMAL)
            self.use_template_btn.config(state=tk.NORMAL)
            
        except Exception as e:
            logger.error(f"Error loading template: {str(e)}")
            messagebox.showerror("Error", f"Failed to load template: {str(e)}")

    def edit_selected_template(self):
        """Edit the selected template."""
        if not hasattr(self, 'selected_template_id') or not self.selected_template_id:
            messagebox.showerror("Error", "No template selected")
            return
            
        # Template is already loaded in the editor from on_template_selected
        messagebox.showinfo("Edit Template", "Make your changes and click 'Save Template' to update")
    
    def delete_selected_template(self):
        """Delete the selected template."""
        if not hasattr(self, 'selected_template_id') or not self.selected_template_id:
            messagebox.showerror("Error", "No template selected")
            return
            
        # Confirm deletion
        if not messagebox.askyesno("Confirm Delete", "Are you sure you want to delete this template?"):
            return
            
        try:
            # Delete template from database
            success = self.db_manager.delete_prompt(self.selected_template_id)
            
            if not success:
                messagebox.showerror("Error", "Failed to delete template")
                return
                
            # Refresh template list
            self.load_templates()
            
            # Clear editor
            self.clear_template_editor()
            
            # Reset selected template
            self.selected_template_id = None
            
            # Disable edit/delete buttons
            self.edit_template_btn.config(state=tk.DISABLED)
            self.delete_template_btn.config(state=tk.DISABLED)
            self.use_template_btn.config(state=tk.DISABLED)
            
            messagebox.showinfo("Success", "Template deleted successfully")
        except Exception as e:
            logger.error(f"Error deleting template: {str(e)}")
            messagebox.showerror("Error", f"Failed to delete template: {str(e)}")
    
    def use_selected_template(self):
        """Use the selected template for prompt generation."""
        if not hasattr(self, 'selected_template_id') or not self.selected_template_id:
            messagebox.showerror("Error", "No template selected")
            return
            
        try:
            # Get template from database
            templates = self.db_manager.get_prompt_history(prompt_id=self.selected_template_id)
            if not templates:
                messagebox.showerror("Error", "Template not found")
                return
                
            template = templates[0]
            
            # Show template variable dialog
            self.show_template_variable_dialog(template['prompt_text'], json.loads(template['template_variables']))
        except Exception as e:
            logger.error(f"Error using template: {str(e)}")
            messagebox.showerror("Error", f"Failed to use template: {str(e)}")
    
    def show_template_variable_dialog(self, template_text, variables):
        """Show a dialog to fill in template variables.
        
        Args:
            template_text (str): The template text
            variables (list): List of variable names
        """
        # Create dialog
        dialog = tk.Toplevel(self.root)
        dialog.title("Fill Template Variables")
        dialog.geometry("500x400")
        dialog.transient(self.root)
        dialog.grab_set()
        
        # Create frame for variable inputs
        frame = ttk.Frame(dialog, padding=10)
        frame.pack(fill=tk.BOTH, expand=True)
        
        # Add instructions
        ttk.Label(frame, text="Fill in the values for each variable:", font=("Arial", 12, "bold")).pack(anchor=tk.W, pady=(0, 10))
        
        # Create dictionary to store variable entries
        var_entries = {}
        
        # Create scrollable frame for variables
        canvas = tk.Canvas(frame)
        scrollbar = ttk.Scrollbar(frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Get all template variables from database
        template_variables = self.db_manager.get_template_variables()
        var_values_dict = {}
        
        # Create a dictionary of variable names to their values
        for var in template_variables:
            if var['name'] in variables:
                var_values_dict[var['name']] = json.loads(var['value_list']) if var['value_list'] else []
        
        # Add variable inputs
        for i, var_name in enumerate(variables):
            var_frame = ttk.Frame(scrollable_frame)
            var_frame.pack(fill=tk.X, pady=5)
            
            ttk.Label(var_frame, text=f"{var_name}:").grid(row=0, column=0, sticky=tk.W, padx=(0, 5))
            
            # Create entry for variable
            var_entry = ttk.Entry(var_frame, width=40)
            var_entry.grid(row=0, column=1, sticky=tk.W+tk.E)
            
            # If we have values for this variable, create a dropdown instead
            if var_name in var_values_dict and var_values_dict[var_name]:
                values = var_values_dict[var_name]
                if values:
                    var_entry.destroy()  # Remove the entry widget
                    var_combo = ttk.Combobox(var_frame, width=38, values=values)
                    var_combo.grid(row=0, column=1, sticky=tk.W+tk.E)
                    var_combo.current(0)  # Set to first value
                    var_entries[var_name] = var_combo
                    continue
            
            # If we get here, use the entry widget
            var_entries[var_name] = var_entry
        
        # Add buttons
        button_frame = ttk.Frame(frame)
        button_frame.pack(fill=tk.X, pady=10)
        
        ttk.Button(
            button_frame, 
            text="Generate Prompt", 
            command=lambda: self.generate_from_template(template_text, var_entries, dialog)
        ).pack(side=tk.RIGHT, padx=5)
        
        ttk.Button(
            button_frame, 
            text="Cancel", 
            command=dialog.destroy
        ).pack(side=tk.RIGHT)
    
    def generate_from_template(self, template_text, var_entries, dialog):
        """Generate a prompt from a template with variable values.
        
        Args:
            template_text (str): The template text
            var_entries (dict): Dictionary of variable entries
            dialog (tk.Toplevel): The dialog window
        """
        # Get variable values
        var_values = {}
        for var_name, entry in var_entries.items():
            var_values[var_name] = entry.get()
            
            if not var_values[var_name]:
                messagebox.showerror("Error", f"Please fill in a value for '{var_name}'")
                return
        
        # Replace variables in template
        prompt_text = template_text
        for var_name, value in var_values.items():
            prompt_text = prompt_text.replace(f"{{{{{var_name}}}}}", value)
        
        # Close dialog
        dialog.destroy()
        
        # Set prompt in main UI
        self.prompt_text.delete("1.0", tk.END)
        self.prompt_text.insert("1.0", prompt_text)
        
        # Show confirmation
        messagebox.showinfo("Success", "Template prompt generated successfully")
    
    def save_variable(self):
        """Save a template variable."""
        # Get variable name and values
        var_name = self.variable_name_entry.get().strip()
        var_values_text = self.variable_values_text.get("1.0", tk.END).strip()
        
        if not var_name:
            messagebox.showerror("Error", "Variable name is required")
            return
            
        if not var_values_text:
            messagebox.showerror("Error", "At least one variable value is required")
            return
            
        # Split values by line
        values = [line.strip() for line in var_values_text.split('\n') if line.strip()]
        
        if not values:
            messagebox.showerror("Error", "At least one variable value is required")
            return
            
        try:
            # Save variable to database
            result = self.db_manager.add_template_variable(var_name, json.dumps(values))
            
            if result:
                messagebox.showinfo("Success", f"Variable '{var_name}' saved successfully")
                self.clear_variable_editor()
                self.load_template_variables()
            else:
                messagebox.showerror("Error", "Failed to save variable")
        except Exception as e:
            logger.error(f"Error saving variable: {str(e)}")
            messagebox.showerror("Error", f"Failed to save variable: {str(e)}")

if __name__ == "__main__":
    root = tk.Tk()
    app = DALLEGeneratorApp(root)
    root.mainloop() 
