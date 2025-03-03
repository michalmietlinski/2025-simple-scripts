import fs from 'fs-extra';
import path from 'path';
import chalk from 'chalk';
import ora from 'ora';
import { Command } from 'commander';

// Basic configuration template with comments
const configTemplate = {
  output_directory: './output',
  defaults: {
    model: 'dall-e-3',
    quality: 'standard',
    size: '1024x1024',
    style: 'vivid',
    response_format: 'url',
    n: 1,
    batch: {
      concurrency: 2,
      rate_limit_rpm: 10,
      retries: {
        attempts: 3,
        initial_delay_ms: 1000,
        max_delay_ms: 10000,
        exponential_backoff: true
      }
    },
    output: {
      directory_structure: 'date',
      filename_template: '{prompt_hash}_{timestamp}',
      save_metadata: true,
      deduplicate: true
    }
  },
  post_processing: [
    {
      name: 'resize',
      params: {
        width: 512,
        height: 512,
        fit: 'contain'
      }
    }
  ],
  images: [
    {
      prompt_template: 'A {color} {animal} in a {environment}',
      variables: {
        color: ['red', 'blue', 'green'],
        animal: ['cat', 'dog', 'bird'],
        environment: ['forest', 'desert', 'ocean']
      },
      filename_template: '{color}_{animal}_{environment}'
    }
  ]
};

// Comments for the configuration file
const configComments = {
  output_directory: 'Directory where generated images will be saved',
  defaults: 'Default settings for all image generations',
  'defaults.model': 'AI model to use for generation (dall-e-3, midjourney, stable-diffusion-xl)',
  'defaults.quality': 'Image quality (standard, hd) - DALL-E 3 specific',
  'defaults.size': 'Image size (1024x1024, 1024x1792, 1792x1024) - DALL-E 3 specific',
  'defaults.style': 'Image style (vivid, natural) - DALL-E 3 specific',
  'defaults.response_format': 'Response format (url, b64_json) - DALL-E 3 specific',
  'defaults.n': 'Number of images to generate per prompt - DALL-E 3 specific',
  'defaults.batch': 'Batch processing settings',
  'defaults.batch.concurrency': 'Number of concurrent API requests',
  'defaults.batch.rate_limit_rpm': 'Maximum requests per minute',
  'defaults.batch.retries': 'Settings for retrying failed requests',
  'defaults.batch.retries.attempts': 'Maximum number of retry attempts',
  'defaults.batch.retries.initial_delay_ms': 'Initial delay before first retry (milliseconds)',
  'defaults.batch.retries.max_delay_ms': 'Maximum delay between retries (milliseconds)',
  'defaults.batch.retries.exponential_backoff': 'Whether to use exponential backoff for retries',
  'defaults.output': 'Output settings',
  'defaults.output.directory_structure': 'Directory structure (flat, date, batch, category)',
  'defaults.output.filename_template': 'Template for filenames with variables in {curly_braces}',
  'defaults.output.save_metadata': 'Whether to save metadata JSON files with each image',
  'defaults.output.deduplicate': 'Whether to skip generating duplicate prompts',
  post_processing: 'Post-processing scripts to apply to generated images',
  'post_processing[].name': 'Name of the post-processing script',
  'post_processing[].params': 'Parameters for the post-processing script',
  images: 'List of image generation configurations',
  'images[].prompt_template': 'Template for the prompt with variables in {curly_braces}',
  'images[].variables': 'Variables to substitute in the prompt template',
  'images[].filename_template': 'Template for the filename (overrides default)'
};

/**
 * Adds comments to a JSON object
 * @param obj Object to add comments to
 * @param comments Comments to add
 * @param prefix Prefix for nested properties
 * @returns JSON string with comments
 */
function addCommentsToJson(
  obj: any, 
  comments: Record<string, string>, 
  prefix = ''
): string {
  let result = '{\n';
  const entries = Object.entries(obj);
  
  entries.forEach(([key, value], index) => {
    const fullKey = prefix ? `${prefix}.${key}` : key;
    const comment = comments[fullKey];
    
    if (comment) {
      result += `  // ${comment}\n`;
    }
    
    result += `  "${key}": `;
    
    if (Array.isArray(value)) {
      result += '[\n';
      
      (value as any[]).forEach((item, i) => {
        if (typeof item === 'object' && item !== null) {
          // For arrays of objects, add comments to each object
          const arrayPrefix = `${fullKey}[]`;
          result += addCommentsToJson(item, comments, arrayPrefix).replace(/^/gm, '    ');
        } else {
          result += `    ${JSON.stringify(item)}`;
        }
        
        if (i < value.length - 1) {
          result += ',';
        }
        
        result += '\n';
      });
      
      result += '  ]';
    } else if (typeof value === 'object' && value !== null) {
      // For nested objects, recursively add comments
      result += addCommentsToJson(value, comments, fullKey).replace(/^/gm, '  ');
    } else {
      result += JSON.stringify(value);
    }
    
    if (index < entries.length - 1) {
      result += ',';
    }
    
    result += '\n';
  });
  
  result += '}';
  return result;
}

/**
 * Initializes a new configuration file
 * @param options Command options
 */
export async function initCommand(options: { output?: string, force?: boolean }) {
  const spinner = ora('Creating configuration file').start();
  
  try {
    const outputPath = path.resolve(process.cwd(), options.output || 'config.jsonc');
    
    // Check if file already exists
    if (await fs.pathExists(outputPath) && !options.force) {
      spinner.fail(`Configuration file already exists at ${outputPath}`);
      console.log(chalk.yellow('Use --force to overwrite the existing file'));
      return;
    }
    
    // Create the configuration file with comments
    const configWithComments = addCommentsToJson(configTemplate, configComments);
    await fs.writeFile(outputPath, configWithComments);
    
    // Create a clean JSON version for actual use
    const jsonOutputPath = outputPath.replace(/\.jsonc$/, '.json');
    if (jsonOutputPath !== outputPath) {
      await fs.writeFile(jsonOutputPath, JSON.stringify(configTemplate, null, 2));
      spinner.succeed(`Created configuration files at:\n- ${outputPath} (with comments)\n- ${jsonOutputPath} (clean JSON)`);
    } else {
      spinner.succeed(`Created configuration file at ${outputPath}`);
    }
    
    console.log(chalk.green('\nNext steps:'));
    console.log(`1. Edit ${chalk.cyan(outputPath)} to customize your configuration`);
    console.log(`2. Run ${chalk.cyan('json-bason -c ' + outputPath.replace(/\.jsonc$/, '.json'))} to generate images`);
    
  } catch (error) {
    spinner.fail(`Error creating configuration file: ${error instanceof Error ? error.message : String(error)}`);
    process.exit(1);
  }
}

/**
 * Registers the init command with the CLI
 * @param program Commander program instance
 */
export function registerInitCommand(program: Command) {
  program
    .command('init')
    .description('Create a new configuration file with examples')
    .option('-o, --output <path>', 'Output path for the configuration file', 'config.jsonc')
    .option('-f, --force', 'Overwrite existing file if it exists', false)
    .action(initCommand);
} 
