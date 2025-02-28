"""Settings manager for handling application configuration."""

import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import dataclass, asdict

logger = logging.getLogger(__name__)

@dataclass
class Settings:
    """Application settings model."""
    api_key: str = ""
    default_quality: str = "standard"
    default_style: str = "vivid"
    output_dir: str = "output"
    cleanup_enabled: bool = False
    cleanup_days: int = 30
    remember_window: bool = True
    page_size: int = 20
    window_geometry: Optional[str] = None

class SettingsManager:
    """Manages application settings."""
    
    def __init__(self, config_dir: Path):
        """Initialize settings manager.
        
        Args:
            config_dir: Directory for storing settings
        """
        self.config_dir = config_dir
        self.settings_file = config_dir / "settings.json"
        self.settings = self._load_settings()
        
        logger.info("Settings manager initialized")
    
    def _load_settings(self) -> Settings:
        """Load settings from file.
        
        Returns:
            Settings object with loaded or default values
        """
        try:
            # Ensure config directory exists
            self.config_dir.mkdir(parents=True, exist_ok=True)
            
            # Load settings if file exists
            if self.settings_file.exists():
                data = json.loads(self.settings_file.read_text())
                logger.info("Settings loaded from file")
                return Settings(**data)
            
            # Create default settings
            settings = Settings()
            self._save_settings(settings)
            logger.info("Created default settings")
            return settings
            
        except Exception as e:
            logger.error(f"Failed to load settings: {str(e)}")
            return Settings()
    
    def _save_settings(self, settings: Settings):
        """Save settings to file.
        
        Args:
            settings: Settings to save
        """
        try:
            # Convert to dict and save
            data = asdict(settings)
            self.settings_file.write_text(
                json.dumps(data, indent=4)
            )
            logger.info("Settings saved to file")
            
        except Exception as e:
            logger.error(f"Failed to save settings: {str(e)}")
            raise
    
    def get_settings(self) -> Dict[str, Any]:
        """Get current settings.
        
        Returns:
            Dictionary of current settings
        """
        return asdict(self.settings)
    
    def update_settings(self, new_settings: Dict[str, Any]):
        """Update settings with new values.
        
        Args:
            new_settings: Dictionary of new settings
        """
        try:
            # Update settings object
            for key, value in new_settings.items():
                if hasattr(self.settings, key):
                    setattr(self.settings, key, value)
            
            # Save to file
            self._save_settings(self.settings)
            logger.info("Settings updated")
            
        except Exception as e:
            logger.error(f"Failed to update settings: {str(e)}")
            raise
    
    def get_api_key(self) -> str:
        """Get API key from settings.
        
        Returns:
            str: API key or empty string
        """
        return self.settings.api_key
    
    def set_api_key(self, api_key: str):
        """Set API key in settings.
        
        Args:
            api_key: New API key
        """
        try:
            self.settings.api_key = api_key
            self._save_settings(self.settings)
            logger.info("API key updated")
        except Exception as e:
            logger.error(f"Failed to update API key: {str(e)}")
            raise
    
    def get_output_dir(self) -> Path:
        """Get output directory from settings.
        
        Returns:
            Path: Output directory path
        """
        return Path(self.settings.output_dir)
    
    def set_window_geometry(self, geometry: str):
        """Save window geometry.
        
        Args:
            geometry: Window geometry string
        """
        if self.settings.remember_window:
            try:
                self.settings.window_geometry = geometry
                self._save_settings(self.settings)
                logger.debug("Window geometry saved")
            except Exception as e:
                logger.error(f"Failed to save window geometry: {str(e)}")
    
    def get_window_geometry(self) -> Optional[str]:
        """Get saved window geometry.
        
        Returns:
            Optional[str]: Window geometry string if available
        """
        if self.settings.remember_window:
            return self.settings.window_geometry
        return None 
