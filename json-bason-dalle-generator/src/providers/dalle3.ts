import fs from 'fs-extra';
import path from 'path';
import axios from 'axios';
import { OpenAI } from 'openai';
import { 
  Provider, 
  GenerationTask, 
  GenerationResult, 
  CostEstimate,
  DallE3Quality,
  DallE3Size
} from '../types';

/**
 * DALL-E 3 provider implementation
 */
export class DallE3Provider implements Provider {
  name = 'dall-e-3' as const;
  private client: OpenAI;
  
  /**
   * Creates a new DALL-E 3 provider
   * @param apiKey OpenAI API key
   */
  constructor(apiKey: string) {
    this.client = new OpenAI({ apiKey });
  }
  
  /**
   * Generates an image using DALL-E 3
   * @param task Generation task
   * @returns Generation result
   */
  async generateImage(task: GenerationTask): Promise<GenerationResult> {
    const startTime = new Date();
    
    try {
      // Validate the task
      if (!this.validateTask(task)) {
        throw new Error('Invalid task configuration for DALL-E 3');
      }
      
      // Extract options
      const { 
        quality = 'standard', 
        size = '1024x1024', 
        style = 'vivid',
        response_format = 'url',
        n = 1,
        user
      } = task.options;
      
      // DALL-E 3 only supports n=1, so we need to make multiple API calls
      const allImages = [];
      
      // Variation hints to make each image more distinct
      const variationHints = [
        "", // First variation uses the original prompt
        "Make this a different variation with unique details.",
        "Create a completely different interpretation of this concept.",
        "Design an alternative version with different styling.",
        "Create a distinct variation with different composition."
      ];
      
      // Make n sequential API calls with n=1 to avoid rate limits
      for (let i = 0; i < n; i++) {
        // Add a delay between calls to respect rate limits
        if (i > 0) {
          // Wait 12 seconds between calls (5 per minute = 12 seconds per call)
          await new Promise(resolve => setTimeout(resolve, 12000));
        }
        
        // Create a variation of the prompt by adding a hint
        const variationHint = i < variationHints.length ? variationHints[i] : variationHints[1];
        const promptVariation = variationHint ? `${task.prompt} ${variationHint}` : task.prompt;
        
        // Make the API call
        const response = await this.client.images.generate({
          model: 'dall-e-3',
          prompt: promptVariation,
          n: 1, // Always use n=1 for DALL-E 3
          quality: quality as DallE3Quality,
          response_format: response_format as 'url' | 'b64_json',
          size: size as DallE3Size,
          style: style as 'vivid' | 'natural',
          user
        });
        
        // Add the image to our collection
        if (response.data && response.data.length > 0) {
          allImages.push(...response.data);
        }
      }
      
      // Ensure we have at least one image
      if (allImages.length === 0) {
        throw new Error('No images generated');
      }
      
      // Process all generated images
      const results = await Promise.all(allImages.map(async (image, index) => {
        // Replace {index} in filename with actual index
        // Ensure the index is always included in the filename
        let indexedFilename = task.output.filename;
        if (indexedFilename.includes('{index}')) {
          indexedFilename = indexedFilename.replace(/\{index\}/g, (index + 1).toString());
        } else {
          // If {index} is not in the template, append it
          indexedFilename = `${indexedFilename}_${index + 1}`;
        }
        
        // Download the image if it's a URL
        let imagePath: string | undefined;
        if (image.url) {
          imagePath = await this.downloadImage(image.url, task.output.directory, indexedFilename);
        } else if (image.b64_json) {
          imagePath = await this.saveBase64Image(image.b64_json, task.output.directory, indexedFilename);
        }
        
        return {
          imagePath,
          image
        };
      }));
      
      // Get all image paths
      const imagePaths = results.map(r => r.imagePath).filter(Boolean) as string[];
      
      // Save metadata if requested
      let metadataPath: string | undefined;
      if (task.output.save_metadata) {
        // Create a combined response for metadata
        const combinedResponse = {
          created: new Date().toISOString(),
          data: allImages
        };
        metadataPath = await this.saveMetadata(combinedResponse, task, imagePaths);
      }
      
      // Return the result
      return {
        task,
        success: true,
        image_path: imagePaths[0], // For backward compatibility
        image_paths: imagePaths,
        metadata_path: metadataPath,
        timestamp: new Date(),
        provider_response: { data: allImages }
      };
    } catch (error) {
      // Handle errors
      return {
        task,
        success: false,
        error: error instanceof Error ? error : new Error(String(error)),
        timestamp: new Date()
      };
    }
  }
  
