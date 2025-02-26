import os
import logging
import base64
import json
from io import BytesIO
from openai import OpenAI
from config import OPENAI_CONFIG, APP_CONFIG
from PIL import Image, ImageDraw, ImageFont

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
            
            # If no DALL-E models found, use a simulated model for testing
            if not available_models:
                logger.warning("No DALL-E models available. Using simulated model for testing.")
                return ["dall-e-simulated"]
            
            return available_models
        except Exception as e:
            logger.warning(f"Could not detect available models: {str(e)}")
            # Use simulated model as fallback
            return ["dall-e-simulated"]
    
    def _select_best_model(self):
        """Select the best available DALL-E model."""
        preferred_model = OPENAI_CONFIG.get("model", "dall-e-3")
        
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
            # Fallback to simulated model if no models detected
            return "dall-e-simulated"
    
    def validate_api_key(self):
        """Validate the API key by making a simple request."""
        try:
            # Make a simple models list request to validate the API key
            logger.info("Validating API key with models.list request")
            response = self.client.models.list(limit=1)
            # Log the response (but sanitize any sensitive information)
            logger.info(f"API key validation response: {response}")
            logger.info("API key validated successfully")
            return True
        except Exception as e:
            # Log detailed error information
            error_type = type(e).__name__
            error_msg = str(e)
            logger.error(f"API key validation failed: {error_type} - {error_msg}")
            
            # Try to extract and log more detailed error information if available
            if hasattr(e, 'response'):
                try:
                    status_code = e.response.status_code
                    error_json = e.response.json()
                    logger.error(f"API Error Details - Status: {status_code}, Response: {json.dumps(error_json)}")
                except:
                    pass
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
            # Check if we're using the simulated model
            if self.model == "dall-e-simulated":
                # Generate a placeholder image for testing
                logger.info("Using simulated model to generate placeholder image")
                
                # Create a blank image with text
                width, height = map(int, size.split('x'))
                image = Image.new('RGB', (width, height), color=(240, 240, 240))
                draw = ImageDraw.Draw(image)
                
                # Add prompt text
                font_size = max(12, min(24, width // 30))
                try:
                    font = ImageFont.truetype("arial.ttf", font_size)
                except IOError:
                    # Fallback to default font if arial not available
                    font = ImageFont.load_default()
                    
                # Wrap text to fit image width
                import textwrap
                wrapped_text = textwrap.fill(prompt, width=40)
                
                # Draw text
                text_color = (0, 0, 0)
                draw.text((20, 20), f"SIMULATED IMAGE\n\n{wrapped_text}", font=font, fill=text_color)
                
                # Add info about DALL-E access
                info_text = "Your account doesn't have DALL-E access.\nPlease enable it in your OpenAI account settings."
                draw.text((20, height - 60), info_text, font=font, fill=(200, 0, 0))
                
                # Convert to bytes
                img_byte_arr = BytesIO()
                image.save(img_byte_arr, format='PNG')
                img_byte_arr.seek(0)
                image_data = img_byte_arr.read()
                
                # Create usage info
                usage_info = {
                    "estimated_tokens": 0,
                    "prompt_tokens": len(prompt.split()),
                    "size": size,
                    "model": "simulated",
                    "n": n
                }
                
                return image_data, usage_info
            
            # Generate the image with appropriate parameters
            logger.info(f"Sending image generation request with params: {json.dumps(generation_params)}")
            response = self.client.images.generate(**generation_params)
            # Log response (excluding binary data)
            response_info = {
                "created": getattr(response, "created", None),
                "data_count": len(getattr(response, "data", [])),
                "model": getattr(response, "model", None)
            }
            logger.info(f"Image generation response info: {json.dumps(response_info)}")
            
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
                try:
                    # Check if response data exists and has the expected structure
                    if not response.data or len(response.data) == 0:
                        logger.error("No data in response")
                        return None, None
                    
                    # Log the response data structure for debugging
                    data_item = response.data[0]
                    has_b64 = hasattr(data_item, 'b64_json')
                    logger.info(f"Response data item has b64_json attribute: {has_b64}")
                    
                    if has_b64:
                        # Get the base64 encoded image data
                        b64_data = data_item.b64_json
                        
                        # Log the first 50 chars of base64 data for debugging
                        if b64_data:
                            logger.info(f"Received base64 data (first 50 chars): {b64_data[:50]}...")
                            # Decode the base64 data
                            image_data = base64.b64decode(b64_data)
                            logger.info(f"Successfully decoded base64 image data, length: {len(image_data)}")
                            return image_data, usage_info
                        else:
                            logger.error("b64_json attribute is empty")
                            return None, None
                    else:
                        # If b64_json is not available, try to get the URL
                        if hasattr(data_item, 'url') and data_item.url:
                            logger.info(f"No b64_json found, using URL instead: {data_item.url[:50]}...")
                            # Return the URL instead
                            return data_item.url, usage_info
                        else:
                            # Try to access b64_json as a dictionary key
                            try:
                                if isinstance(data_item, dict) and 'b64_json' in data_item:
                                    b64_data = data_item['b64_json']
                                    logger.info(f"Found b64_json as dictionary key, first 50 chars: {b64_data[:50]}...")
                                    image_data = base64.b64decode(b64_data)
                                    logger.info(f"Successfully decoded base64 image data from dict, length: {len(image_data)}")
                                    return image_data, usage_info
                            except:
                                pass
                            
                            # Last resort: try to convert to dict and access
                            try:
                                data_dict = vars(data_item)
                                if 'b64_json' in data_dict:
                                    b64_data = data_dict['b64_json']
                                    logger.info(f"Found b64_json in vars(), first 50 chars: {b64_data[:50]}...")
                                    image_data = base64.b64decode(b64_data)
                                    logger.info(f"Successfully decoded base64 image data from vars, length: {len(image_data)}")
                                    return image_data, usage_info
                            except:
                                pass
                                
                            logger.error("Response data item has neither b64_json nor url")
                            return None, None
                except Exception as e:
                    logger.error(f"Error decoding base64 data: {str(e)}")
                    # Log the response structure for debugging
                    try:
                        logger.error(f"Response structure: {dir(response)}")
                        logger.error(f"Response data structure: {dir(response.data[0])}")
                    except:
                        pass
                    return None, None
            else:
                # For URL response format, return the URL
                return response.data[0].url, usage_info
                
        except Exception as e:
            # Log detailed error information
            error_type = type(e).__name__
            error_msg = str(e)
            logger.error(f"Image generation failed: {error_type} - {error_msg}")
            
            # Check for specific billing errors
            billing_error = False
            error_message = "Unknown error"
            
            # Try to extract and log more detailed error information if available
            if hasattr(e, 'response'):
                try:
                    status_code = e.response.status_code
                    error_json = e.response.json()
                    logger.error(f"API Error Details - Status: {status_code}, Response: {json.dumps(error_json)}")
                    
                    # Check for specific error codes
                    if 'error' in error_json:
                        error_code = error_json['error'].get('code')
                        error_type = error_json['error'].get('type')
                        
                        if error_code == 'billing_hard_limit_reached' or error_type == 'insufficient_quota':
                            billing_error = True
                            error_message = "Billing limit reached. Please check your OpenAI account billing settings."
                        elif error_code == 'model_not_found':
                            error_message = f"Model {self.model} not available to your account."
                except:
                    pass
            
            # If billing error detected, generate a special error image
            if billing_error:
                logger.warning("Billing error detected, generating error image")
                
                # Create a blank image with text explaining the billing issue
                width, height = map(int, size.split('x'))
                image = Image.new('RGB', (width, height), color=(240, 240, 240))
                draw = ImageDraw.Draw(image)
                
                # Add error text
                font_size = max(12, min(24, width // 30))
                try:
                    font = ImageFont.truetype("arial.ttf", font_size)
                except IOError:
                    font = ImageFont.load_default()
                    
                # Draw error message
                draw.text((20, 20), "BILLING ERROR", font=font, fill=(200, 0, 0))
                draw.text((20, 60), error_message, font=font, fill=(0, 0, 0))
                draw.text((20, 100), "To fix this:", font=font, fill=(0, 0, 0))
                draw.text((20, 140), "1. Go to platform.openai.com", font=font, fill=(0, 0, 0))
                draw.text((20, 180), "2. Check your billing settings", font=font, fill=(0, 0, 0))
                draw.text((20, 220), "3. Add a payment method or increase limits", font=font, fill=(0, 0, 0))
                
                # Add the prompt at the bottom
                wrapped_text = textwrap.fill(f"Your prompt: {prompt}", width=40)
                draw.text((20, height - 100), wrapped_text, font=font, fill=(100, 100, 100))
                
                # Convert to bytes
                img_byte_arr = BytesIO()
                image.save(img_byte_arr, format='PNG')
                img_byte_arr.seek(0)
                image_data = img_byte_arr.read()
                
                # Create usage info
                usage_info = {
                    "estimated_tokens": 0,
                    "prompt_tokens": len(prompt.split()),
                    "size": size,
                    "model": "billing_error",
                    "n": n,
                    "error": error_message
                }
                
                return image_data, usage_info
            
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
