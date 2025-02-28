"""Error handling utilities for the application."""

import logging
import traceback
from typing import Optional, Type, Dict, Any
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
import json

logger = logging.getLogger(__name__)

@dataclass
class ErrorReport:
    """Model for error reports."""
    timestamp: str
    error_type: str
    message: str
    traceback: str
    context: Dict[str, Any]

class AppError(Exception):
    """Base class for application errors."""
    def __init__(self, message: str, context: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.context = context or {}
        self.timestamp = datetime.now().isoformat()

class APIError(AppError):
    """Errors related to API operations."""
    pass

class DatabaseError(AppError):
    """Errors related to database operations."""
    pass

class FileError(AppError):
    """Errors related to file operations."""
    pass

class ValidationError(AppError):
    """Errors related to data validation."""
    pass

class ConfigError(AppError):
    """Errors related to configuration."""
    pass

class ErrorHandler:
    """Handles application errors and error reporting."""
    
    def __init__(self, error_dir: Path):
        """Initialize error handler.
        
        Args:
            error_dir: Directory for error reports
        """
        self.error_dir = error_dir
        self.error_dir.mkdir(parents=True, exist_ok=True)
        logger.info("Error handler initialized")
    
    def handle_error(
        self,
        error: Exception,
        context: Optional[Dict[str, Any]] = None,
        show_dialog: bool = True
    ) -> Optional[ErrorReport]:
        """Handle an error and optionally show dialog.
        
        Args:
            error: Exception to handle
            context: Additional context information
            show_dialog: Whether to show error dialog
            
        Returns:
            Optional[ErrorReport]: Error report if created
        """
        try:
            # Create error report
            report = self._create_error_report(error, context)
            
            # Save report
            self._save_error_report(report)
            
            # Log error
            logger.error(
                f"Error occurred: {report.error_type} - {report.message}",
                extra={"error_context": report.context}
            )
            
            # Show dialog if requested
            if show_dialog:
                # Import here to avoid circular imports
                from ..ui.dialogs.error_dialog import ErrorDialog
                
                # Get root window
                root = self._get_root_window()
                if root:
                    # Show error dialog
                    ErrorDialog(
                        root,
                        error,
                        self,
                        title=f"Error: {report.error_type}"
                    )
            
            return report
            
        except Exception as e:
            logger.error(f"Error handler failed: {str(e)}")
            return None
    
    def _create_error_report(
        self,
        error: Exception,
        context: Optional[Dict[str, Any]] = None
    ) -> ErrorReport:
        """Create error report from exception.
        
        Args:
            error: Exception to report
            context: Additional context information
            
        Returns:
            ErrorReport: Created report
        """
        # Get error details
        error_type = error.__class__.__name__
        message = str(error)
        tb = "".join(traceback.format_exception(
            type(error),
            error,
            error.__traceback__
        ))
        
        # Combine context
        full_context = {
            "error_type": error_type,
            "timestamp": datetime.now().isoformat()
        }
        
        if isinstance(error, AppError):
            full_context.update(error.context)
        
        if context:
            full_context.update(context)
        
        return ErrorReport(
            timestamp=datetime.now().isoformat(),
            error_type=error_type,
            message=message,
            traceback=tb,
            context=full_context
        )
    
    def _save_error_report(self, report: ErrorReport):
        """Save error report to file.
        
        Args:
            report: Error report to save
        """
        try:
            # Create filename with timestamp
            timestamp = datetime.fromisoformat(report.timestamp)
            filename = f"error_{timestamp.strftime('%Y%m%d_%H%M%S')}.json"
            
            # Save report
            report_path = self.error_dir / filename
            report_path.write_text(json.dumps({
                "timestamp": report.timestamp,
                "error_type": report.error_type,
                "message": report.message,
                "traceback": report.traceback,
                "context": report.context
            }, indent=4))
            
            logger.debug(f"Error report saved: {report_path}")
            
        except Exception as e:
            logger.error(f"Failed to save error report: {str(e)}")
    
    def get_error_message(
        self,
        error: Exception,
        user_friendly: bool = True
    ) -> str:
        """Get user-friendly error message.
        
        Args:
            error: Exception to get message for
            user_friendly: Whether to return user-friendly message
            
        Returns:
            str: Error message
        """
        if not user_friendly:
            return str(error)
        
        # Map error types to user-friendly messages
        messages = {
            APIError: "There was a problem connecting to the API. Please check your internet connection and API key.",
            DatabaseError: "There was a problem with the database. Please try restarting the application.",
            FileError: "There was a problem accessing files. Please check your permissions and disk space.",
            ValidationError: "The provided data is invalid. Please check your input and try again.",
            ConfigError: "There was a problem with the application settings. Please check your configuration."
        }
        
        # Get message for error type
        for error_type, message in messages.items():
            if isinstance(error, error_type):
                return message
        
        # Default message
        return "An unexpected error occurred. Please try again or check the logs for details."
    
    def cleanup_old_reports(self, days: int = 30):
        """Clean up old error reports.
        
        Args:
            days: Number of days to keep reports
        """
        try:
            cutoff = datetime.now().timestamp() - (days * 24 * 60 * 60)
            
            for report_file in self.error_dir.glob("error_*.json"):
                if report_file.stat().st_mtime < cutoff:
                    report_file.unlink()
                    logger.debug(f"Removed old error report: {report_file}")
                    
        except Exception as e:
            logger.error(f"Failed to cleanup error reports: {str(e)}")

    def _get_root_window(self):
        """Get the root Tkinter window if available."""
        try:
            import tkinter as tk
            
            # Try to get existing root window
            for widget in tk._default_root.winfo_children():
                if widget.winfo_toplevel() == widget:
                    return widget
            
            return tk._default_root
        except (ImportError, AttributeError):
            return None

def handle_errors(show_dialog: bool = True):
    """Decorator for error handling.
    
    Args:
        show_dialog: Whether to show error dialog
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                # Get error handler instance
                error_handler = None
                for arg in args:
                    if hasattr(arg, "error_handler"):
                        error_handler = arg.error_handler
                        break
                
                if error_handler:
                    error_handler.handle_error(e, show_dialog=show_dialog)
                else:
                    logger.error(f"Unhandled error in {func.__name__}: {str(e)}")
                raise
        return wrapper
    return decorator 
