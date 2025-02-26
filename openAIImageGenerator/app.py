import os
import logging
import tkinter as tk
from tkinter import messagebox, Text, Frame, Label, Button, StringVar, OptionMenu, filedialog, simpledialog
from PIL import Image, ImageTk
from io import BytesIO
from dotenv import load_dotenv
from utils.openai_client import OpenAIClient
from utils.file_manager import FileManager
from utils.usage_tracker import UsageTracker
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
            api_status = tk.Label(self.root, text="API Key: ✓ Loaded", fg="green", font=("Arial", 12))
        else:
            api_status = tk.Label(self.root, text="API Key: ✗ Not found", fg="red", font=("Arial", 12))
        api_status.pack(pady=10)
        
        # Add button to test API key
        test_key_btn = tk.Button(self.root, text="Test API Key", command=self.test_api_key)
        test_key_btn.pack(pady=10)
        
        # Add button to update API key
        update_key_btn = tk.Button(self.root, text="Update API Key", command=self.show_api_key_dialog)
        update_key_btn.pack(pady=10)
        
        # Add verification status section
        verification_frame = tk.LabelFrame(self.root, text="Phase 1 Verification", padx=10, pady=10)
        verification_frame.pack(pady=20, padx=20, fill="x")
        
        # Check project structure
        structure_label = tk.Label(verification_frame, text="Project Structure: Checking...", font=("Arial", 10))
        structure_label.pack(anchor="w", pady=5)
        
        # Check configuration
        config_label = tk.Label(verification_frame, text="Configuration: Checking...", font=("Arial", 10))
        config_label.pack(anchor="w", pady=5)
        
        # Check utility modules
        utils_label = tk.Label(verification_frame, text="Utility Modules: Checking...", font=("Arial", 10))
        utils_label.pack(anchor="w", pady=5)
        
        # Run verification
        self.run_verification(structure_label, config_label, utils_label)
        
        # Add image generation section
        self.setup_image_generation_ui()
    
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
        generation_frame = Frame(self.root, padx=20, pady=20)
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
        self.current_image = None
        
        # Initialize clients if API key is available
        if self.api_key:
            try:
                self.openai_client = OpenAIClient()
                self.file_manager = FileManager()
                self.usage_tracker = UsageTracker()
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

if __name__ == "__main__":
    root = tk.Tk()
    app = DALLEGeneratorApp(root)
    root.mainloop() 
