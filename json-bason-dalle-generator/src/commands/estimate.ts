import path from 'path';
import chalk from 'chalk';
import ora from 'ora';
import { Command } from 'commander';
import { parseConfig } from '../config/parser';
import { expandPromptTemplate } from '../template/engine';
import { OutputManager } from '../output/manager';
import { CostEstimator } from '../cost/estimator';
import { DallE3Provider } from '../providers/dalle3';

/**
 * Estimates the cost of generating images from a configuration file
 * @param configPath Path to the configuration file
 * @param options Command options
 */
export async function estimateCommand(configPath: string, options: { 
  apiKey?: string, 
  detailed?: boolean,
  outputDir?: string
}) {
  const spinner = ora('Estimating cost').start();
  
  try {
    // Parse the configuration file
    const resolvedPath = path.resolve(process.cwd(), configPath);
    const config = await parseConfig(resolvedPath);
    
    // Override output directory if specified
    if (options.outputDir) {
      config.output_directory = options.outputDir;
    }
    
    // Get the API key (only needed for provider initialization)
    const apiKey = options.apiKey || process.env.OPENAI_API_KEY || 'dummy-key';
    
    // Create providers
    const providers: Record<string, any> = {
      'dall-e-3': new DallE3Provider(apiKey)
      // Add more providers here
    };
    
    // Create the output manager
    const outputDir = path.resolve(path.dirname(resolvedPath), config.output_directory);
    const outputManager = new OutputManager(outputDir, config.defaults.output);
    
    // Expand all prompt templates
    spinner.text = 'Expanding prompt templates';
    const expandedPrompts = config.images.flatMap(imageConfig => expandPromptTemplate(imageConfig));
    
    // Create generation tasks
    spinner.text = 'Creating generation tasks';
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
    
    // Estimate cost
    const costEstimator = new CostEstimator(providers);
    const costEstimates = costEstimator.estimateCost(tasks);
    const { cost: totalCost, currency } = costEstimator.getTotalCost(tasks);
    
    spinner.succeed(`Estimated cost: ${CostEstimator.formatCost(totalCost, currency)}`);
    
    // Print summary
    console.log('\nEstimation Summary:');
    console.log(`- Configuration file: ${configPath}`);
    console.log(`- Number of templates: ${config.images.length}`);
    console.log(`- Total prompts after expansion: ${expandedPrompts.length}`);
    console.log(`- Total estimated cost: ${CostEstimator.formatCost(totalCost, currency)}`);
    
    // Print detailed cost report if requested
    if (options.detailed) {
      console.log('\n' + costEstimator.createCostReport(tasks));
      
      // Print model-specific details
      console.log('\nModel-specific details:');
      costEstimates.forEach(estimate => {
        console.log(`- ${estimate.provider}: ${estimate.task_count} tasks, ${CostEstimator.formatCost(estimate.estimated_cost, estimate.currency)}`);
        
        if (estimate.details) {
          Object.entries(estimate.details).forEach(([key, value]) => {
            console.log(`  - ${key}: ${value}`);
          });
        }
      });
      
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
    
  } catch (error) {
    spinner.fail(`Error estimating cost: ${error instanceof Error ? error.message : String(error)}`);
    process.exit(1);
  }
}

/**
 * Registers the estimate command with the CLI
 * @param program Commander program instance
 */
export function registerEstimateCommand(program: Command) {
  program
    .command('estimate')
    .description('Estimate the cost of generating images from a configuration file')
    .argument('<config-file>', 'Path to the configuration file')
    .option('-k, --api-key <key>', 'OpenAI API key (overrides environment variable)')
    .option('-d, --detailed', 'Show detailed cost breakdown', false)
    .option('-o, --output-dir <path>', 'Output directory (overrides config file)')
    .action(estimateCommand);
} 
