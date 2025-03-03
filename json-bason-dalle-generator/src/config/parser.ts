import fs from 'fs-extra';
import path from 'path';
import Joi from 'joi';
import { Config, ImageGenerationConfig } from '../types';

/**
 * Configuration validation schema using Joi
 */
const configSchema = Joi.object({
  output_directory: Joi.string().required(),
  defaults: Joi.object({
    model: Joi.string().valid('dall-e-3', 'midjourney', 'stable-diffusion-xl').required(),
    quality: Joi.string().valid('standard', 'hd'),
    size: Joi.string().valid('1024x1024', '1024x1792', '1792x1024'),
    style: Joi.string().valid('vivid', 'natural'),
    response_format: Joi.string().valid('url', 'b64_json'),
    n: Joi.number().integer().min(1).max(10),
    user: Joi.string(),
    batch: Joi.object({
      concurrency: Joi.number().integer().min(1).required(),
      rate_limit_rpm: Joi.number().integer().min(0).required(),
      retries: Joi.object({
        attempts: Joi.number().integer().min(0).required(),
        initial_delay_ms: Joi.number().integer().min(0).required(),
        max_delay_ms: Joi.number().integer().min(0).required(),
        exponential_backoff: Joi.boolean().required()
      }).required()
    }).required(),
    output: Joi.object({
      directory_structure: Joi.string().valid('flat', 'date', 'batch', 'category').required(),
      filename_template: Joi.string().required(),
      save_metadata: Joi.boolean().required(),
      deduplicate: Joi.boolean().required()
    }).required()
  }).required(),
  post_processing: Joi.array().items(
    Joi.object({
      name: Joi.string().required(),
      params: Joi.object().required()
    })
  ).default([]),
  images: Joi.array().items(
    Joi.object({
      prompt_template: Joi.string().required(),
      variables: Joi.object().pattern(
        Joi.string(),
        Joi.array().items(Joi.string())
      ).required(),
      filename_template: Joi.string(),
      model: Joi.string().valid('dall-e-3', 'midjourney', 'stable-diffusion-xl'),
      quality: Joi.string().valid('standard', 'hd'),
      size: Joi.string().valid('1024x1024', '1024x1792', '1792x1024'),
      style: Joi.string().valid('vivid', 'natural'),
      response_format: Joi.string().valid('url', 'b64_json'),
      n: Joi.number().integer().min(1).max(10),
      user: Joi.string()
    })
  ).min(1).required()
});

/**
 * Parse and validate a configuration file
 * @param configPath Path to the configuration file
 * @returns Validated configuration object
 */
export async function parseConfig(configPath: string): Promise<Config> {
  try {
    // Ensure the file exists
    if (!await fs.pathExists(configPath)) {
      throw new Error(`Configuration file not found: ${configPath}`);
    }

    // Read and parse the JSON file
    const configContent = await fs.readFile(configPath, 'utf8');
    const config = JSON.parse(configContent);

    // Validate the configuration
    const { error, value } = configSchema.validate(config, { 
      abortEarly: false,
      allowUnknown: false
    });

    if (error) {
      const errorDetails = error.details.map(detail => `- ${detail.message}`).join('\n');
      throw new Error(`Configuration validation failed:\n${errorDetails}`);
    }

    // Ensure output directory exists
    const outputDir = path.resolve(path.dirname(configPath), value.output_directory);
    await fs.ensureDir(outputDir);

    return value as Config;
  } catch (error) {
    if (error instanceof SyntaxError) {
      throw new Error(`Invalid JSON in configuration file: ${error.message}`);
    }
    throw error;
  }
}

/**
 * Validate a single image generation configuration
 * @param imageConfig Image generation configuration
 * @returns Validation result
 */
export function validateImageConfig(imageConfig: ImageGenerationConfig): { valid: boolean; errors: string[] } {
  const { error } = configSchema.extract('images.0').validate(imageConfig, { 
    abortEarly: false,
    allowUnknown: false
  });

  if (error) {
    return {
      valid: false,
      errors: error.details.map(detail => detail.message)
    };
  }

  return { valid: true, errors: [] };
} 
