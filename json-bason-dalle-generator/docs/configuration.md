# Configuration Guide

JSON-BASON uses JSON configuration files to define how images are generated. This guide explains all available configuration options.

## Basic Structure

A configuration file has the following structure:

```json
{
  "output_directory": "generated_images",
  "defaults": {
    "model": "dall-e-3",
    "quality": "standard",
    "size": "1024x1024",
    "style": "vivid",
    "response_format": "url",
    "n": 1,
    "batch": {
      "concurrency": 2,
      "rate_limit_rpm": 50,
      "retries": {
        "attempts": 3,
        "initial_delay_ms": 1000,
        "max_delay_ms": 10000,
        "exponential_backoff": true
      }
    },
    "output": {
      "directory_structure": "date",
      "filename_template": "{timestamp}_{model}_{prompt_hash}",
      "save_metadata": true,
      "deduplicate": false
    }
  },
  "post_processing": [
    {
      "name": "resize",
      "params": {
        "width": 512,
        "height": 512
      }
    }
  ],
  "images": [
    {
      "prompt_template": "A {adjective} {subject} in {setting}",
      "variables": {
        "adjective": ["beautiful", "mysterious", "serene"],
        "subject": ["landscape", "portrait", "still life"],
        "setting": ["mountains", "urban environment", "underwater scene"]
      },
      "size": "1792x1024",
      "quality": "hd"
    }
  ]
}
```

## Top-Level Options

| Option | Description | Type | Required |
|--------|-------------|------|----------|
| `output_directory` | Directory where generated images will be saved | string | Yes |
| `defaults` | Default options for all images | object | Yes |
| `post_processing` | Post-processing scripts to apply to generated images | array | No |
| `images` | Array of image generation configurations | array | Yes |

## Default Options

The `defaults` object contains default options that apply to all images unless overridden in individual image configurations.

### Model Options

| Option | Description | Type | Values | Default |
|--------|-------------|------|--------|---------|
| `model` | Image generation model to use | string | `dall-e-3`, `midjourney`, `stable-diffusion-xl` | Required |

### DALL-E 3 Options

| Option | Description | Type | Values | Default |
|--------|-------------|------|--------|---------|
| `quality` | Image quality | string | `standard`, `hd` | `standard` |
| `size` | Image size | string | `1024x1024`, `1024x1792`, `1792x1024` | `1024x1024` |
| `style` | Image style | string | `vivid`, `natural` | `vivid` |
| `response_format` | Response format | string | `url`, `b64_json` | `url` |
| `n` | Number of images to generate per prompt | number | 1-10 | 1 |
| `user` | User identifier for OpenAI usage tracking | string | any | none |

### Batch Processing Options

The `batch` object controls how images are generated in batches.

| Option | Description | Type | Default |
|--------|-------------|------|---------|
| `concurrency` | Maximum number of concurrent requests | number | 2 |
| `rate_limit_rpm` | Rate limit in requests per minute (0 for unlimited) | number | 50 |
| `retries` | Retry options for failed requests | object | See below |

#### Retry Options

| Option | Description | Type | Default |
|--------|-------------|------|---------|
| `attempts` | Number of retry attempts | number | 3 |
| `initial_delay_ms` | Initial delay between retries in milliseconds | number | 1000 |
| `max_delay_ms` | Maximum delay between retries in milliseconds | number | 10000 |
| `exponential_backoff` | Whether to use exponential backoff | boolean | true |

### Output Options

The `output` object controls how generated images are saved.

| Option | Description | Type | Values | Default |
|--------|-------------|------|--------|---------|
| `directory_structure` | Directory structure for output | string | `flat`, `date`, `batch`, `category` | `date` |
| `filename_template` | Template for filenames | string | See below | `{timestamp}_{model}_{prompt_hash}` |
| `save_metadata` | Whether to save metadata alongside images | boolean | `true`, `false` | `true` |
| `deduplicate` | Whether to deduplicate similar images | boolean | `true`, `false` | `false` |

#### Directory Structures

- `flat`: All images in the output directory
- `date`: Organized by date (YYYY/MM/DD)
- `batch`: Organized by batch (timestamp)
- `category`: Organized by model and first variable

#### Filename Templates

Filename templates can include variables from the prompt and special variables:

- `{timestamp}`: ISO timestamp (with colons and periods replaced by hyphens)
- `{date}`: Date in YYYY-MM-DD format
- `{time}`: Time in HH-MM-SS format
- `{random}`: Random string
- `{prompt_hash}`: Hash of the prompt
- `{model}`: Model name
- Any variable from the prompt template

## Post-Processing

The `post_processing` array contains scripts to apply to generated images.

### Resize

Resizes images to specified dimensions.

```json
{
  "name": "resize",
  "params": {
    "width": 512,
    "height": 512,
    "fit": "cover",
    "position": "center",
    "quality": 80
  }
}
```

