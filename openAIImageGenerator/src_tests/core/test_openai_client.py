"""
Tests for the openai_client module.
"""
import pytest
from unittest.mock import MagicMock, patch
import sys
import os
import base64
from io import BytesIO
from PIL import Image
import requests

# Add the parent directory to the path to allow imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# Import the module to test
from src.core.openai_client import OpenAIImageClient

class TestOpenAIImageClient:
    """Tests for the OpenAIImageClient class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        # Create patcher for OpenAI client
        self.openai_patcher = patch('src.core.openai_client.OpenAI')
        self.mock_openai = self.openai_patcher.start()
        
        # Configure mock OpenAI client
        self.mock_openai_instance = MagicMock()
        self.mock_openai.return_value = self.mock_openai_instance
        
        # Mock models list response
        self.mock_models_response = MagicMock()
        self.mock_models_response.data = [
            MagicMock(id="dall-e-3"),
            MagicMock(id="dall-e-2")
        ]
        self.mock_openai_instance.models.list.return_value = self.mock_models_response
        
        # Create the OpenAI client with mocked dependencies
        self.client = OpenAIImageClient(api_key="test_key")
        
        # Reset the mock call counts after initialization
        self.mock_openai_instance.models.list.reset_mock()
    
    def teardown_method(self):
        """Tear down test fixtures."""
        self.openai_patcher.stop()
    
    def test_init(self):
        """Test initialization of the OpenAI client."""
        # Create a new client to test initialization
        with patch('src.core.openai_client.OpenAI') as mock_openai:
            mock_instance = MagicMock()
            mock_openai.return_value = mock_instance
            
            # Mock models list response
            mock_models_response = MagicMock()
            mock_models_response.data = [
                MagicMock(id="dall-e-3"),
                MagicMock(id="dall-e-2")
            ]
            mock_instance.models.list.return_value = mock_models_response
            
            # Create a new client
            client = OpenAIImageClient(api_key="test_key")
            
            # Assert
            assert client.api_key == "test_key"
            assert client.client == mock_instance
            mock_openai.assert_called_once_with(api_key="test_key")
            assert "dall-e-3" in client.available_models
            assert "dall-e-2" in client.available_models
    
    def test_detect_available_models(self):
        """Test detecting available models."""
        # Act
        models = self.client._detect_available_models()
        
        # Assert
        assert "dall-e-3" in models
        assert "dall-e-2" in models
        self.mock_openai_instance.models.list.assert_called_once()
    
    def test_select_best_model(self):
        """Test selecting the best model."""
        # Arrange
        self.client.available_models = ["dall-e-3", "dall-e-2"]
        
        # Act
        model = self.client._select_best_model()
        
        # Assert
        assert model == "dall-e-3"
    
    def test_select_best_model_fallback(self):
        """Test selecting the best model with fallback."""
        # Arrange
        self.client.available_models = ["dall-e-2"]
        
        # Act
        model = self.client._select_best_model()
        
        # Assert
        assert model == "dall-e-2"
    
    def test_validate_api_key_valid(self):
        """Test validation of a valid API key."""
        # Act
        result = self.client.validate_api_key()
        
        # Assert
        assert result is True
        self.mock_openai_instance.models.list.assert_called_once()
    
    def test_validate_api_key_invalid(self):
        """Test validation of an invalid API key."""
        # Arrange
        self.mock_openai_instance.models.list.side_effect = Exception("Invalid API key")
        
        # Act
        result = self.client.validate_api_key()
        
        # Assert
        assert result is False
        self.mock_openai_instance.models.list.assert_called_once()
    
    def test_generate_image(self):
        """Test generating an image."""
        # Arrange
        prompt = "A beautiful sunset over mountains"
        
        # Mock the OpenAI response
        mock_response = MagicMock()
        mock_response.data = [
            MagicMock(
                url="https://example.com/image.png",
                revised_prompt="A stunning sunset over mountains",
                b64_json=None
            )
        ]
        self.mock_openai_instance.images.generate.return_value = mock_response
        
        # Mock the image download and PIL Image
        with patch('requests.get') as mock_get, patch('PIL.Image.open') as mock_image_open:
            mock_get_response = MagicMock()
            mock_get_response.content = b'fake_image_data'
            mock_get_response.status_code = 200
            mock_get.return_value = mock_get_response
            
            mock_image = MagicMock()
            mock_image_open.return_value = mock_image
            
            # Act
            images, metadata = self.client.generate_image(prompt=prompt)
            
            # Assert
            assert len(images) == 1
            self.mock_openai_instance.images.generate.assert_called_once()
            mock_get.assert_called_once()
            mock_image_open.assert_called_once()

if __name__ == "__main__":
    pytest.main(["-xvs", __file__]) 
