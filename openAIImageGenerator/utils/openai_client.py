import os
import logging
import base64
from io import BytesIO
from openai import OpenAI
from config import OPENAI_CONFIG, APP_CONFIG

logger = logging.getLogger(__name__)

class OpenAIClient:
    """Wrapper for OpenAI API client with DALL-E specific functionality."""
    
    def __init__(self):
        """Initialize the OpenAI client with API key from config."""
        # Try to get API key from config or environment
        self.api_key = OPENAI_CONFIG.get("api_key") or os.environ.get("OPENAI_API_KEY")
        if not self.api_key:
            logger.error("OpenAI API key not found")
            raise ValueError("OpenAI API key is required")
        
        self.client = OpenAI(
            api_key=self.api_key,
            organization=OPENAI_CONFIG.get("organization"),
            timeout=OPENAI_CONFIG.get("timeout", 30)
        )
        # Detect available models
        self.available_models = self._detect_available_models()
        self.model = self._select_best_model()
        logger.info("OpenAI client initialized")
        logger.info(f"Using model: {self.model}")
    
    def _detect_available_models(self):
        """Detect which DALL-E models are available to the user."""
        try:
            models = self.client.models.list()
            available_models = []
            
            # Check for DALL-E models
            for model in models.data:
                if "dall-e" in model.id.lower():
                    available_models.append(model.id)
                    logger.info(f"Found available model: {model.id}")
            
            return available_models
        except Exception as e:
            logger.warning(f"Could not detect available models: {str(e)}")
            # Default to DALL-E 2 as fallback
            return ["dall-e-2"]
    
    def _select_best_model(self):
        """Select the best available DALL-E model."""
        preferred_model = OPENAI_CONFIG.get("model", "dall-e-2")
        
        # If preferred model is available, use it
        if preferred_model in self.available_models:
            return preferred_model
        
        # If DALL-E 3 is available, use it
        if "dall-e-3" in self.available_models:
            return "dall-e-3"
        
        # Otherwise use DALL-E 2 or the first available model
        if "dall-e-2" in self.available_models:
            return "dall-e-2"
        elif self.available_models:
            return self.available_models[0]
        else:
            # Fallback to DALL-E 2 if no models detected
            return "dall-e-2"
    
    def validate_api_key(self):
        """Validate the API key by making a simple request."""
        try:
            # Make a simple models list request to validate the API key
            self.client.models.list(limit=1)
            logger.info("API key validated successfully")
            return True
        except Exception as e:
            logger.error(f"API key validation failed: {str(e)}")
            return False

    def get_model_capabilities(self):
        """Get the capabilities of the current model."""
        capabilities = {
            "supports_quality": False,
            "supports_style": False,
            "max_size": "1024x1024",
            "sizes": ["256x256", "512x512", "1024x1024"]
        }
        
        # DALL-E 3 supports quality and style
        if "dall-e-3" in self.model:
            capabilities["supports_quality"] = True
            capabilities["supports_style"] = True
            capabilities["max_size"] = "1792x1024"
            capabilities["sizes"] = ["1024x1024", "1792x1024", "1024x1792"]
        
        return capabilities

    def generate_image(self, prompt, size=None, quality=None, style=None, n=1, response_format="b64_json"):
        """Generate an image using DALL-E.
        
        Args:
            prompt (str): The prompt to generate an image from
            size (str, optional): Image size. Defaults to config value.
            quality (str, optional): Image quality. Defaults to config value.
            style (str, optional): Image style. Defaults to config value.
            n (int, optional): Number of images to generate. Defaults to 1.
            response_format (str, optional): Response format. Defaults to "b64_json".
            
        Returns:
            tuple: (image_data, usage_info) or (None, None) on failure
        """
        # Use default values from config if not specified
        size = size or APP_CONFIG["default_image_size"]
        
        # Get model capabilities
        capabilities = self.get_model_capabilities()
        
        # Check if size is supported
        if size not in capabilities["sizes"]:
            logger.warning(f"Size {size} not supported by {self.model}, using {capabilities['max_size']}")
            size = capabilities["max_size"]
        
        # Prepare generation parameters
        generation_params = {
            "model": self.model,
            "prompt": prompt,
            "size": size,
            "n": n,
            "response_format": response_format
        }
        
        # Add quality and style for DALL-E 3
        if capabilities["supports_quality"] and quality:
            generation_params["quality"] = quality or APP_CONFIG["default_image_quality"]
            
        if capabilities["supports_style"] and style:
            generation_params["style"] = style or APP_CONFIG["default_image_style"]
        
        # Log generation attempt
        log_msg = f"Generating image with prompt: '{prompt[:50]}...' (size: {size}"
        if "quality" in generation_params:
            log_msg += f", quality: {generation_params['quality']}"
        if "style" in generation_params:
            log_msg += f", style: {generation_params['style']}"
        log_msg += f") using model {self.model}"
        logger.info(log_msg)
        
        try:
            # Generate the image with appropriate parameters
            response = self.client.images.generate(**generation_params)
            
            # Extract usage information (this is approximate as the API doesn't provide exact token counts)
            # We'll estimate based on prompt length and image size
            prompt_tokens = len(prompt.split())
            size_multiplier = 1
            if size == "1024x1024":
                size_multiplier = 2
            elif size == "1792x1024" or size == "1024x1792":
                size_multiplier = 3
                
            # Add quality multiplier for DALL-E 3
            quality_multiplier = 1
            if "quality" in generation_params and generation_params["quality"] == "hd":
                quality_multiplier = 1.5
                
            estimated_tokens = int(prompt_tokens * size_multiplier * quality_multiplier * n)
            
            usage_info = {
                "estimated_tokens": estimated_tokens,
                "prompt_tokens": prompt_tokens,
                "size": size,
                "model": self.model,
                "n": n
            }
            
            # Add quality and style to usage info if used
            if "quality" in generation_params:
                usage_info["quality"] = generation_params["quality"]
            if "style" in generation_params:
                usage_info["style"] = generation_params["style"]
            
            # For b64_json response format, decode the base64 data
            if response_format == "b64_json":
                image_data = base64.b64decode(response.data[0].b64_json)
                return image_data, usage_info
            else:
                # For URL response format, return the URL
                return response.data[0].url, usage_info
                
        except Exception as e:
            logger.error(f"Image generation failed: {str(e)}")
            return None, None
            
    def generate_image_variation(self, image_data, size=None, n=1, response_format="b64_json"):
        """Generate variations of an image.
        
        Args:
            image_data (bytes): The image data to create variations from
            size (str, optional): Image size. Defaults to config value.
            n (int, optional): Number of variations to generate. Defaults to 1.
            response_format (str, optional): Response format. Defaults to "b64_json".
            
        Returns:
            tuple: (image_data, usage_info) or (None, None) on failure
        """
        # Use default values from config if not specified
        size = size or APP_CONFIG["default_image_size"]
        
        logger.info(f"Generating image variation (size: {size})")
        
        try:
            # Convert image data to file-like object
            image_file = BytesIO(image_data)
            image_file.name = "image.png"  # The API needs a filename
            
            response = self.client.images.create_variation(
                image=image_file,
                size=size,
                n=n,
                response_format=response_format
            )
            
            # Estimate usage (this is approximate)
            size_multiplier = 1
            if size == "1024x1024":
                size_multiplier = 2
            elif size == "1792x1024" or size == "1024x1792":
                size_multiplier = 3
                
            estimated_tokens = int(1000 * size_multiplier * n)  # Base estimate for variations
            
            usage_info = {
                "estimated_tokens": estimated_tokens,
                "size": size,
                "n": n
            }
            
            # For b64_json response format, decode the base64 data
            if response_format == "b64_json":
                image_data = base64.b64decode(response.data[0].b64_json)
                return image_data, usage_info
            else:
                # For URL response format, return the URL
                return response.data[0].url, usage_info
                
        except Exception as e:
            logger.error(f"Image variation generation failed: {str(e)}")
            return None, None 
