import path from 'path';
import chalk from 'chalk';
import ora from 'ora';
import { Command } from 'commander';
import { parseConfig } from '../config/parser';
import { expandPromptTemplate } from '../template/engine';

/**
 * Validates a configuration file
 * @param configPath Path to the configuration file
 * @param options Command options
 */
export async function validateConfig(configPath: string, options: { verbose?: boolean }) {
  const spinner = ora('Validating configuration file').start();
  
  try {
    // Parse the configuration file
    const config = await parseConfig(configPath);
    spinner.succeed('Configuration file is valid');
    
    // If verbose, print more details
    if (options.verbose) {
      console.log('\nConfiguration details:');
      console.log(`- Output directory: ${config.output_directory}`);
      console.log(`- Default model: ${config.defaults.model}`);
      console.log(`- Number of image templates: ${config.images.length}`);
      
      // Expand templates to count total prompts
      const expandedPrompts = config.images.flatMap(imageConfig => expandPromptTemplate(imageConfig));
      console.log(`- Total prompts after expansion: ${expandedPrompts.length}`);
      
      // Print post-processing scripts
      if (config.post_processing && config.post_processing.length > 0) {
        console.log(`- Post-processing scripts: ${config.post_processing.length}`);
        config.post_processing.forEach((script, index) => {
          console.log(`  ${index + 1}. ${script.name}`);
        });
      } else {
        console.log('- No post-processing scripts configured');
      }
      
      // Print batch settings
      console.log('\nBatch settings:');
      console.log(`- Concurrency: ${config.defaults.batch.concurrency}`);
      console.log(`- Rate limit: ${config.defaults.batch.rate_limit_rpm} requests per minute`);
      console.log(`- Retry attempts: ${config.defaults.batch.retries.attempts}`);
      
      // Print first few prompts as examples
      if (expandedPrompts.length > 0) {
        console.log('\nSample prompts:');
        expandedPrompts.slice(0, 3).forEach((prompt, index) => {
          console.log(`${index + 1}. "${prompt.prompt}"`);
        });
        
        if (expandedPrompts.length > 3) {
          console.log(`... and ${expandedPrompts.length - 3} more`);
        }
      }
    }
    
    return true;
  } catch (error) {
    spinner.fail(`Configuration file is invalid: ${error instanceof Error ? error.message : String(error)}`);
    
    // Print stack trace in verbose mode
    if (options.verbose && error instanceof Error && error.stack) {
      console.error(chalk.gray(error.stack));
    }
    
    return false;
  }
}

/**
 * Validates a configuration file command
 * @param configPath Path to the configuration file
 * @param options Command options
 */
export async function validateCommand(configPath: string, options: { verbose?: boolean }) {
  const resolvedPath = path.resolve(process.cwd(), configPath);
  const success = await validateConfig(resolvedPath, options);
  
  if (!success) {
    process.exit(1);
  }
}

/**
 * Registers the validate command with the CLI
 * @param program Commander program instance
 */
export function registerValidateCommand(program: Command) {
  program
    .command('validate')
    .description('Validate a configuration file')
    .argument('<config-file>', 'Path to the configuration file')
    .option('-v, --verbose', 'Show detailed validation information', false)
    .action(validateCommand);
} 
