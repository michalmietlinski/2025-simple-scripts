"""OpenAI API client for image generation."""

from typing import List, Optional, Dict, Any, Tuple
import logging
import base64
import json
from io import BytesIO
from openai import OpenAI
from PIL import Image, ImageDraw, ImageFont
import requests

logger = logging.getLogger(__name__)

class OpenAIImageClient:
    """Handles all OpenAI API interactions for image generation."""
    
    def __init__(self, api_key: str):
        """Initialize OpenAI client.
        
        Args:
            api_key: OpenAI API key
        """
        self.api_key = api_key
        self.client = OpenAI(api_key=api_key)
        self.available_models = self._detect_available_models()
        self.model = self._select_best_model()
        logger.info(f"OpenAI client initialized with model: {self.model}")

    def _detect_available_models(self) -> List[str]:
        """Detect which DALL-E models are available."""
        try:
            models = self.client.models.list()
            available_models = []
            
            for model in models.data:
                if "dall-e" in model.id.lower():
                    available_models.append(model.id)
                    logger.info(f"Found available model: {model.id}")
            
            if not available_models:
                logger.warning("No DALL-E models available. Using simulated mode.")
                return ["dall-e-simulated"]
            
            return available_models
        except Exception as e:
            logger.warning(f"Could not detect models: {str(e)}")
            return ["dall-e-simulated"]

    def _select_best_model(self) -> str:
        """Select the best available DALL-E model."""
        if "dall-e-3" in self.available_models:
            return "dall-e-3"
        elif "dall-e-2" in self.available_models:
            return "dall-e-2"
        return self.available_models[0]

    def validate_api_key(self) -> bool:
        """Validate the API key."""
        try:
            # Just try to list one model to validate the key
            self.client.models.list()
            logger.info("API key validated successfully")
            return True
        except Exception as e:
            logger.error(f"API key validation failed: {str(e)}")
            return False

    def get_model_capabilities(self) -> Dict[str, Any]:
        """Get current model capabilities."""
        capabilities = {
            "supports_quality": False,
            "supports_style": False,
            "max_size": "1024x1024",
            "sizes": ["256x256", "512x512", "1024x1024"]
        }
        
        if "dall-e-3" in self.model:
            capabilities.update({
                "supports_quality": True,
                "supports_style": True,
                "max_size": "1792x1024",
                "sizes": ["1024x1024", "1792x1024", "1024x1792"]
            })
        
        return capabilities

    def _create_simulated_image(
        self,
        prompt: str,
        size: str,
        n: int
    ) -> Tuple[List[Image.Image], Dict[str, Any]]:
        """Create a simulated image for testing."""
        width, height = map(int, size.split('x'))
        images = []
        
        for _ in range(n):
            image = Image.new('RGB', (width, height), color=(240, 240, 240))
            draw = ImageDraw.Draw(image)
            
            try:
                font = ImageFont.truetype("arial.ttf", max(12, min(24, width // 30)))
            except IOError:
                font = ImageFont.load_default()
            
            draw.text((20, 20), f"SIMULATED IMAGE\n\n{prompt}", font=font, fill=(0, 0, 0))
            draw.text(
                (20, height - 60),
                "Your account doesn't have DALL-E access.\nPlease enable it in OpenAI settings.",
                font=font,
                fill=(200, 0, 0)
            )
            images.append(image)
        
        usage_info = {
            "estimated_tokens": 0,
            "prompt_tokens": len(prompt.split()),
            "size": size,
            "model": "simulated",
            "n": n
        }
        
        return images, usage_info

    def generate_image(
        self,
        prompt: str,
        size: str = "1024x1024",
        quality: str = "standard",
        style: Optional[str] = None,
        n: int = 1
    ) -> Tuple[List[Image.Image], Dict[str, Any]]:
        """Generate images using DALL-E.
        
        Args:
            prompt: Text description of the desired image
            size: Image size (e.g., "1024x1024")
            quality: Image quality ("standard" or "hd")
            style: Image style (vivid or natural)
            n: Number of images to generate
            
        Returns:
            Tuple of (List of PIL Images, Usage information)
            
        Raises:
            Exception: If image generation fails
        """
        try:
            # Check if using simulated mode
            if self.model == "dall-e-simulated":
                return self._create_simulated_image(prompt, size, n)

            # Get model capabilities and validate size
            capabilities = self.get_model_capabilities()
            if size not in capabilities["sizes"]:
                logger.warning(f"Size {size} not supported, using {capabilities['max_size']}")
                size = capabilities["max_size"]

            # Prepare generation parameters
            params = {
                "model": self.model,
                "prompt": prompt,
                "size": size,
                "n": n,
                "response_format": "b64_json"
            }

            # Add quality and style for DALL-E 3
            if capabilities["supports_quality"]:
                params["quality"] = quality
            if capabilities["supports_style"] and style:
                params["style"] = style

            logger.info(f"Generating image with params: {json.dumps(params)}")
            response = self.client.images.generate(**params)

            # Process images
            images = []
            revised_prompt = None
            for data in response.data:
                if hasattr(data, 'revised_prompt') and data.revised_prompt:
                    revised_prompt = data.revised_prompt
                
                if data.b64_json:
                    # Handle base64 encoded image
                    image_data = base64.b64decode(data.b64_json)
                    image = Image.open(BytesIO(image_data))
                    images.append(image)
                elif data.url:
                    # Handle URL-based image
                    response = requests.get(data.url)
                    if response.status_code == 200:
                        image = Image.open(BytesIO(response.content))
                        images.append(image)
                    else:
                        logger.error(f"Failed to download image from URL: {data.url}")
                        raise Exception(f"Failed to download image: HTTP {response.status_code}")

            # Calculate usage information
            size_multiplier = 2 if size == "1024x1024" else 3
            quality_multiplier = 1.5 if quality == "hd" else 1
            prompt_tokens = len(prompt.split())
            
            usage_info = {
                "estimated_tokens": int(prompt_tokens * size_multiplier * quality_multiplier * n),
                "prompt_tokens": prompt_tokens,
                "size": size,
                "model": self.model,
                "n": n
            }
            
            if revised_prompt:
                usage_info["revised_prompt"] = revised_prompt

            logger.info(f"Successfully generated {len(images)} images")
            return images, usage_info

        except Exception as e:
            logger.error(f"Failed to generate image: {str(e)}")
            raise

    def generate_variation(
        self,
        image: Image.Image,
        size: str = "1024x1024",
        n: int = 1
    ) -> Tuple[List[Image.Image], Dict[str, Any]]:
        """Generate variations of an input image.
        
        Args:
            image: Input PIL Image
            size: Output image size
            n: Number of variations to generate
            
        Returns:
            Tuple of (List of PIL Images, Usage information)
        """
        try:
            # Convert image to PNG bytes
            buffer = BytesIO()
            image.save(buffer, format="PNG")
            image_bytes = buffer.getvalue()

            response = self.client.images.create_variation(
                image=image_bytes,
                size=size,
                n=n,
                response_format="b64_json"
            )

            # Process variations
            variations = []
            for data in response.data:
                var_data = base64.b64decode(data.b64_json)
                var_image = Image.open(BytesIO(var_data))
                variations.append(var_image)

            usage_info = {
                "size": size,
                "model": self.model,
                "n": n
            }

            logger.info(f"Successfully generated {len(variations)} variations")
            return variations, usage_info

        except Exception as e:
            logger.error(f"Failed to generate variation: {str(e)}")
            raise 
