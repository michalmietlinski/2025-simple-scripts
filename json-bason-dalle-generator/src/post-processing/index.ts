import fs from 'fs-extra';
import path from 'path';
import { PostProcessingScript } from '../types';

/**
 * Interface for post-processing scripts
 */
export interface PostProcessor {
  name: string;
  process(imagePath: string, params: Record<string, any>): Promise<string>;
}

/**
 * Registry of available post-processors
 */
const processors: Record<string, PostProcessor> = {};

/**
 * Registers a post-processor
 * @param processor Post-processor to register
 */
export function registerProcessor(processor: PostProcessor): void {
  processors[processor.name] = processor;
}

/**
 * Applies post-processing scripts to an image
 * @param imagePath Path to the image
 * @param scripts Array of post-processing scripts
 * @returns Path to the processed image
 */
export async function applyPostProcessing(
  imagePath: string,
  scripts: PostProcessingScript[]
): Promise<string> {
  // If no scripts, return the original image
  if (!scripts || scripts.length === 0) {
    return imagePath;
  }
  
  // Apply each script in sequence
  let currentPath = imagePath;
  
  for (const script of scripts) {
    const processor = processors[script.name];
    
    if (!processor) {
      console.warn(`Post-processor "${script.name}" not found, skipping`);
      continue;
    }
    
    try {
      // Apply the processor
      currentPath = await processor.process(currentPath, script.params);
    } catch (error) {
      console.error(`Error applying post-processor "${script.name}":`, error);
    }
  }
  
  return currentPath;
}

// Import and register built-in processors
import { ResizeProcessor } from './resize';
import { WatermarkProcessor } from './watermark';

// Register built-in processors
registerProcessor(new ResizeProcessor());
registerProcessor(new WatermarkProcessor()); 
