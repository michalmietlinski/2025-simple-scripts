import { GenerationTask, CostEstimate, Provider } from '../types';

/**
 * Cost estimator for image generation
 */
export class CostEstimator {
  private providers: Record<string, Provider>;
  
  /**
   * Creates a new cost estimator
   * @param providers Object mapping provider names to provider instances
   */
  constructor(providers: Record<string, Provider>) {
    this.providers = providers;
  }
  
  /**
   * Estimates the cost of generating images
   * @param tasks Array of generation tasks
   * @returns Cost estimate
   */
  estimateCost(tasks: GenerationTask[]): CostEstimate[] {
    // Group tasks by provider
    const tasksByProvider: Record<string, GenerationTask[]> = {};
    
    tasks.forEach(task => {
      const providerName = task.options.model;
      if (!tasksByProvider[providerName]) {
        tasksByProvider[providerName] = [];
      }
      tasksByProvider[providerName].push(task);
    });
    
    // Estimate cost for each provider
    const estimates: CostEstimate[] = [];
    
    Object.entries(tasksByProvider).forEach(([providerName, providerTasks]) => {
      const provider = this.providers[providerName];
      
      if (provider) {
        // Get estimate from provider
        const estimate = provider.estimateCost(providerTasks);
        estimates.push(estimate);
      } else {
        // If provider not found, create a placeholder estimate
        estimates.push({
          provider: providerName as any,
          task_count: providerTasks.length,
          estimated_cost: 0,
          currency: 'USD',
          details: { error: 'Provider not available' }
        });
      }
    });
    
    return estimates;
  }
  
  /**
   * Gets the total estimated cost across all providers
   * @param tasks Array of generation tasks
   * @returns Total estimated cost
   */
  getTotalCost(tasks: GenerationTask[]): { cost: number; currency: string } {
    const estimates = this.estimateCost(tasks);
    
    // Sum up costs
    const totalCost = estimates.reduce((sum, estimate) => sum + estimate.estimated_cost, 0);
    
    // Assume all costs are in the same currency (USD)
    return {
      cost: totalCost,
      currency: 'USD'
    };
  }
  
  /**
   * Formats a cost as a string
   * @param cost Cost value
   * @param currency Currency code
   * @returns Formatted cost string
   */
  static formatCost(cost: number, currency: string): string {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency
    }).format(cost);
  }
  
  /**
   * Creates a detailed cost report
   * @param tasks Array of generation tasks
   * @returns Cost report as a string
   */
  createCostReport(tasks: GenerationTask[]): string {
    const estimates = this.estimateCost(tasks);
    const { cost: totalCost, currency } = this.getTotalCost(tasks);
    
    // Create the report
    let report = `Cost Estimate for ${tasks.length} Images\n`;
    report += `=================================\n\n`;
    
    // Add provider-specific costs
    estimates.forEach(estimate => {
      report += `Provider: ${estimate.provider}\n`;
      report += `Tasks: ${estimate.task_count}\n`;
      report += `Cost: ${CostEstimator.formatCost(estimate.estimated_cost, estimate.currency)}\n`;
      
      // Add details if available
      if (estimate.details && typeof estimate.details === 'object') {
        report += `Details:\n`;
        
        Object.entries(estimate.details).forEach(([key, value]) => {
          if (typeof value === 'object') {
            report += `  ${key}:\n`;
            Object.entries(value).forEach(([subKey, subValue]) => {
              report += `    ${subKey}: ${subValue}\n`;
            });
          } else {
            report += `  ${key}: ${value}\n`;
          }
        });
      }
      
      report += `\n`;
    });
    
    // Add total cost
    report += `Total Estimated Cost: ${CostEstimator.formatCost(totalCost, currency)}\n`;
    
    return report;
  }
} 
