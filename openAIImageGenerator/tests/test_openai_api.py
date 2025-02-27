import os
import sys
import json
import logging
from dotenv import load_dotenv

# Add parent directory to path to import app modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("openai_api_test.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("openai_api_test")

# Load environment variables
load_dotenv()

def test_openai_api():
    """Test OpenAI API access and log detailed information."""
    try:
        # Import OpenAI
        logger.info("Importing OpenAI library...")
        from openai import OpenAI
        logger.info("OpenAI library imported successfully")
        
        # Get API key
        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            logger.error("No API key found in environment variables")
            return False
            
        # Log API key length and first/last few characters (for debugging without exposing the key)
        key_length = len(api_key)
        key_preview = f"{api_key[:4]}...{api_key[-4:]}"
        logger.info(f"API key found (length: {key_length}, preview: {key_preview})")
        
        # Initialize client
        logger.info("Initializing OpenAI client...")
        client = OpenAI(api_key=api_key)
        logger.info("OpenAI client initialized")
        
        # Test models endpoint
        logger.info("Testing models.list endpoint...")
        try:
            models_response = client.models.list()
            model_ids = [model.id for model in models_response.data]
            logger.info(f"Models available: {json.dumps(model_ids)}")
            
            # Check for DALL-E models specifically
            dalle_models = [model for model in model_ids if "dall-e" in model.lower()]
            if dalle_models:
                logger.info(f"DALL-E models available: {json.dumps(dalle_models)}")
            else:
                logger.warning("No DALL-E models found in available models")
        except Exception as e:
            logger.error(f"Error accessing models endpoint: {str(e)}")
            if hasattr(e, 'response'):
                try:
                    status_code = e.response.status_code
                    error_json = e.response.json()
                    logger.error(f"API Error Details - Status: {status_code}, Response: {json.dumps(error_json)}")
                except:
                    pass
        
        # Test image generation
        logger.info("Testing image generation endpoint...")
        try:
            response = client.images.generate(
                model="dall-e-2",
                prompt="A simple test image of a blue circle",
                size="256x256",
                n=1,
                response_format="url"
            )
            logger.info(f"Image generation successful: {response.data[0].url}")
        except Exception as e:
            logger.error(f"Error generating image: {str(e)}")
            if hasattr(e, 'response'):
                try:
                    status_code = e.response.status_code
                    error_json = e.response.json()
                    logger.error(f"API Error Details - Status: {status_code}, Response: {json.dumps(error_json)}")
                except:
                    pass
        
        # Test completions (as a fallback to check general API access)
        logger.info("Testing completions endpoint...")
        try:
            completion = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user", "content": "Hello!"}
                ]
            )
            logger.info(f"Completion successful: {completion.choices[0].message.content}")
        except Exception as e:
            logger.error(f"Error creating completion: {str(e)}")
            if hasattr(e, 'response'):
                try:
                    status_code = e.response.status_code
                    error_json = e.response.json()
                    logger.error(f"API Error Details - Status: {status_code}, Response: {json.dumps(error_json)}")
                except:
                    pass
        
        return True
    except Exception as e:
        logger.error(f"Unexpected error in test_openai_api: {str(e)}")
        return False

if __name__ == "__main__":
    logger.info("Starting OpenAI API test")
    test_openai_api()
    logger.info("OpenAI API test completed") 
