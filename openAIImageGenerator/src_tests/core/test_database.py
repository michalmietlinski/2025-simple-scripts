"""
Tests for the database module.
"""
import pytest
from unittest.mock import MagicMock, patch
import sys
import os
import sqlite3
import json
from pathlib import Path

# Add the parent directory to the path to allow imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# Import the module to test
from src.core.database import DatabaseManager, DatabaseError
from src.core.data_models import Prompt, Generation, TemplateVariable

class TestDatabaseManager:
    """Tests for the DatabaseManager class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        # Create an in-memory database for testing
        self.db_path = ":memory:"
        self.db_manager = DatabaseManager(db_path=self.db_path)
    
    def test_init_creates_tables(self):
        """Test that initialization creates the required tables."""
        # Arrange
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Act
        # Tables should already be created by the setup
        
        # Assert
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        
        assert "prompt_history" in tables
        assert "template_variables" in tables
        assert "batch_generations" in tables
        assert "generation_history" in tables
        assert "usage_stats" in tables
        
        conn.close()
    
    def test_save_prompt(self):
        """Test saving a prompt to the database."""
        # Arrange
        prompt_text = "Test prompt"
        is_template = False
        template_variables = None
        
        # Act
        prompt_id = self.db_manager.save_prompt(prompt_text, is_template, template_variables)
        
        # Assert
        assert prompt_id is not None
        assert prompt_id > 0
        
        # Verify the prompt was saved
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT prompt_text, is_template FROM prompt_history WHERE id = ?", (prompt_id,))
        result = cursor.fetchone()
        conn.close()
        
        assert result is not None
        assert result[0] == prompt_text
        assert result[1] == 0  # False is stored as 0
    
    def test_get_prompt_history(self):
        """Test retrieving prompt history."""
        # Arrange
        # Add some prompts
        self.db_manager.save_prompt("Prompt 1", False, None)
        self.db_manager.save_prompt("Prompt 2", False, None)
        self.db_manager.save_prompt("Template 1", True, ["var1", "var2"])
        
        # Act
        prompts = self.db_manager.get_prompt_history()
        
        # Assert
        assert len(prompts) == 3
        assert isinstance(prompts[0], Prompt)
        assert prompts[0].prompt_text == "Prompt 1"
        assert prompts[2].is_template == True
        assert prompts[2].template_variables == ["var1", "var2"]
    
    def test_save_generation(self):
        """Test saving a generation record."""
        # Arrange
        prompt_id = self.db_manager.save_prompt("Test generation prompt", False, None)
        image_path = "test/path/image.png"
        parameters = {"model": "dall-e-3", "size": "1024x1024"}
        token_usage = 100
        cost = 0.02
        
        # Act
        generation_id = self.db_manager.save_generation(
            prompt_id, image_path, parameters, token_usage, cost
        )
        
        # Assert
        assert generation_id is not None
        assert generation_id > 0
        
        # Verify the generation was saved
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT prompt_id, image_path, parameters FROM generation_history WHERE id = ?", (generation_id,))
        result = cursor.fetchone()
        conn.close()
        
        assert result is not None
        assert result[0] == prompt_id
        assert result[1] == image_path
        assert json.loads(result[2]) == parameters
    
    def test_get_generation_history(self):
        """Test retrieving generation history."""
        # Arrange
        # Add a prompt and generation
        prompt_id = self.db_manager.save_prompt("Test prompt for history", False, None)
        self.db_manager.save_generation(
            prompt_id, "path/to/image1.png", {"model": "dall-e-3"}, 100, 0.02
        )
        self.db_manager.save_generation(
            prompt_id, "path/to/image2.png", {"model": "dall-e-3"}, 100, 0.02
        )
        
        # Act
        generations = self.db_manager.get_generation_history()
        
        # Assert
        assert len(generations) == 2
        assert isinstance(generations[0], Generation)
        assert generations[0].prompt_id == prompt_id
        assert generations[0].image_path == "path/to/image1.png"
        assert generations[0].parameters["model"] == "dall-e-3"
    
    def test_get_template_variables(self):
        """Test retrieving template variables."""
        # Arrange
        # Add a template variable
        self.db_manager.save_template_variable("color", ["red", "blue", "green"])
        
        # Act
        variables = self.db_manager.get_template_variables()
        
        # Assert
        assert len(variables) == 1
        assert isinstance(variables[0], TemplateVariable)
        assert variables[0].name == "color"
        assert variables[0].values == ["red", "blue", "green"]
    
    def test_get_model_distribution(self):
        """Test retrieving model distribution statistics."""
        # Arrange
        prompt_id = self.db_manager.save_prompt("Test prompt", False, None)
        # Add generations with different models
        self.db_manager.save_generation(
            prompt_id, "path1.png", {"model": "dall-e-3"}, 100, 0.02
        )
        self.db_manager.save_generation(
            prompt_id, "path2.png", {"model": "dall-e-3"}, 100, 0.02
        )
        self.db_manager.save_generation(
            prompt_id, "path3.png", {"model": "dall-e-2"}, 50, 0.01
        )
        
        # Act
        distribution = self.db_manager.get_model_distribution()
        
        # Assert
        assert len(distribution) == 2
        assert distribution[0][0] == "dall-e-3"  # Most used model first
        assert distribution[0][1] == 2  # Count of dall-e-3 usages
        assert distribution[1][0] == "dall-e-2"
        assert distribution[1][1] == 1
    
    def test_database_error_handling(self):
        """Test that database errors are properly handled."""
        # Arrange
        # Create a database manager with an invalid path to force an error
        invalid_db_manager = DatabaseManager(db_path="/nonexistent/path/db.sqlite")
        
        # Act & Assert
        with pytest.raises(DatabaseError):
            invalid_db_manager.get_prompt_history()

if __name__ == "__main__":
    pytest.main(["-xvs", __file__]) 
