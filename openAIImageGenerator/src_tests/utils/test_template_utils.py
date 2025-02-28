"""
Tests for the template_utils module.
"""
import pytest
from unittest.mock import MagicMock, patch
import sys
import os
import json

# Add the parent directory to the path to allow imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# Import the module to test
from src.utils.template_utils import TemplateProcessor

class TestTemplateProcessor:
    """Tests for the TemplateProcessor class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.mock_db_manager = MagicMock()
        self.template_processor = TemplateProcessor(self.mock_db_manager)
    
    def test_extract_variables(self):
        """Test extracting variables from template text."""
        # Arrange
        template_text = "This is a {{variable1}} template with {{variable2}} and {{variable3}}."
        
        # Act
        variables = self.template_processor.extract_variables(template_text)
        
        # Assert
        assert len(variables) == 3
        assert "variable1" in variables
        assert "variable2" in variables
        assert "variable3" in variables
    
    def test_extract_variables_with_duplicates(self):
        """Test extracting variables with duplicates."""
        # Arrange
        template_text = "This {{variable1}} has {{variable2}} and {{variable1}} again."
        
        # Act
        variables = self.template_processor.extract_variables(template_text)
        
        # Assert
        assert len(variables) == 2
        assert "variable1" in variables
        assert "variable2" in variables
    
    def test_extract_variables_empty(self):
        """Test extracting variables from text without variables."""
        # Arrange
        template_text = "This is a template without variables."
        
        # Act
        variables = self.template_processor.extract_variables(template_text)
        
        # Assert
        assert len(variables) == 0
    
    def test_validate_template_valid(self):
        """Test validating a valid template."""
        # Arrange
        template_text = "This is a {{variable1}} template with {{variable2}}."
        
        # Act
        is_valid, error_message = self.template_processor.validate_template(template_text)
        
        # Assert
        assert is_valid is True
        assert error_message == ""
    
    def test_validate_template_unbalanced_braces(self):
        """Test validating a template with unbalanced braces."""
        # Arrange
        template_text = "This is a {{variable1}} template with {{variable2."
        
        # Act
        is_valid, error_message = self.template_processor.validate_template(template_text)
        
        # Assert
        assert is_valid is False
        assert "Unbalanced braces" in error_message
    
    def test_validate_template_empty_variable(self):
        """Test validating a template with empty variable names."""
        # Arrange
        template_text = "This is a {{}} template."
        
        # Act
        is_valid, error_message = self.template_processor.validate_template(template_text)
        
        # Assert
        assert is_valid is False
        assert "Empty variable names" in error_message
    
    def test_validate_template_nested_variables(self):
        """Test validating a template with nested variables."""
        # Arrange
        template_text = "This is a {{variable1 {{nested}}}} template."
        
        # Act
        is_valid, error_message = self.template_processor.validate_template(template_text)
        
        # Assert
        assert is_valid is False
        assert "Nested variables" in error_message
    
    def test_substitute_variables(self):
        """Test substituting variables in template text."""
        # Arrange
        template_text = "This is a {{variable1}} template with {{variable2}}."
        variable_values = {
            "variable1": "test",
            "variable2": "substitution"
        }
        
        # Act
        result = self.template_processor.substitute_variables(template_text, variable_values)
        
        # Assert
        assert result == "This is a test template with substitution."
    
    def test_substitute_variables_missing_value(self):
        """Test substituting variables with missing values."""
        # Arrange
        template_text = "This is a {{variable1}} template with {{variable2}}."
        variable_values = {
            "variable1": "test"
        }
        
        # Act
        result = self.template_processor.substitute_variables(template_text, variable_values)
        
        # Assert
        assert result == "This is a test template with [variable2]."

if __name__ == "__main__":
    pytest.main(["-xvs", __file__]) 
