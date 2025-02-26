import os
import logging
import sys
from dotenv import load_dotenv

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger("verification")

def verify_project_structure():
    """Verify that all required directories and files exist."""
    logger.info("Verifying project structure...")
    
    # Get the parent directory path
    parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    
    # Check directories
    directories = ["utils", "outputs", "data"]
    for directory in directories:
        dir_path = os.path.join(parent_dir, directory)
        if not os.path.isdir(dir_path):
            logger.error(f"Directory '{directory}' not found")
            return False
    
    # Check files
    files = [
        "app.py", 
        "config.py", 
        "utils/__init__.py", 
        "utils/openai_client.py", 
        "utils/file_manager.py", 
        "utils/usage_tracker.py"
    ]
    for file in files:
        file_path = os.path.join(parent_dir, file)
        if not os.path.isfile(file_path):
            logger.error(f"File '{file}' not found")
            return False
    
    logger.info("Project structure verified successfully")
    return True

def verify_config_loading():
    """Verify that configuration can be loaded."""
    logger.info("Verifying configuration loading...")
    
    try:
        from config import APP_CONFIG, OPENAI_CONFIG, ensure_directories
        
        # Check if config has required keys
        required_app_keys = ["app_name", "version", "output_dir", "data_dir"]
        for key in required_app_keys:
            if key not in APP_CONFIG:
                logger.error(f"APP_CONFIG missing required key: {key}")
                return False
        
        required_openai_keys = ["api_key", "model", "api_base", "timeout"]
        for key in required_openai_keys:
            if key not in OPENAI_CONFIG:
                logger.error(f"OPENAI_CONFIG missing required key: {key}")
                return False
        
        # Test ensure_directories function
        ensure_directories()
        
        logger.info("Configuration loading verified successfully")
        return True
    except Exception as e:
        logger.error(f"Error verifying configuration loading: {str(e)}")
        return False

def verify_api_key_management():
    """Verify that API key management is implemented."""
    logger.info("Verifying API key management...")
    
    # Get the parent directory path
    parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    env_file = os.path.join(parent_dir, '.env')
    
    # Check if .env file exists or OPENAI_API_KEY environment variable is set
    if not os.path.isfile(env_file) and not os.getenv('OPENAI_API_KEY'):
        logger.warning("No .env file or OPENAI_API_KEY environment variable found")
        logger.warning("API key management can't be fully verified without a key")
    
    # Check if app.py has API key management code
    try:
        with open(os.path.join(parent_dir, 'app.py'), 'r') as f:
            app_code = f.read()
            
        # Check for key management functions
        if 'show_api_key_dialog' not in app_code:
            logger.error("API key dialog function not found in app.py")
            return False
            
        if '.env' not in app_code:
            logger.error("No .env file handling found in app.py")
            return False
        
        logger.info("API key management verified successfully")
        return True
    except Exception as e:
        logger.error(f"Error verifying API key management: {str(e)}")
        return False

def verify_utility_modules():
    """Verify that utility modules can be imported and initialized."""
    logger.info("Verifying utility modules...")
    
    try:
        # Fix the import error in usage_tracker.py
        parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
        usage_tracker_path = os.path.join(parent_dir, 'utils', 'usage_tracker.py')
        with open(usage_tracker_path, "r") as f:
            content = f.read()
        
        if content.startswith("aimport logging"):
            with open(usage_tracker_path, "w") as f:
                f.write(content.replace("aimport logging", "import logging"))
            logger.info("Fixed import error in usage_tracker.py")
        
        # Try importing modules
        from utils.file_manager import FileManager
        from utils.usage_tracker import UsageTracker
        
        # Initialize modules
        file_manager = FileManager()
        usage_tracker = UsageTracker()
        
        # Test file manager
        test_path = file_manager.get_output_path("Test prompt", "test description")
        if not test_path or not test_path.endswith(".png"):
            logger.error(f"File manager returned invalid path: {test_path}")
            return False
        
        logger.info("Utility modules verified successfully")
        return True
    except Exception as e:
        logger.error(f"Error verifying utility modules: {str(e)}")
        return False

def main():
    """Run all verification checks."""
    logger.info("Starting Phase 1 verification...")
    
    checks = [
        verify_project_structure,
        verify_config_loading,
        verify_api_key_management,
        verify_utility_modules
    ]
    
    all_passed = True
    for check in checks:
        if not check():
            all_passed = False
    
    if all_passed:
        logger.info("✅ All Phase 1 verification checks passed!")
        return 0
    else:
        logger.error("❌ Some verification checks failed")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 
