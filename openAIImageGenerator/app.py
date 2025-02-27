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
        self.notebook = ttk.Notebook(self.root)
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
        self.size_menu = OptionMenu(size_frame, self.size_var, *self.sizes)
        self.size_menu.pack(side="left", padx=(0, 20))
        
        # Quality and style options (will be shown/hidden based on model)
        self.quality_frame = Frame(size_frame)
        self.quality_frame.pack(side="left", padx=(0, 10))
        
        self.quality_label = Label(self.quality_frame, text="Quality:", font=("Arial", 10))
        self.quality_var = StringVar(value=APP_CONFIG["default_image_quality"])
        self.quality_menu = OptionMenu(self.quality_frame, self.quality_var, "standard", "hd")
        
        self.style_frame = Frame(size_frame)
        self.style_frame.pack(side="left")
        
        self.style_label = Label(self.style_frame, text="Style:", font=("Arial", 10))
        self.style_var = StringVar(value=APP_CONFIG["default_image_style"])
        self.style_menu = OptionMenu(self.style_frame, self.style_var, "vivid", "natural")
        
        # Model info label
        self.model_label = Label(size_frame, text="Detecting model...", font=("Arial", 10, "italic"))
        self.model_label.pack(side="left", padx=(10, 0))
        
        # Generate button
        generate_btn = Button(generation_frame, text="Generate Image", command=self.generate_image, bg="#4CAF50", fg="white", font=("Arial", 12), padx=20, pady=10)
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
            self.size_menu = OptionMenu(self.size_menu.master, self.size_var, *capabilities["sizes"])
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
            
            # Create label to display image
            image_label = Label(self.preview_frame, image=tk_image)
            image_label.image = tk_image  # Keep a reference to prevent garbage collection
            image_label.pack(expand=True)
            
        except Exception as e:
            logger.error(f"Error displaying image: {str(e)}")
            Label(self.preview_frame, text=f"Error displaying image: {str(e)}", bg="#f0f0f0").pack(expand=True)

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
                    messagebox.showinfo("Success", f"Image saved to: {output_path}")
                    # Open the containing folder
                    try:
                        os.startfile(os.path.dirname(output_path))
                    except Exception as e:
                        logger.error(f"Failed to open containing folder: {str(e)}")
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
                        messagebox.showinfo("Success (from backup)", f"Image saved to: {new_path}")
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
        history_notebook = ttk.Notebook(history_frame)
        history_notebook.pack(fill="both", expand=True)
        
        # Create sub-tabs
        prompt_history_tab = Frame(history_notebook)
        generation_history_tab = Frame(history_notebook)
        
        history_notebook.add(prompt_history_tab, text="Prompt History")
        history_notebook.add(generation_history_tab, text="Generation History")
        
        # Setup prompt history UI
        self.setup_prompt_history_ui(prompt_history_tab)
        
        # Setup generation history UI
        self.setup_generation_history_ui(generation_history_tab)
    
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
        search_btn = Button(controls_frame, text="Search", command=self.search_prompts)
        search_btn.pack(side="left", padx=(0, 20))
        
        # Favorites only checkbox
        self.favorites_only_var = tk.BooleanVar(value=False)
        favorites_check = tk.Checkbutton(controls_frame, text="Favorites Only", variable=self.favorites_only_var, command=self.search_prompts)
        favorites_check.pack(side="left", padx=(0, 20))
        
        # Refresh button
        refresh_btn = Button(controls_frame, text="Refresh", command=self.search_prompts)
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
        
        use_btn = Button(buttons_frame, text="Use Prompt", command=self.use_selected_prompt)
        use_btn.pack(side="left", padx=(0, 10))
        
        favorite_btn = Button(buttons_frame, text="Toggle Favorite", command=self.toggle_favorite_prompt)
        favorite_btn.pack(side="left", padx=(0, 10))
        
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
        search_btn = Button(controls_frame, text="Search", command=self.search_generations)
        search_btn.pack(side="left", padx=(0, 20))
        
        # Refresh button
        refresh_btn = Button(controls_frame, text="Refresh", command=self.search_generations)
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
        
        view_btn = Button(buttons_frame, text="View Image", command=self.view_selected_generation)
        view_btn.pack(side="left", padx=(0, 10))
        
        use_prompt_btn = Button(buttons_frame, text="Use Prompt", command=self.use_selected_generation_prompt)
        use_prompt_btn.pack(side="left", padx=(0, 10))
        
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

if __name__ == "__main__":
    root = tk.Tk()
    app = DALLEGeneratorApp(root)
    root.mainloop() 
