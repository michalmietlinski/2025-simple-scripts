import fs from 'fs-extra';
import path from 'path';
import pLimit from 'p-limit';
import pRetry from 'p-retry';
import { 
  GenerationTask, 
  GenerationResult, 
  ProgressState, 
  Provider,
  BatchConfig
} from '../types';

/**
 * Batch processor for image generation tasks
 */
export class BatchProcessor {
  private tasks: GenerationTask[];
  private provider: Provider;
  private batchConfig: BatchConfig;
  private progressState: ProgressState;
  private statePath: string;
  private aborted: boolean = false;
  
  /**
   * Creates a new batch processor
   * @param tasks Array of generation tasks
   * @param provider Provider to use for generation
   * @param batchConfig Batch processing configuration
   * @param statePath Path to save state for resumable batches
   */
  constructor(
    tasks: GenerationTask[], 
    provider: Provider, 
    batchConfig: BatchConfig,
    statePath?: string
  ) {
    this.tasks = tasks;
    this.provider = provider;
    this.batchConfig = batchConfig;
    this.statePath = statePath || path.join(process.cwd(), '.batch-state.json');
    
    // Calculate total images based on n parameter
    const totalImages = tasks.reduce((sum, task) => {
      // Get the number of variations per prompt
      const n = task.options.n || 1;
      return sum + n;
    }, 0);
    
    // Initialize progress state
    this.progressState = {
      total_tasks: tasks.length,
      total_images: totalImages,
      completed_tasks: 0,
      completed_images: 0,
      failed_tasks: 0,
      in_progress_tasks: 0,
      remaining_tasks: tasks.length,
      start_time: new Date(),
      completed_results: [],
      failed_results: [],
      pending_tasks: [...tasks]
    };
  }
  
  /**
   * Processes all tasks in the batch
   * @param onProgress Callback for progress updates
   * @returns Array of generation results
   */
  async process(onProgress?: (state: ProgressState) => void): Promise<GenerationResult[]> {
    // Try to load existing state if available
    if (this.statePath) {
      await this.loadState();
    }
    
    // Create a concurrency limiter
    const limit = pLimit(this.batchConfig.concurrency);
    
    // Create a rate limiter if needed
    const rateLimitDelay = this.batchConfig.rate_limit_rpm > 0 
      ? Math.ceil(60000 / this.batchConfig.rate_limit_rpm) 
      : 0;
    
    // Process tasks with concurrency limit
    const pendingPromises = this.progressState.pending_tasks.map(task => 
      limit(() => this.processTask(task, rateLimitDelay))
    );
    
    // Update progress periodically
    const progressInterval = setInterval(() => {
      if (onProgress) {
        onProgress(this.progressState);
      }
      this.saveState();
    }, 1000);
    
    try {
      // Wait for all tasks to complete
      const results = await Promise.all(pendingPromises);
      
      // Final progress update
      if (onProgress) {
        onProgress(this.progressState);
      }
      
      // Save final state
      await this.saveState();
      
      // Return all results
      return [
        ...this.progressState.completed_results,
        ...this.progressState.failed_results
      ];
    } finally {
      clearInterval(progressInterval);
    }
  }
  
  /**
   * Aborts the batch processing
   */
  abort(): void {
    this.aborted = true;
  }
  
  /**
   * Processes a single task with retries
   * @param task Generation task
   * @param rateLimitDelay Delay between requests for rate limiting
   * @returns Generation result
   */
  private async processTask(task: GenerationTask, rateLimitDelay: number): Promise<GenerationResult> {
    // Update progress state
    this.progressState.in_progress_tasks++;
    this.progressState.remaining_tasks--;
    
    try {
      // Process the task with retries
      const result = await pRetry(
        async () => {
          // Check if aborted
          if (this.aborted) {
            throw new pRetry.AbortError('Batch processing aborted');
          }
          
          // Apply rate limiting
          if (rateLimitDelay > 0) {
            await new Promise(resolve => setTimeout(resolve, rateLimitDelay));
          }
          
          // Generate the image
          const result = await this.provider.generateImage(task);
          
          // If failed, throw an error to trigger retry
          if (!result.success) {
            throw new Error(result.error?.message || 'Unknown error');
          }
          
          return result;
        },
        {
          retries: this.batchConfig.retries.attempts,
          factor: this.batchConfig.retries.exponential_backoff ? 2 : 1,
          minTimeout: this.batchConfig.retries.initial_delay_ms,
          maxTimeout: this.batchConfig.retries.max_delay_ms,
          onFailedAttempt: error => {
            // Log retry information
            console.warn(
              `Task failed (attempt ${error.attemptNumber}/${this.batchConfig.retries.attempts + 1}): ${error.message}`
            );
          }
        }
      );
      
      // Update progress state
      this.progressState.completed_tasks++;
      // Update completed images count based on the number of images generated
      this.progressState.completed_images += (result.image_paths?.length || (result.image_path ? 1 : 0));
      this.progressState.in_progress_tasks--;
      this.progressState.completed_results.push(result);
      
      return result;
    } catch (error) {
      // Create a failed result
      const failedResult: GenerationResult = {
        task,
        success: false,
        error: error instanceof Error ? error : new Error(String(error)),
        timestamp: new Date()
      };
      
      // Update progress state
      this.progressState.failed_tasks++;
      this.progressState.in_progress_tasks--;
      this.progressState.failed_results.push(failedResult);
      
      return failedResult;
    }
  }
  
