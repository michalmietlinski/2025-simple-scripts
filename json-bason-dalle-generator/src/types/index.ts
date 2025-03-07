/**
 * Core types for the JSON-BASON image generator
 */

// Supported image generation models
export type ImageModel = 'dall-e-3' | 'midjourney' | 'stable-diffusion-xl';

// DALL-E 3 specific options
export type DallE3Quality = 'standard' | 'hd';
export type DallE3Size = '1024x1024' | '1024x1792' | '1792x1024';
export type DallE3Style = 'vivid' | 'natural';
export type DallE3ResponseFormat = 'url' | 'b64_json';

// Directory structure options
export type DirectoryStructure = 'flat' | 'date' | 'batch' | 'category';

// Retry configuration
export interface RetryConfig {
  attempts: number;
  initial_delay_ms: number;
  max_delay_ms: number;
  exponential_backoff: boolean;
}

// Batch processing configuration
export interface BatchConfig {
  concurrency: number;
  rate_limit_rpm: number;
  retries: RetryConfig;
}

// Output configuration
export interface OutputConfig {
  directory_structure: DirectoryStructure;
  filename_template: string;
  save_metadata: boolean;
  deduplicate: boolean;
}

// Post-processing script configuration
export interface PostProcessingScript {
  name: string;
  params: Record<string, any>;
}

// Provider-specific options
export interface ProviderOptions {
  // DALL-E 3 specific options
  quality?: DallE3Quality;
  size?: DallE3Size;
  style?: DallE3Style;
  response_format?: DallE3ResponseFormat;
  n?: number;
  user?: string;
  
  // Midjourney specific options (to be expanded)
  
  // Stable Diffusion specific options (to be expanded)
}

// Image generation configuration
export interface ImageGenerationConfig {
  prompt_template: string;
  variables: Record<string, string[]>;
  filename_template?: string;
  
  // Provider options (can override defaults)
  model?: ImageModel;
  
  // Provider-specific options
  quality?: DallE3Quality;
  size?: DallE3Size;
  style?: DallE3Style;
  response_format?: DallE3ResponseFormat;
  n?: number;
  user?: string;
}

// Main configuration
export interface Config {
  output_directory: string;
  defaults: {
    model: ImageModel;
    batch: BatchConfig;
    output: OutputConfig;
  } & ProviderOptions;
  post_processing: PostProcessingScript[];
  images: ImageGenerationConfig[];
}

// Expanded prompt with all variables substituted
export interface ExpandedPrompt {
  prompt: string;
  variables: Record<string, string>;
  original_config: ImageGenerationConfig;
}

// Generation task with all options resolved
export interface GenerationTask {
  prompt: string;
  variables: Record<string, string>;
  options: {
    model: ImageModel;
  } & ProviderOptions;
  output: {
    directory: string;
    filename: string;
    save_metadata: boolean;
  };
  original_config: ImageGenerationConfig;
}

// Generation result
export interface GenerationResult {
  task: GenerationTask;
  success: boolean;
  image_path?: string;
  image_paths?: string[];
  metadata_path?: string;
  error?: Error;
  retry_count?: number;
  timestamp: Date;
  provider_response?: any;
}

// Progress tracking
export interface ProgressState {
  total_tasks: number;
  completed_tasks: number;
  failed_tasks: number;
  in_progress_tasks: number;
  remaining_tasks: number;
  start_time: Date;
  estimated_completion_time?: Date;
  estimated_cost?: number;
  completed_results: GenerationResult[];
  failed_results: GenerationResult[];
  pending_tasks: GenerationTask[];
}

// Cost estimation
export interface CostEstimate {
  provider: ImageModel;
  task_count: number;
  estimated_cost: number;
  currency: string;
  details: Record<string, any>;
}

// Provider interface
export interface Provider {
  name: ImageModel;
  generateImage(task: GenerationTask): Promise<GenerationResult>;
  estimateCost(tasks: GenerationTask[]): CostEstimate;
  validateTask(task: GenerationTask): boolean;
} 
