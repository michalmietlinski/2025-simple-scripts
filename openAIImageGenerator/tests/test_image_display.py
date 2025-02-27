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
        """Set up test environment."""
        # Create a mock root window with tk attribute
        self.root = MagicMock()
        self.root.tk = MagicMock()
        
        # Create a mock preview frame
        self.preview_frame = MagicMock()
        self.preview_frame.winfo_width.return_value = 600
        self.preview_frame.winfo_height.return_value = 600
        self.preview_frame.winfo_children.return_value = []
        
        # Create a test image
        self.test_image = Image.new('RGB', (1024, 768), color='red')
        self.image_bytes = BytesIO()
        self.test_image.save(self.image_bytes, format='PNG')
        self.image_data = self.image_bytes.getvalue()
        
        # Create a mock app with only the methods we need to test
        self.app = MagicMock()
        self.app.preview_frame = self.preview_frame
        self.app.file_manager = MagicMock()
        self.app.file_manager.ensure_directories.return_value = "/mock/output/directory"
        
        # Import the actual methods we want to test
        from app import DALLEGeneratorApp
        self.app.view_original_resolution = DALLEGeneratorApp.view_original_resolution.__get__(self.app)
        self.app.open_output_directory = DALLEGeneratorApp.open_output_directory.__get__(self.app)
        self.app.display_image = DALLEGeneratorApp.display_image.__get__(self.app)
        self.app.save_image = DALLEGeneratorApp.save_image.__get__(self.app)
    
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
    @patch('PIL.Image.open')
    @patch('tkinter.messagebox.showinfo')
    @patch('os.path.exists')
    @patch('os.path.getsize')
    def test_save_image(self, mock_getsize, mock_exists, mock_showinfo, mock_image_open, mock_askstring):
        """Test saving an image without showing any message."""
        # Set up the current image
        self.app.current_image = {
            "data": self.image_data,
            "prompt": "Test prompt"
        }
        
        # Configure mocks
        mock_exists.return_value = True
        mock_getsize.return_value = 1024  # Mock file size
        mock_image_open.return_value = self.test_image
        mock_askstring.return_value = "Test description"
        self.app.file_manager.save_image.return_value = "/mock/output/directory/test_image.png"
        
        # Call the method
        self.app.save_image()
        
        # Verify the file manager was called to save the image
        self.app.file_manager.save_image.assert_called_once()
        
        # Verify no success message was shown (since we removed it)
        mock_showinfo.assert_not_called()
    
    @patch('PIL.Image.open')
    @patch('tkinter.Frame')
    @patch('tkinter.Label')
    @patch('tkinter.Button')
    @patch('PIL.ImageTk.PhotoImage')
    def test_display_image(self, mock_photo_image, mock_button, mock_label, mock_frame, mock_image_open):
        """Test displaying an image in the preview area."""
        # Configure mock to return our test image
        mock_image_open.return_value = self.test_image
        
        # Call the method
        self.app.display_image(self.image_data)
        
        # Verify image was opened
        mock_image_open.assert_called_once()
        
        # Verify original image was stored
        self.assertEqual(self.app.original_image, self.test_image)
        
        # Verify children were cleared from preview frame
        self.preview_frame.winfo_children.assert_called_once()

if __name__ == '__main__':
    unittest.main() 
