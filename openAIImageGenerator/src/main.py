"""Main entry point for the OpenAI Image Generator application."""

import tkinter as tk
import logging
from pathlib import Path

from .core.openai_client import OpenAIImageClient
from .core.database import DatabaseManager
from .core.file_manager import FileManager
from .utils.settings_manager import SettingsManager
from .utils.error_handler import ErrorHandler
from .ui.main_window import MainWindow

def main():
    """Initialize and run the application."""
    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    logger = logging.getLogger(__name__)
    
    try:
        # Initialize root window
        root = tk.Tk()
        
        # Set up configuration directories
        config_dir = Path.home() / ".openai_image_generator"
        config_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize managers
        settings_manager = SettingsManager(config_dir)
        error_handler = ErrorHandler(config_dir / "errors")
        
        settings = settings_manager.get_settings()
        db_manager = DatabaseManager(config_dir / "database.sqlite")
        file_manager = FileManager(Path(settings["output_dir"]))
        openai_client = OpenAIImageClient(settings["api_key"])
        
        # Create and run main window
        app = MainWindow(
            root,
            openai_client=openai_client,
            db_manager=db_manager,
            file_manager=file_manager,
            settings_manager=settings_manager,
            error_handler=error_handler
        )
        app.run()
        
    except Exception as e:
        logger.error(f"Application failed to start: {str(e)}")
        raise

if __name__ == "__main__":
    main() 