| Option | Description | Type | Values | Default |
|--------|-------------|------|--------|---------|
| `width` | Target width in pixels | number | any | Required |
| `height` | Target height in pixels | number | any | Required |
| `fit` | Resizing method | string | `cover`, `contain`, `fill`, `inside`, `outside` | `cover` |
| `position` | Position for `cover` fit | string | `center`, `top`, `bottom`, `left`, `right`, etc. | `center` |
| `quality` | JPEG quality | number | 1-100 | 80 |

### Watermark

Adds a text or image watermark.

```json
{
  "name": "watermark",
  "params": {
    "text": "© 2023",
    "position": "bottom-right",
    "opacity": 0.5,
    "size": 24,
    "color": "white"
  }
}
```

| Option | Description | Type | Values | Default |
|--------|-------------|------|--------|---------|
| `text` | Watermark text | string | any | Required if no `image` |
| `image` | Path to watermark image | string | any | Required if no `text` |
| `position` | Watermark position | string | `top-left`, `top-right`, `bottom-left`, `bottom-right`, `center` | `bottom-right` |
| `opacity` | Watermark opacity | number | 0-1 | 0.5 |
| `size` | Text size in pixels | number | any | 24 |
| `color` | Text color | string | any CSS color | `white` |

## Image Configurations

The `images` array contains configurations for individual image generation tasks.

| Option | Description | Type | Required |
|--------|-------------|------|----------|
| `prompt_template` | Template for the prompt | string | Yes |
| `variables` | Variables to substitute in the template | object | Yes |
| `filename_template` | Template for the filename | string | No |

Plus any option from the `defaults` section to override for this specific image.

### Prompt Templates

Prompt templates can include variables in curly braces:

```
A {adjective} {subject} in {setting} with {lighting} lighting
```

### Variables

Variables are defined as objects with keys matching the variables in the template and arrays of possible values:

```json
"variables": {
  "adjective": ["beautiful", "mysterious", "serene"],
  "subject": ["landscape", "portrait", "still life"],
  "setting": ["mountains", "urban environment", "underwater scene"],
  "lighting": ["dramatic", "soft", "natural"]
}
```

The generator will create all possible combinations of these variables. In this example, it would generate 3×3×3×3 = 81 images.

## Environment Variables

The following environment variables can be used:

| Variable | Description |
|----------|-------------|
| `OPENAI_API_KEY` | OpenAI API key for DALL-E 3 |
| `MIDJOURNEY_API_KEY` | Midjourney API key |
| `STABILITY_API_KEY` | Stability AI API key for Stable Diffusion |

## Command Line Options

| Option | Description | Default |
|--------|-------------|---------|
| `-c, --config <path>` | Path to the configuration file | `config.json` |
| `-k, --api-key <key>` | OpenAI API key (overrides environment variable) | none |
| `-o, --output-dir <path>` | Output directory (overrides config file) | none |
| `-d, --dry-run` | Estimate cost without generating images | `false` |
| `-y, --yes` | Skip confirmation prompts | `false` |
| `-v, --verbose` | Enable verbose logging | `false` |

## Examples

### Basic Example

```json
{
  "output_directory": "generated_images",
  "defaults": {
    "model": "dall-e-3",
    "quality": "standard",
    "size": "1024x1024",
    "batch": {
      "concurrency": 2,
      "rate_limit_rpm": 50,
      "retries": {
        "attempts": 3,
        "initial_delay_ms": 1000,
        "max_delay_ms": 10000,
        "exponential_backoff": true
      }
    },
    "output": {
      "directory_structure": "flat",
      "filename_template": "{timestamp}_{prompt_hash}",
      "save_metadata": true,
      "deduplicate": false
    }
  },
  "images": [
    {
      "prompt_template": "A photo of a {color} {animal}",
      "variables": {
        "color": ["red", "blue", "green"],
        "animal": ["cat", "dog", "bird"]
      }
    }
  ]
}
```

### Advanced Example

```json
{
  "output_directory": "portfolio",
  "defaults": {
    "model": "dall-e-3",
    "quality": "hd",
    "size": "1792x1024",
    "style": "natural",
    "batch": {
      "concurrency": 1,
      "rate_limit_rpm": 30,
      "retries": {
        "attempts": 5,
        "initial_delay_ms": 2000,
        "max_delay_ms": 30000,
        "exponential_backoff": true
      }
    },
    "output": {
      "directory_structure": "category",
      "filename_template": "{subject}_{style}_{random}",
      "save_metadata": true,
      "deduplicate": true
    }
  },
  "post_processing": [
    {
      "name": "watermark",
      "params": {
        "text": "© AI Portfolio 2023",
        "position": "bottom-right",
        "opacity": 0.3,
        "size": 18,
        "color": "white"
      }
    }
  ],
  "images": [
    {
      "prompt_template": "A professional {style} photograph of a {subject} in {setting}, {lighting} lighting, high detail, 8k",
      "variables": {
        "style": ["portrait", "landscape", "architectural"],
        "subject": ["young woman with blue eyes", "elderly man with weathered face", "modern glass building"],
        "setting": ["studio with neutral background", "golden hour in a forest", "urban cityscape"],
        "lighting": ["soft", "dramatic", "natural"]
      },
      "filename_template": "{style}_{subject}"
    }
  ]
}
``` 
