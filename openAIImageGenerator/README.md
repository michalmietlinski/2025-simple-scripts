# DALL-E Image Generator

A desktop application for generating images using OpenAI's DALL-E API.

## Features

- Generate images using DALL-E 2 or DALL-E 3
- Customize image size, quality, and style
- Save generated images with prompts
- View generation history
- Manage favorite prompts
- Track usage and costs

## Requirements

- Python 3.8+
- OpenAI API key
- Required Python packages (see requirements.txt)

## Installation

1. Clone the repository
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Create a `.env` file in the project root and add your OpenAI API key:
   ```
   OPENAI_API_KEY=your_api_key_here
   ```

## Usage

Run the application:
```bash
python app.py
```

The application will open with two main tabs:
1. **Generate Images**: Enter prompts and generate images
2. **History**: View past generations and manage prompts

## Configuration

The application creates the following directories:
- `outputs/`: Generated images
- `data/`: SQLite database for history and settings
- `logs/`: Application logs

## License

MIT License 
