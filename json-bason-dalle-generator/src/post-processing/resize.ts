import fs from 'fs-extra';
import path from 'path';
import { PostProcessor } from './index';

/**
 * Parameters for the resize processor
 */
export interface ResizeParams {
  width?: number;
  height?: number;
  fit?: 'cover' | 'contain' | 'fill' | 'inside' | 'outside';
  position?: string;
  quality?: number;
}

/**
 * Resize post-processor
 * 
 * This processor uses the sharp library to resize images.
 * It needs to be installed separately with:
 * npm install sharp
 */
export class ResizeProcessor implements PostProcessor {
  name = 'resize';
  
  /**
   * Resizes an image
   * @param imagePath Path to the image
   * @param params Resize parameters
   * @returns Path to the resized image
   */
  async process(imagePath: string, params: ResizeParams): Promise<string> {
    try {
      // Try to import sharp
      let sharp;
      try {
        sharp = require('sharp');
      } catch (error) {
        throw new Error('Sharp library not installed. Please install it with: npm install sharp');
      }
      
      // Parse parameters
      const { width, height, fit = 'cover', position = 'center', quality = 80 } = params;
      
      // Validate parameters
      if (!width && !height) {
        throw new Error('Either width or height must be specified');
      }
      
      // Create output path
      const parsedPath = path.parse(imagePath);
      const outputPath = path.join(
        parsedPath.dir,
        `${parsedPath.name}_resized${parsedPath.ext}`
      );
      
      // Resize the image
      await sharp(imagePath)
        .resize({
          width,
          height,
          fit,
          position
        })
        .jpeg({ quality })
        .toFile(outputPath);
      
      return outputPath;
    } catch (error) {
      console.error('Error resizing image:', error);
      return imagePath; // Return original image on error
    }
  }
} 
