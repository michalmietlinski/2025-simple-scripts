"""
Tests for the main_window module.
"""
import pytest
from unittest.mock import MagicMock, patch
import sys
import os
import tkinter as tk

# Add the parent directory to the path to allow imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# Import the module to test
from src.ui.main_window import MainWindow
from src.core.openai_client import OpenAIImageClient
from src.core.database import DatabaseManager
from src.core.file_manager import FileManager
from src.utils.settings_manager import SettingsManager
from src.utils.error_handler import ErrorHandler

class TestMainWindow:
    """Tests for the MainWindow class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        # Mock dependencies
        self.root = MagicMock(spec=tk.Tk)
        self.openai_client = MagicMock(spec=OpenAIImageClient)
        self.db_manager = MagicMock(spec=DatabaseManager)
        self.file_manager = MagicMock(spec=FileManager)
        self.settings_manager = MagicMock(spec=SettingsManager)
        self.error_handler = MagicMock(spec=ErrorHandler)
        
        # Configure mocks
        self.settings_manager.get_settings.return_value = {
            "api_key": "test_key",
            "output_dir": "test_output",
            "cleanup_enabled": True,
            "cleanup_days": 30,
            "page_size": 10
        }
        
        # Create the main window with mocked dependencies
        self.main_window = MainWindow(
            self.root,
            self.openai_client,
            self.db_manager,
            self.file_manager,
            self.settings_manager,
            self.error_handler
        )
    
    @patch('src.ui.main_window.ttk.Notebook')
    @patch('src.ui.main_window.GenerationTab')
    @patch('src.ui.main_window.HistoryTab')
    def test_setup_main_ui(self, mock_history_tab, mock_generation_tab, mock_notebook):
        """Test that the main UI is set up correctly."""
        # Arrange
        mock_notebook_instance = MagicMock()
        mock_notebook.return_value = mock_notebook_instance
        
        # Act
        self.main_window._setup_main_ui()
        
        # Assert
        mock_notebook.assert_called_once()
        mock_generation_tab.assert_called_once()
        mock_history_tab.assert_called_once()
        mock_notebook_instance.add.assert_called()
    
    def test_verify_api_key_valid(self):
        """Test API key verification with a valid key."""
        # Arrange
        self.openai_client.validate_api_key.return_value = True
        
        # Act
        result = self.main_window._verify_api_key()
        
        # Assert
        assert result is True
        self.openai_client.validate_api_key.assert_called_once()
    
    def test_verify_api_key_invalid(self):
        """Test API key verification with an invalid key."""
        # Arrange
        self.openai_client.validate_api_key.return_value = False
        
        # Act
        result = self.main_window._verify_api_key()
        
        # Assert
        assert result is False
        self.openai_client.validate_api_key.assert_called_once()
    
    def test_cleanup_files(self):
        """Test file cleanup functionality."""
        # Arrange
        self.settings_manager.get_settings.return_value = {
            "cleanup_enabled": True,
            "cleanup_days": 30
        }
        
        # Act
        self.main_window._cleanup_files()
        
        # Assert
        self.file_manager.cleanup_old_files.assert_called_once_with(days=30)
    
    def test_show_settings(self):
        """Test showing settings dialog."""
        # Act
        with patch('src.ui.main_window.SettingsDialog') as mock_dialog:
            mock_dialog_instance = MagicMock()
            mock_dialog.return_value = mock_dialog_instance
            
            self.main_window._show_settings()
            
            # Assert
            mock_dialog.assert_called_once()
            mock_dialog_instance.focus.assert_called_once()
    
    def test_set_status(self):
        """Test setting status message."""
        # Arrange
        status_message = "Test status message"
        
        # Act
        self.main_window.set_status(status_message)
        
        # Assert
        self.main_window.status_var.set.assert_called_once_with(status_message)

if __name__ == "__main__":
    pytest.main(["-xvs", __file__]) 
