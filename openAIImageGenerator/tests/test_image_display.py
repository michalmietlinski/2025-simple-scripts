import unittest
from unittest.mock import MagicMock, patch
import sys
import os
import tkinter as tk
from PIL import Image
from io import BytesIO

# Add parent directory to path to import app modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class TestImageDisplay(unittest.TestCase):
    """Test cases for image display functionality in the DALL-E Generator App."""
    
    def setUp(self):
        """Set up the test environment."""
        # Create mock objects
        self.root = MagicMock()
        self.preview_frame = MagicMock()
        
        # Create a test image
        self.test_image = MagicMock()
        self.test_image.size = (512, 512)
        self.image_data = b'test_image_data'
        
        # Create a mock app
        self.app = MagicMock()
        
        # Import the class to be tested
        from app import DALLEGeneratorApp
        
        # Bind methods to be tested to the mock app
        self.app.display_image = DALLEGeneratorApp.display_image.__get__(self.app)
        self.app.open_output_directory = DALLEGeneratorApp.open_output_directory.__get__(self.app)
        self.app.save_image = DALLEGeneratorApp.save_image.__get__(self.app)
        self.app.view_original_resolution = DALLEGeneratorApp.view_original_resolution.__get__(self.app)
        self.app.delete_selected_prompt = DALLEGeneratorApp.delete_selected_prompt.__get__(self.app)
        self.app.clear_all_prompts = DALLEGeneratorApp.clear_all_prompts.__get__(self.app)
        self.app.delete_selected_generation = DALLEGeneratorApp.delete_selected_generation.__get__(self.app)
        self.app.clear_all_generations = DALLEGeneratorApp.clear_all_generations.__get__(self.app)
        
        # Set up mock attributes
        self.app.root = self.root
        self.app.preview_frame = self.preview_frame
        self.app.preview_label = MagicMock()
        self.app.file_manager = MagicMock()
        self.app.db_manager = MagicMock()
        self.app.config = {
            'output_directory': '/mock/output/directory'
        }
    
    @patch('tkinter.Toplevel')
    @patch('tkinter.messagebox.showerror')
    @patch('tkinter.Frame')
    @patch('tkinter.Button')
    @patch('tkinter.Canvas')
    @patch('tkinter.Scrollbar')
    @patch('PIL.ImageTk.PhotoImage')
    def test_view_original_resolution(self, mock_photo_image, mock_scrollbar, mock_canvas, 
                                     mock_button, mock_frame, mock_showerror, mock_toplevel):
        """Test viewing image in original resolution."""
        # Set up the original image
        self.app.original_image = self.test_image
        
        # Mock the toplevel window and its components
        mock_top = MagicMock()
        mock_toplevel.return_value = mock_top
        mock_top.winfo_screenwidth.return_value = 1920
        mock_top.winfo_screenheight.return_value = 1080
        
        # Call the method
        self.app.view_original_resolution()
        
        # Verify toplevel window was created
        mock_toplevel.assert_called_once()
        
        # Verify window title was set
        mock_top.title.assert_called_with("Full Resolution Image")
        
        # Verify no error message was shown
        mock_showerror.assert_not_called()
    
    @patch('tkinter.messagebox.showerror')
    def test_view_original_resolution_no_image(self, mock_showerror):
        """Test viewing original resolution when no image is available."""
        # Ensure no original image is set
        if hasattr(self.app, 'original_image'):
            delattr(self.app, 'original_image')
        
        # Call the method
        self.app.view_original_resolution()
        
        # Verify error message was shown
        mock_showerror.assert_called_with("Error", "No image available")
    
    @patch('os.path.exists')
    @patch('os.startfile')
    @patch('tkinter.messagebox.showerror')
    def test_open_output_directory(self, mock_showerror, mock_startfile, mock_exists):
        """Test opening the output directory."""
        # Configure mock to indicate directory exists
        mock_exists.return_value = True
        
        # Call the method
        self.app.open_output_directory()
        
        # Verify directory existence was checked
        mock_exists.assert_called_once()
        
        # Verify startfile was called to open the directory
        mock_startfile.assert_called_once()
        
        # Verify no error message was shown
        mock_showerror.assert_not_called()
    
    @patch('os.path.exists')
    @patch('tkinter.messagebox.showerror')
    def test_open_output_directory_not_found(self, mock_showerror, mock_exists):
        """Test opening output directory when it doesn't exist."""
        # Configure mock to indicate directory doesn't exist
        mock_exists.return_value = False
        
        # Call the method
        self.app.open_output_directory()
        
        # Verify directory existence was checked
        mock_exists.assert_called_once()
        
        # Verify error message was shown
        mock_showerror.assert_called_with("Error", "Output directory not found")
    
    @patch('tkinter.simpledialog.askstring')
    @patch('tkinter.messagebox.showinfo')
    @patch('PIL.Image.open')
    @patch('os.path.exists')
    @patch('os.path.getsize')
    def test_save_image(self, mock_getsize, mock_exists, mock_open, mock_showinfo, mock_askstring):
        """Test saving an image without showing any message."""
        # Set up current image
        self.app.current_image = {
            'data': b'test_image_data',
            'prompt': 'test prompt'
        }
        
        # Configure mocks
        mock_exists.return_value = True
        mock_getsize.return_value = 1024  # 1KB
        mock_open.return_value = MagicMock()
        mock_askstring.return_value = "Test description"
        
        # Call save_image
        self.app.save_image()
        
        # Verify file_manager.save_image was called once
        self.app.file_manager.save_image.assert_called_once()
        
        # Verify no success message was shown
        mock_showinfo.assert_not_called()

    @patch('tkinter.messagebox.askyesno')
    def test_delete_selected_prompt(self, mock_askyesno):
        """Test deleting a selected prompt."""
        # Configure mock
        mock_askyesno.return_value = True
        
        # Set up prompt listbox with a selection
        self.app.prompt_listbox = MagicMock()
        self.app.prompt_listbox.curselection.return_value = (0,)
        self.app.prompt_listbox.get.return_value = "Test prompt"
        
        # Set up prompt history
        self.app.prompt_history = [{"id": 1, "text": "Test prompt"}]
        
        # Set up selected prompt ID
        self.app.selected_prompt_id = 1
        
        # Mock the search_prompts method to avoid calling it
        original_search_prompts = self.app.search_prompts
        self.app.search_prompts = MagicMock()
        
        try:
            # Call delete_selected_prompt
            self.app.delete_selected_prompt()
            
            # Verify db_manager.delete_prompt was called
            self.app.db_manager.delete_prompt.assert_called_once_with(1)
            
            # Verify search_prompts was called to refresh the list
            self.app.search_prompts.assert_called_once()
        finally:
            # Restore original method
            self.app.search_prompts = original_search_prompts

    @patch('tkinter.messagebox.askyesno')
    def test_clear_all_prompts(self, mock_askyesno):
        """Test clearing all prompts."""
        # Configure mock
        mock_askyesno.return_value = True
        
        # Set up prompt listbox
        self.app.prompt_listbox = MagicMock()
        
        # Mock the search_prompts method to avoid calling it
        original_search_prompts = self.app.search_prompts
        self.app.search_prompts = MagicMock()
        
        try:
            # Call clear_all_prompts
            self.app.clear_all_prompts()
            
            # Verify db_manager.clear_all_prompts was called
            self.app.db_manager.clear_all_prompts.assert_called_once()
            
            # Verify search_prompts was called to refresh the list
            self.app.search_prompts.assert_called_once()
        finally:
            # Restore original method
            self.app.search_prompts = original_search_prompts

    @patch('tkinter.messagebox.askyesno')
    def test_delete_selected_generation(self, mock_askyesno):
        """Test deleting a selected generation."""
        # Configure mock
        mock_askyesno.return_value = True
        
        # Set up generation listbox with a selection
        self.app.generation_listbox = MagicMock()
        self.app.generation_listbox.curselection.return_value = (0,)
        self.app.generation_listbox.get.return_value = "Test generation"
        
        # Set up generation history
        self.app.generation_history = [{"id": 1, "description": "Test generation"}]
        
        # Set up selected generation
        self.app.selected_generation = {"id": 1, "description": "Test generation"}
        
        # Mock the search_generations method to avoid calling it
        original_search_generations = self.app.search_generations
        self.app.search_generations = MagicMock()
        
        try:
            # Call delete_selected_generation
            self.app.delete_selected_generation()
            
            # Verify db_manager.delete_generation was called
            self.app.db_manager.delete_generation.assert_called_once_with(1)
            
            # Verify search_generations was called to refresh the list
            self.app.search_generations.assert_called_once()
        finally:
            # Restore original method
            self.app.search_generations = original_search_generations

    @patch('tkinter.messagebox.askyesno')
    def test_clear_all_generations(self, mock_askyesno):
        """Test clearing all generations."""
        # Configure mock
        mock_askyesno.return_value = True
        
        # Set up generation listbox
        self.app.generation_listbox = MagicMock()
        
        # Mock the search_generations method to avoid calling it
        original_search_generations = self.app.search_generations
        self.app.search_generations = MagicMock()
        
        try:
            # Call clear_all_generations
            self.app.clear_all_generations()
            
            # Verify db_manager.clear_all_generations was called
            self.app.db_manager.clear_all_generations.assert_called_once()
            
            # Verify search_generations was called to refresh the list
            self.app.search_generations.assert_called_once()
        finally:
            # Restore original method
            self.app.search_generations = original_search_generations

    @patch('PIL.ImageTk.PhotoImage')
    @patch('PIL.Image.open')
    def test_display_image(self, mock_open, mock_photo_image):
        """Test displaying an image in the preview area."""
        # Set up mocks
        mock_open.return_value = self.test_image
        mock_photo_image.return_value = MagicMock()
        
        # Set up preview frame dimensions
        self.app.preview_frame.winfo_width.return_value = 600
        self.app.preview_frame.winfo_height.return_value = 600
        self.app.preview_frame.winfo_children.return_value = []
        
        # Mock the original_image attribute
        self.app.original_image = None
        
        # Mock the preview_label
        self.app.preview_label = MagicMock()
        
        # Set up the test_image size attributes to be integers instead of MagicMocks
        self.test_image.width = 512
        self.test_image.height = 512
        
        # Call display_image
        self.app.display_image(self.image_data)
        
        # Verify that the image was opened
        mock_open.assert_called_once()
        
        # Verify that the original image was stored
        self.assertEqual(self.app.original_image, self.test_image)

if __name__ == '__main__':
    unittest.main() 
