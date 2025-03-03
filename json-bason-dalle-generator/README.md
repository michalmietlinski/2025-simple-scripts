# JSON-BASON: AI Image Generator

A flexible, powerful TypeScript-based tool for generating images using multiple AI image generation services (DALL-E 3, Midjourney, Stable Diffusion) based on JSON configuration files.

## Features

- **JSON Configuration**: Fully commented configuration files with all available options
- **Multi-Provider Support**: Generate images using DALL-E 3, Midjourney, or Stable Diffusion
- **Batch Processing**: Rate limiting, retry mechanisms, and resumable batches
- **Cost Management**: Estimate costs before generation and set hard limits
- **Output Organization**: Structured output directories and comprehensive metadata
- **Extensibility**: Custom post-processing scripts and plugin architecture

## Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/json-bason-dalle-generator.git
cd json-bason-dalle-generator

# Install dependencies
npm install

# Build the project
npm run build

# Link the command globally (optional)
npm link
```

## Quick Start

1. Create a configuration file:

```bash
# Create a new configuration file with examples
json-bason init

# Or specify a custom output path
json-bason init --output my-config.jsonc
```

2. Edit the generated configuration file to customize your prompts and settings.

3. Run the generator:

```bash
# Using environment variables for API key
export OPENAI_API_KEY=your-api-key
json-bason --config config.json

# Or provide the API key directly
json-bason --config config.json --api-key your-openai-api-key
```

## Available Commands

### Generate Images (Default)

```bash
json-bason --config config.json
```

Options:
- `--config, -c <path>`: Path to the configuration file (default: `config.json`)
- `--api-key, -k <key>`: OpenAI API key (overrides environment variable)
- `--output-dir, -o <path>`: Output directory (overrides config file)
- `--dry-run, -d`: Estimate cost without generating images
- `--yes, -y`: Skip confirmation prompts
- `--verbose, -v`: Enable verbose logging

### Initialize Configuration

```bash
json-bason init
```

Options:
- `--output, -o <path>`: Output path for the configuration file (default: `config.jsonc`)
- `--force, -f`: Overwrite existing file if it exists

### Validate Configuration

```bash
json-bason validate config.json
```

Options:
- `--verbose, -v`: Show detailed validation information

### Estimate Cost

```bash
json-bason estimate config.json
```

Options:
- `--api-key, -k <key>`: OpenAI API key (overrides environment variable)
- `--detailed, -d`: Show detailed cost breakdown
- `--output-dir, -o <path>`: Output directory (overrides config file)

## Configuration Reference

See the [Configuration Guide](docs/configuration.md) for a complete reference of all available options.

## Provider Guides

- [DALL-E 3 Guide](docs/providers/dalle3.md)
- [Midjourney Guide](docs/providers/midjourney.md) (Coming soon)
- [Stable Diffusion Guide](docs/providers/stable-diffusion.md) (Coming soon)

## Development

See the [Development Plan](Development_plan.md) for the project roadmap and implementation details.

```bash
# Run tests
npm test

# Run linter
npm run lint

# Run in development mode
npm run dev -- --config your-config.json
```

## License

MIT 
