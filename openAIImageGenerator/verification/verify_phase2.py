import os
import sys
import logging
from PIL import Image
from io import BytesIO
import tkinter as tk
from tkinter import messagebox

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from utils.openai_client import OpenAIClient
from utils.file_manager import FileManager
from utils.usage_tracker import UsageTracker
from config import ensure_directories

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger("phase2_verification")

def verify_openai_client():
    """Verify that the OpenAI client is properly implemented."""
    logger.info("Verifying OpenAI client...")
    
    try:
        client = OpenAIClient()
        
        # Check if the client has the required methods
        required_methods = ["validate_api_key", "generate_image", "generate_image_variation"]
        for method in required_methods:
            if not hasattr(client, method) or not callable(getattr(client, method)):
                logger.error(f"OpenAI client missing required method: {method}")
                return False
        
        logger.info("OpenAI client verified successfully")
        return True
    except Exception as e:
        logger.error(f"Error verifying OpenAI client: {str(e)}")
        return False

def verify_image_generation(test_mode=True):
    """Verify that image generation works."""
    logger.info("Verifying image generation...")
    
    if test_mode:
        logger.info("Running in test mode - skipping actual API call")
        return True
    
    try:
        client = OpenAIClient()
        file_manager = FileManager()
        usage_tracker = UsageTracker()
        
        # Generate a simple test image
        test_prompt = "A simple test image of a blue circle on a white background"
        image_data, usage_info = client.generate_image(test_prompt, size="256x256")
        
        if not image_data or not usage_info:
            logger.error("Image generation failed")
            return False
        
        # Verify the image data is valid
        try:
            Image.open(BytesIO(image_data))
        except Exception as e:
            logger.error(f"Generated image data is invalid: {str(e)}")
            return False
        
        # Save the image
        output_path = file_manager.save_image(image_data, test_prompt, "verification_test")
        if not output_path or not os.path.exists(output_path):
            logger.error(f"Failed to save image to {output_path}")
            return False
        
        # Record usage
        usage_tracker.record_usage(usage_info["estimated_tokens"])
        
        logger.info(f"Image generation verified successfully - saved to {output_path}")
        return True
    except Exception as e:
        logger.error(f"Error verifying image generation: {str(e)}")
        return False

def verify_app_ui_updates():
    """Verify that the app UI has been updated with image generation components."""
    logger.info("Verifying app UI updates...")
    
    try:
        # Import the app module
        from app import DALLEGeneratorApp
        
        # Check if the app has the required methods
        required_methods = [
            "setup_image_generation_ui", 
            "generate_image", 
            "display_image", 
            "save_image"
        ]
        
        for method in required_methods:
            if not hasattr(DALLEGeneratorApp, method) or not callable(getattr(DALLEGeneratorApp, method)):
                logger.error(f"App missing required method: {method}")
                return False
        
        logger.info("App UI updates verified successfully")
        return True
    except Exception as e:
        logger.error(f"Error verifying app UI updates: {str(e)}")
        return False

def main():
    """Run all verification checks."""
    logger.info("Starting Phase 2 verification...")
    
    # Ensure directories exist
    ensure_directories()
    
    checks = [
        verify_openai_client,
        lambda: verify_image_generation(test_mode=True),  # Skip actual API call in automated testing
        verify_app_ui_updates
    ]
    
    all_passed = True
    for check in checks:
        if not check():
            all_passed = False
    
    if all_passed:
        logger.info("✅ All Phase 2 verification checks passed!")
        
        # Ask if user wants to test actual image generation
        if input("Do you want to test actual image generation with the OpenAI API? (y/n): ").lower() == 'y':
            if verify_image_generation(test_mode=False):
                logger.info("✅ Image generation test successful!")
            else:
                logger.error("❌ Image generation test failed")
                all_passed = False
        
        return 0 if all_passed else 1
    else:
        logger.error("❌ Some verification checks failed")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 
