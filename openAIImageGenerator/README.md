# OpenAI Image Generator

A GUI application for generating images using OpenAI's DALL-E models, with prompt management, token usage tracking, and organized image storage.

## Features

- Connect to OpenAI API for DALL-E image generation
- Support for different image sizes and quality settings
- Preview generated images in the application
- Save history of all prompts and generations
- Template system with variable substitution
- Usage tracking and statistics
- Comprehensive error handling
- Organized file management with automatic cleanup

## Project Status

The application has been fully migrated to a new, modular architecture with improved organization and maintainability.

### Completed
- Core functionality (OpenAI client, database, file management)
- UI components (main window, generation tab, history tab)
- Template system
- Usage tracking
- Error handling
- Settings management

### Next Features to Implement
1. **Import/Export Features**
   - Export prompt history to JSON/CSV
   - Import prompts from external sources
   - Batch export of favorite prompts

2. **Batch Operations**
   - Template-based batch generation
   - Rate-limited batch processing
   - Progress tracking for batch operations

3. **Advanced Prompt Management**
   - AI-assisted prompt enhancement
   - Prompt analysis for better results
   - Prompt categorization and tagging system

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/openai-image-generator.git
cd openai-image-generator
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Run the application:
```bash
python -m src.main
```

## Testing

Tests are organized in the `src_tests` directory, matching the structure of the `src` directory:

- **core/**: Tests for core components
- **ui/**: Tests for UI components
- **utils/**: Tests for utility modules

To run tests:

```bash
# Install test dependencies
pip install pytest pytest-mock pytest-cov

# Run all tests with coverage report
pytest src_tests/ --cov=src

# Run specific test categories
pytest src_tests/core/
pytest src_tests/ui/
pytest src_tests/utils/
```

## Project Structure

```
openai-image-generator/
├── src/                    # Source code
│   ├── core/               # Core components
│   │   ├── database.py     # Database management
│   │   ├── data_models.py  # Data models
│   │   ├── file_manager.py # File management
│   │   └── openai_client.py # OpenAI API client
│   ├── ui/                 # UI components
│   │   ├── dialogs/        # Dialog windows
│   │   ├── tabs/           # Tab components
│   │   └── main_window.py  # Main application window
│   ├── utils/              # Utility modules
│   │   ├── error_handler.py # Error handling
│   │   ├── settings_manager.py # Settings management
│   │   ├── template_utils.py # Template processing
│   │   └── usage_tracker.py # Usage tracking
│   └── main.py             # Application entry point
├── src_tests/              # Tests
│   ├── core/               # Core component tests
│   ├── ui/                 # UI component tests
│   └── utils/              # Utility module tests
├── output/                 # Generated images
├── requirements.txt        # Dependencies
└── README.md               # Documentation
```

## License

[MIT License](LICENSE) 
