# DALL-E 3 Provider Guide

DALL-E 3 is OpenAI's most advanced image generation model, capable of creating highly detailed and accurate images based on text prompts.

## Setup

To use the DALL-E 3 provider, you need an OpenAI API key. You can get one by signing up at [OpenAI's website](https://platform.openai.com/).

Once you have an API key, you can provide it in one of two ways:

1. Set the `OPENAI_API_KEY` environment variable:
   ```bash
   export OPENAI_API_KEY=your-api-key
   ```

2. Pass it directly to the CLI:
   ```bash
   npm run generate -- --config your-config.json --api-key your-api-key
   ```

## Configuration Options

DALL-E 3 supports the following configuration options:

| Option | Description | Values | Default |
|--------|-------------|--------|---------|
| `quality` | Image quality | `standard`, `hd` | `standard` |
| `size` | Image size | `1024x1024`, `1024x1792`, `1792x1024` | `1024x1024` |
| `style` | Image style | `vivid`, `natural` | `vivid` |
| `response_format` | Response format | `url`, `b64_json` | `url` |
| `n` | Number of images to generate per prompt | 1-10 | 1 |
| `user` | User identifier for OpenAI usage tracking | string | none |

## Example Configuration

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

## Pricing

DALL-E 3 pricing varies based on the quality and size of the generated images:

| Quality | Size | Price per image |
|---------|------|-----------------|
| Standard | 1024x1024 | $0.04 |
| Standard | 1024x1792 or 1792x1024 | $0.08 |
| HD | 1024x1024 | $0.08 |
| HD | 1024x1792 or 1792x1024 | $0.12 |

Prices are in USD and are subject to change. Check [OpenAI's pricing page](https://openai.com/pricing) for the most up-to-date information.

## Best Practices

### Prompt Engineering

DALL-E 3 works best with detailed, descriptive prompts. Here are some tips:

1. **Be specific**: Include details about style, lighting, composition, and mood.
2. **Use adjectives**: Descriptive adjectives help create more nuanced images.
3. **Specify medium**: Mention if you want a photo, painting, sketch, etc.
4. **Reference artists or styles**: Mentioning specific artists or art styles can help guide the output.

### Rate Limiting

OpenAI has rate limits on their API. To avoid hitting these limits:

1. Set a reasonable `rate_limit_rpm` value (50 is a good starting point).
2. Use the `concurrency` setting to control how many requests are made simultaneously.
3. Enable retries with exponential backoff to handle rate limit errors gracefully.

### Cost Management

To manage costs:

1. Start with `standard` quality and only use `hd` when necessary.
2. Use the `--dry-run` option to estimate costs before generating images.
3. Set a reasonable batch size to avoid unexpected large charges.

## Troubleshooting

### Common Errors

1. **API Key Invalid**: Ensure your API key is correct and has permissions for DALL-E.
2. **Rate Limit Exceeded**: Reduce your `rate_limit_rpm` and `concurrency` settings.
3. **Content Policy Violation**: DALL-E has content filters that may reject certain prompts.
4. **Timeout Errors**: These can occur during high API load. The retry mechanism should handle these automatically.

### Getting Help

If you encounter issues:

1. Check the OpenAI [documentation](https://platform.openai.com/docs/guides/images).
2. Visit the OpenAI [community forum](https://community.openai.com/).
3. Contact OpenAI support if you have a paid account. 
