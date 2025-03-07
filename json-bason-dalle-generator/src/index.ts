#!/usr/bin/env node

import path from 'path';
import fs from 'fs-extra';
import { Command } from 'commander';
import chalk from 'chalk';
import ora, { Ora } from 'ora';
import dotenv from 'dotenv';

// Load environment variables
dotenv.config();

// Import components
import { parseConfig } from './config/parser';
import { expandPromptTemplate } from './template/engine';
import { DallE3Provider } from './providers/dalle3';
import { BatchProcessor } from './batch/processor';
import { OutputManager } from './output/manager';
import { CostEstimator } from './cost/estimator';
import { ProgressState } from './types';
import { registerCommands } from './commands';
import { getKey } from './commands/keys';

// Define the program version
const packageJson = require('../package.json');
const version = packageJson.version;

// Create the command line interface
const program = new Command();

program
  .name('json-bason')
  .description('JSON-based AI image generator')
  .version(version)
  .option('-c, --config <path>', 'Path to the configuration file', 'config.json')
  .option('-o, --output-dir <path>', 'Output directory (overrides config file)')
  .option('-d, --dry-run', 'Estimate cost without generating images', false)
  .option('-y, --yes', 'Skip confirmation prompts', false)
  .option('-v, --verbose', 'Enable verbose logging', false);

// Register all commands
registerCommands(program);

// Default command (generate images)
program.action(async (options) => {
  await generateImages(options);
});

// Parse command line arguments
program.parse(process.argv);

// Main function for generating images
async function generateImages(options: any) {
  // Create a spinner instance
  let spinner: Ora | null = null;
  
  try {
    // Parse the configuration file
    spinner = ora('Parsing configuration file').start();
    const configPath = path.resolve(process.cwd(), options.config);
    const config = await parseConfig(configPath);
    spinner.succeed('Configuration file parsed successfully');
    
    // Override output directory if specified
    if (options.outputDir) {
      config.output_directory = options.outputDir;
    }
    
    // Ensure the output directory exists
    const outputDir = path.resolve(path.dirname(configPath), config.output_directory);
    await fs.ensureDir(outputDir);
    
    // Get the API key from stored keys or environment variable
    const apiKey = await getKey('openai') || process.env.OPENAI_API_KEY;
    if (!apiKey) {
      throw new Error(
        'OpenAI API key not found. Please set it using one of these methods:\n' +
        `1. Run ${chalk.cyan('json-bason keys set openai <your-key>')}\n` +
        '2. Set the OPENAI_API_KEY environment variable'
      );
    }
    
    // Create providers
    const providers: Record<string, any> = {
      'dall-e-3': new DallE3Provider(apiKey)
      // Add more providers here
    };
    
    // Create the output manager
    const outputManager = new OutputManager(outputDir, config.defaults.output);
    
    // Expand all prompt templates
    spinner = ora('Expanding prompt templates').start();
    const expandedPrompts = config.images.flatMap(imageConfig => expandPromptTemplate(imageConfig));
    spinner.succeed(`Expanded ${expandedPrompts.length} prompts from ${config.images.length} templates`);
    
    // Create generation tasks
    spinner = ora('Creating generation tasks').start();
    const tasks = expandedPrompts.map(expandedPrompt => {
      // Get the provider options
      const options = {
        model: expandedPrompt.original_config.model || config.defaults.model,
        quality: expandedPrompt.original_config.quality || config.defaults.quality,
        size: expandedPrompt.original_config.size || config.defaults.size,
        style: expandedPrompt.original_config.style || config.defaults.style,
        response_format: expandedPrompt.original_config.response_format || config.defaults.response_format,
        n: expandedPrompt.original_config.n || config.defaults.n,
        user: expandedPrompt.original_config.user || config.defaults.user
      };
      
      // Create the task
      return outputManager.createTask(
        expandedPrompt.prompt,
        expandedPrompt.variables,
        expandedPrompt.original_config,
        options
      );
    });
    spinner.succeed(`Created ${tasks.length} generation tasks`);
    
    // Ensure output directories exist
    spinner = ora('Ensuring output directories exist').start();
    await outputManager.ensureDirectories(tasks);
    spinner.succeed('Output directories created');
    
    // Estimate cost
    spinner = ora('Estimating cost').start();
    const costEstimator = new CostEstimator(providers);
    const costEstimates = costEstimator.estimateCost(tasks);
    const { cost: totalCost, currency } = costEstimator.getTotalCost(tasks);
    spinner.succeed(`Estimated cost: ${CostEstimator.formatCost(totalCost, currency)}`);
    
    // Print cost report
    console.log('\n' + costEstimator.createCostReport(tasks));
    
    // If dry run, exit
    if (options.dryRun) {
      console.log(chalk.yellow('Dry run completed. No images were generated.'));
      return;
    }
    
    // Confirm generation
    if (!options.yes) {
      const readline = require('readline').createInterface({
        input: process.stdin,
        output: process.stdout
      });
      
      const answer = await new Promise<string>(resolve => {
        readline.question(
          `Generate ${tasks.length} images for an estimated cost of ${CostEstimator.formatCost(totalCost, currency)}? (y/N) `,
          resolve
        );
      });
      
      readline.close();
      
      if (answer.toLowerCase() !== 'y' && answer.toLowerCase() !== 'yes') {
        console.log(chalk.yellow('Generation cancelled.'));
        return;
      }
    }
    
    // Create the batch processor
    const batchProcessor = new BatchProcessor(
      tasks,
      providers[config.defaults.model],
      config.defaults.batch
    );
    
    // Process the batch
    spinner = ora(`Generating ${tasks.length} images`).start();
    
    // Track progress
    let lastProgress = 0;
    
    const results = await batchProcessor.process(state => {
      // Calculate progress percentage
      const progress = Math.floor((state.completed_tasks / state.total_tasks) * 100);
      
      // Only update if progress has changed
      if (progress !== lastProgress) {
        spinner!.text = `Generating images: ${progress}% (${state.completed_tasks}/${state.total_tasks})`;
        lastProgress = progress;
      }
    });
    
    // Count successes and failures
    const successes = results.filter(result => result.success).length;
    const failures = results.filter(result => !result.success).length;
    
    if (failures === 0) {
      spinner.succeed(`Generated ${successes} images successfully`);
    } else {
      spinner.warn(`Generated ${successes} images, ${failures} failed`);
    }
    
    // Print summary
    console.log('\nGeneration Summary:');
    console.log(`- Total tasks: ${tasks.length}`);
    console.log(`- Successful: ${successes}`);
    console.log(`- Failed: ${failures}`);
    console.log(`- Output directory: ${outputDir}`);
    
    // Print failures if any
    if (failures > 0) {
      console.log('\nFailed tasks:');
      results
        .filter(result => !result.success)
        .forEach((result, index) => {
          console.log(`${index + 1}. Prompt: "${result.task.prompt.substring(0, 50)}..."`);
          console.log(`   Error: ${result.error?.message}`);
        });
    }
    
  } catch (error) {
    // Handle errors
    if (spinner && spinner.isSpinning) {
      spinner.fail(`Error: ${error instanceof Error ? error.message : String(error)}`);
    } else {
      console.error(chalk.red(`Error: ${error instanceof Error ? error.message : String(error)}`));
    }
    
    // Print stack trace in verbose mode
    if (options.verbose && error instanceof Error && error.stack) {
      console.error(chalk.gray(error.stack));
    }
    
    process.exit(1);
  }
} 