  /**
   * Saves the current state for resumable batches
   */
  private async saveState(): Promise<void> {
    try {
      await fs.writeJson(this.statePath, this.progressState, { spaces: 2 });
    } catch (error) {
      console.error('Failed to save batch state:', error);
    }
  }
  
  /**
   * Loads the state for resumable batches
   */
  private async loadState(): Promise<void> {
    try {
      // Check if state file exists
      if (await fs.pathExists(this.statePath)) {
        // Load the state
        const savedState = await fs.readJson(this.statePath) as ProgressState;
        
        // Validate the state
        if (
          savedState &&
          savedState.total_tasks === this.progressState.total_tasks &&
          savedState.pending_tasks &&
          savedState.completed_results &&
          savedState.failed_results
        ) {
          // Get current date for directory structure
          const now = new Date();
          
          // Update pending tasks with fresh date information
          savedState.pending_tasks = savedState.pending_tasks.map(task => {
            // If using date directory structure, update the directory path
            if (task.output.directory.includes('/')) {
              const parts = task.output.directory.split('/');
              // If we have at least 3 parts (year/month/day)
              if (parts.length >= 4) {
                // Replace the date parts with current date
                const year = now.getFullYear().toString();
                const month = (now.getMonth() + 1).toString().padStart(2, '0');
                const day = now.getDate().toString().padStart(2, '0');
                
                // Update the directory path with current date
                parts[parts.length - 4] = year;
                parts[parts.length - 3] = month;
                parts[parts.length - 2] = day;
                
                task.output.directory = parts.join('/');
              }
            }
            return task;
          });
          
          // Restore the state with updated tasks
          this.progressState = {
            ...savedState,
            // Ensure dates are Date objects
            start_time: now, // Use current time as start time
            estimated_completion_time: savedState.estimated_completion_time 
              ? new Date(savedState.estimated_completion_time) 
              : undefined,
            // Ensure timestamps are Date objects
            completed_results: savedState.completed_results.map(result => ({
              ...result,
              timestamp: new Date(result.timestamp)
            })),
            failed_results: savedState.failed_results.map(result => ({
              ...result,
              timestamp: new Date(result.timestamp)
            }))
          };
          
          console.log(`Resuming batch with ${this.progressState.pending_tasks.length} remaining tasks`);
        }
      }
    } catch (error) {
      console.error('Failed to load batch state:', error);
    }
  }
  
  /**
   * Calculates the estimated completion time
   * @returns Estimated completion time
   */
  calculateEstimatedCompletionTime(): Date | undefined {
    const { completed_tasks, total_tasks, start_time } = this.progressState;
    
    // If no tasks completed yet, can't estimate
    if (completed_tasks === 0) {
      return undefined;
    }
    
    // Calculate elapsed time
    const elapsedMs = Date.now() - start_time.getTime();
    
    // Calculate time per task
    const msPerTask = elapsedMs / completed_tasks;
    
    // Calculate remaining time
    const remainingTasks = total_tasks - completed_tasks;
    const remainingMs = msPerTask * remainingTasks;
    
    // Calculate estimated completion time
    return new Date(Date.now() + remainingMs);
  }
  
  /**
   * Gets the total number of images to be generated
   * @returns Total number of images
   */
  getTotalImages(): number {
    return this.progressState.total_images;
  }
} 
