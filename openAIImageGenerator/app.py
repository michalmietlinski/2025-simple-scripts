import os
import logging
import tkinter as tk
from tkinter import messagebox
from dotenv import load_dotenv

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
        self.root.geometry("1200x800")
        
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
            from utils.openai_client import OpenAIClient
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
            from config import APP_CONFIG, OPENAI_CONFIG, ensure_directories
            ensure_directories()
            config_label.config(text="Configuration: ✓ Verified", fg="green")
        except Exception as e:
            config_label.config(text="Configuration: ✗ Error - " + str(e), fg="red")
        
        # Check utility modules
        try:
            from utils.file_manager import FileManager
            from utils.usage_tracker import UsageTracker
            
            # Fix import error if needed
            try:
                from utils.openai_client import OpenAIClient
            except ImportError:
                with open("utils/usage_tracker.py", "r") as f:
                    content = f.read()
                
                if content.startswith("aimport logging"):
                    with open("utils/usage_tracker.py", "w") as f:
                        f.write(content.replace("aimport logging", "import logging"))
                    # Try again
                    from utils.openai_client import OpenAIClient
            
            utils_label.config(text="Utility Modules: ✓ Verified", fg="green")
        except Exception as e:
            utils_label.config(text="Utility Modules: ✗ Error - " + str(e), fg="red")

if __name__ == "__main__":
    root = tk.Tk()
    app = DALLEGeneratorApp(root)
    root.mainloop() 
