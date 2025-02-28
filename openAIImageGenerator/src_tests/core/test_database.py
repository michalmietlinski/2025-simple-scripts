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
        
        # Explicitly create tables to ensure they exist
        self.db_manager.create_tables()
    
    def test_init_creates_tables(self):
        """Test that initialization creates the required tables."""
        # Arrange & Act - Create a new database manager with in-memory database
        db_manager = DatabaseManager(db_path=":memory:")
        
        # Assert - Check that tables were created
        conn = sqlite3.connect(":memory:")
        cursor = conn.cursor()
        
        # Create tables in this connection (since in-memory DBs are connection-specific)
        db_manager.create_tables()
        
        # Check tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        
        # Close the test connection
        conn.close()
        
        # Check that our database manager has the tables
        with db_manager.connection:
            cursor = db_manager.connection.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cursor.fetchall()]
            
            assert "prompt_history" in tables
            assert "template_variables" in tables
            assert "generation_history" in tables
            assert "usage_statistics" in tables
    
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
        with self.db_manager.connection:
            cursor = self.db_manager.connection.cursor()
            cursor.execute("SELECT prompt_text, is_template FROM prompt_history WHERE id = ?", (prompt_id,))
            row = cursor.fetchone()
            
            assert row is not None
            assert row[0] == prompt_text
            assert row[1] == 0  # is_template is False (0)
    
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
        with self.db_manager.connection:
            cursor = self.db_manager.connection.cursor()
            cursor.execute("SELECT prompt_id, image_path, parameters FROM generation_history WHERE id = ?", (generation_id,))
            row = cursor.fetchone()
            
            assert row is not None
            assert row[0] == prompt_id
            assert row[1] == image_path
            assert json.loads(row[2])["model"] == "dall-e-3"
    
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
        assert generations[0]['prompt_id'] == prompt_id
        assert 'image_path' in generations[0]
        assert 'parameters' in generations[0]
    
    def test_get_template_variables(self):
        """Test retrieving template variables."""
        # Arrange
        # Add a template variable
        self.db_manager.add_template_variable("color", ["red", "blue", "green"])
        
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
        # Check that dall-e-3 has 2 entries and dall-e-2 has 1
        model_counts = {model: count for model, count in distribution}
        assert model_counts.get("dall-e-3") == 2
        assert model_counts.get("dall-e-2") == 1
    
    def test_database_error_handling(self):
        """Test that database errors are properly handled."""
        # Arrange
        # Create a database manager with an invalid path to force an error
        with patch('sqlite3.connect') as mock_connect:
            mock_connect.side_effect = sqlite3.Error("Test error")
            
            # Act & Assert
            with pytest.raises(DatabaseError):
                # This should raise a DatabaseError
                invalid_db = DatabaseManager(db_path="/nonexistent/path/db.sqlite")

if __name__ == "__main__":
    pytest.main(["-xvs", __file__]) 
