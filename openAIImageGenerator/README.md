# DALL-E Image Generator

A desktop application for generating images using OpenAI's DALL-E models with advanced prompt management, history tracking, and usage statistics.

## Project Overview

This application provides a user-friendly interface for generating images using OpenAI's DALL-E models. It includes features for managing prompts, tracking generation history, and monitoring API usage.

## Key Features

- **Image Generation**: Generate images using DALL-E 3 and DALL-E 2 models
- **Customization Options**: Select size, quality, and style parameters
- **Prompt Management**: Save, search, and reuse prompts
- **History Tracking**: View and manage generation history
- **Database Storage**: Store prompts, generations, and usage statistics
- **Usage Monitoring**: Track token usage and associated costs
- **Full Resolution Viewing**: Examine generated images in their original resolution
- **Output Directory Access**: Easily access saved images

## Project Structure

The project is organized into the following directories:

- `utils/`: Utility modules for various functionalities
- `outputs/`: Directory for storing generated images
- `data/`: Database and configuration files
- `verification/`: Scripts for verifying implementation phases
- `readmes/`: Detailed documentation for each phase
- `tests/`: Test files for various components of the application

## Implementation Phases

The project has been implemented in phases, each building upon the previous:

1. **[Phase 1: Project Setup](readmes/README_PHASE1.md)** - Basic application structure, configuration management, and utility modules
2. **[Phase 2: OpenAI Integration](readmes/README_PHASE2.md)** - Integration with OpenAI API and image generation functionality
3. **[Phase 3: Database Implementation](readmes/README_PHASE3.md)** - Database for storing prompts, generations, and usage statistics
4. **[Phase 4: GUI Implementation](readmes/README_PHASE4.md)** - Comprehensive graphical user interface with advanced viewing options

## Getting Started

### Prerequisites

- Python 3.8 or higher
- OpenAI API key
- Required Python packages (see requirements.txt)

### Installation

1. Clone the repository
2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
3. Set up your OpenAI API key in the application or as an environment variable

### Running the Application

```
python app.py
```

## Testing

The application includes a comprehensive test suite in the `tests/` directory. To run all tests:

```
cd tests
python run_tests.py
```

## Verification

Each phase includes verification scripts to ensure proper implementation:

```
python -m verification.verify_phase1
python -m verification.verify_phase2
python -m verification.verify_phase3
```

## License

This project is licensed under the MIT License - see the LICENSE file for details. 
