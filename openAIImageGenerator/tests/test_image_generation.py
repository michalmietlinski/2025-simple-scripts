import os
import sys
import logging

# Add parent directory to path to import app modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

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
logger = logging.getLogger("image_generation_test")

def generate_test_image(prompt, size=None):
    """Generate a test image using the provided prompt."""
    logger.info(f"Testing image generation with prompt: '{prompt}'")
    
    # Ensure directories exist
    ensure_directories()
    
    # Initialize clients
    openai_client = OpenAIClient()
    file_manager = FileManager()
    usage_tracker = UsageTracker()
    
    # Generate image
    image_data, usage_info = openai_client.generate_image(prompt, size=size)
    
    if image_data and usage_info:
        # Save image
        output_path = file_manager.save_image(image_data, prompt, "test_generation")
        
        # Record usage
        usage_tracker.record_usage(
            usage_info["estimated_tokens"],
            # Approximate cost calculation
            cost=usage_info["estimated_tokens"] * 0.00002
        )
        
        logger.info(f"Image generated and saved to: {output_path}")
        logger.info(f"Estimated tokens used: {usage_info['estimated_tokens']}")
        
        return True, output_path
    else:
        logger.error("Image generation failed")
        return False, None

def main():
    """Run the image generation test."""
    if len(sys.argv) < 2:
        print("Usage: python test_image_generation.py \"Your prompt here\" [size]")
        return 1
    
    prompt = sys.argv[1]
    size = sys.argv[2] if len(sys.argv) > 2 else None
    
    success, path = generate_test_image(prompt, size)
    
    if success:
        print(f"\nSuccess! Image saved to: {path}")
        return 0
    else:
        print("\nFailed to generate image. Check logs for details.")
        return 1

if __name__ == "__main__":
    print("Running image generation test...")
    sys.exit(main()) 