  /**
   * Estimates the cost of generating images
   * @param tasks Array of generation tasks
   * @returns Cost estimate
   */
  estimateCost(tasks: GenerationTask[]): CostEstimate {
    // Count tasks by quality and size
    const counts = {
      standard: {
        '1024x1024': 0,
        '1024x1792': 0,
        '1792x1024': 0
      },
      hd: {
        '1024x1024': 0,
        '1024x1792': 0,
        '1792x1024': 0
      }
    };
    
    // Count tasks by quality and size
    tasks.forEach(task => {
      const quality = (task.options.quality || 'standard') as 'standard' | 'hd';
      const size = (task.options.size || '1024x1024') as '1024x1024' | '1024x1792' | '1792x1024';
      counts[quality][size] += 1;
    });
    
    // Calculate cost (prices as of November 2023)
    const prices = {
      standard: {
        '1024x1024': 0.04,
        '1024x1792': 0.08,
        '1792x1024': 0.08
      },
      hd: {
        '1024x1024': 0.08,
        '1024x1792': 0.12,
        '1792x1024': 0.12
      }
    };
    
    // Calculate total cost
    let totalCost = 0;
    Object.entries(counts).forEach(([quality, sizes]) => {
      Object.entries(sizes).forEach(([size, count]) => {
        totalCost += prices[quality as 'standard' | 'hd'][size as '1024x1024' | '1024x1792' | '1792x1024'] * count;
      });
    });
    
    return {
      provider: this.name,
      task_count: tasks.length,
      estimated_cost: totalCost,
      currency: 'USD',
      details: counts
    };
  }
  
  /**
   * Validates a generation task
   * @param task Generation task
   * @returns Whether the task is valid
   */
  validateTask(task: GenerationTask): boolean {
    // Check if the model is correct
    if (task.options.model !== this.name) {
      return false;
    }
    
    // Check if the prompt is valid
    if (!task.prompt || task.prompt.trim().length === 0) {
      return false;
    }
    
    // Check if the quality is valid
    const quality = task.options.quality || 'standard';
    if (quality !== 'standard' && quality !== 'hd') {
      return false;
    }
    
    // Check if the size is valid
    const size = task.options.size || '1024x1024';
    if (size !== '1024x1024' && size !== '1024x1792' && size !== '1792x1024') {
      return false;
    }
    
    // Check if the style is valid
    const style = task.options.style || 'vivid';
    if (style !== 'vivid' && style !== 'natural') {
      return false;
    }
    
    // Check if the response format is valid
    const responseFormat = task.options.response_format || 'url';
    if (responseFormat !== 'url' && responseFormat !== 'b64_json') {
      return false;
    }
    
    return true;
  }
  
  /**
   * Downloads an image from a URL
   * @param url Image URL
   * @param directory Output directory
   * @param filename Output filename
   * @returns Path to the downloaded image
   */
  private async downloadImage(url: string, directory: string, filename: string): Promise<string> {
    // Ensure the directory exists
    await fs.ensureDir(directory);
    
    // Download the image
    const response = await axios.get(url, { responseType: 'arraybuffer' });
    
    // Determine the file extension
    const contentType = response.headers['content-type'];
    const extension = contentType === 'image/jpeg' ? 'jpg' : 
                      contentType === 'image/png' ? 'png' : 
                      contentType === 'image/webp' ? 'webp' : 'png';
    
    // Create the output path
    let outputPath = path.join(directory, `${filename}.${extension}`);
    
    // Check if the file already exists and add a unique suffix if needed
    let counter = 1;
    while (await fs.pathExists(outputPath)) {
      outputPath = path.join(directory, `${filename}_${counter}.${extension}`);
      counter++;
    }
    
    // Save the image
    await fs.writeFile(outputPath, response.data);
    
    return outputPath;
  }
  
  /**
   * Saves a base64-encoded image
   * @param base64 Base64-encoded image data
   * @param directory Output directory
   * @param filename Output filename
   * @returns Path to the saved image
   */
  private async saveBase64Image(base64: string, directory: string, filename: string): Promise<string> {
    // Ensure the directory exists
    await fs.ensureDir(directory);
    
    // Create the output path
    let outputPath = path.join(directory, `${filename}.png`);
    
    // Check if the file already exists and add a unique suffix if needed
    let counter = 1;
    while (await fs.pathExists(outputPath)) {
      outputPath = path.join(directory, `${filename}_${counter}.png`);
      counter++;
    }
    
    // Decode and save the image
    const buffer = Buffer.from(base64, 'base64');
    await fs.writeFile(outputPath, buffer);
    
    return outputPath;
  }
  
  /**
   * Saves metadata for a generated image
   * @param response API response
   * @param task Generation task
   * @param imagePaths Paths to the generated images
   * @returns Path to the metadata file
   */
  private async saveMetadata(
    response: any, 
    task: GenerationTask, 
    imagePaths: string[]
  ): Promise<string> {
    // Ensure the directory exists
    await fs.ensureDir(task.output.directory);
    
    // Create the metadata
    const metadata = {
      timestamp: new Date().toISOString(),
      prompt: task.prompt,
      variables: task.variables,
      options: task.options,
      image_paths: imagePaths,
      response: {
        created: response.created,
        data: response.data.map((item: any) => ({
          revised_prompt: item.revised_prompt,
          url: item.url ? true : undefined,
          b64_json: item.b64_json ? true : undefined
        }))
      }
    };
    
    // Create the output path
    let outputPath = path.join(task.output.directory, `${task.output.filename}.json`);
    
    // Check if the file already exists and add a unique suffix if needed
    let counter = 1;
    while (await fs.pathExists(outputPath)) {
      outputPath = path.join(task.output.directory, `${task.output.filename}_${counter}.json`);
      counter++;
    }
    
    // Save the metadata
    await fs.writeJson(outputPath, metadata, { spaces: 2 });
    
    return outputPath;
  }
} 
