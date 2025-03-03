import fs from 'fs-extra';
import path from 'path';
import { PostProcessor } from './index';

/**
 * Parameters for the watermark processor
 */
export interface WatermarkParams {
  text?: string;
  image?: string;
  position?: 'top-left' | 'top-right' | 'bottom-left' | 'bottom-right' | 'center';
  opacity?: number;
  size?: number;
  color?: string;
}

/**
 * Watermark post-processor
 * 
 * This processor uses the sharp and sharp-text libraries to add watermarks to images.
 * They need to be installed separately with:
 * npm install sharp sharp-text
 */
export class WatermarkProcessor implements PostProcessor {
  name = 'watermark';
  
  /**
   * Adds a watermark to an image
   * @param imagePath Path to the image
   * @param params Watermark parameters
   * @returns Path to the watermarked image
   */
  async process(imagePath: string, params: WatermarkParams): Promise<string> {
    try {
      // Try to import sharp
      let sharp;
      try {
        sharp = require('sharp');
      } catch (error) {
        throw new Error('Sharp library not installed. Please install it with: npm install sharp');
      }
      
      // Parse parameters
      const { 
        text, 
        image, 
        position = 'bottom-right', 
        opacity = 0.5,
        size = 24,
        color = 'white'
      } = params;
      
      // Validate parameters
      if (!text && !image) {
        throw new Error('Either text or image must be specified');
      }
      
      // Create output path
      const parsedPath = path.parse(imagePath);
      const outputPath = path.join(
        parsedPath.dir,
        `${parsedPath.name}_watermarked${parsedPath.ext}`
      );
      
      // Load the image
      let sharpImage = sharp(imagePath);
      
      // Get image metadata
      const metadata = await sharpImage.metadata();
      const { width = 0, height = 0 } = metadata;
      
      if (text) {
        // Text watermark
        try {
          // Try to dynamically import sharp-text
          // Note: This is a workaround for TypeScript error
          // In production, you should install the sharp-text package
          const sharpTextModule = await Promise.resolve().then(() => {
            try {
              // @ts-ignore - Ignore TypeScript error for dynamic import
              return require('sharp-text');
            } catch (e) {
              throw new Error('sharp-text library not installed. Please install it with: npm install sharp-text');
            }
          });
          
          const sharpText = sharpTextModule.default || sharpTextModule;
          
          // Create text overlay
          const textOverlay = await sharpText({
            text,
            font: 'sans',
            fontSize: size,
            color,
            opacity
          });
          
          // Calculate position
          const overlayMetadata = await sharp(textOverlay).metadata();
          const overlayWidth = overlayMetadata.width || 0;
          const overlayHeight = overlayMetadata.height || 0;
          
          let left = 0;
          let top = 0;
          
          switch (position) {
            case 'top-left':
              left = 10;
              top = 10;
              break;
            case 'top-right':
              left = width - overlayWidth - 10;
              top = 10;
              break;
            case 'bottom-left':
              left = 10;
              top = height - overlayHeight - 10;
              break;
            case 'bottom-right':
              left = width - overlayWidth - 10;
              top = height - overlayHeight - 10;
              break;
            case 'center':
              left = Math.floor((width - overlayWidth) / 2);
              top = Math.floor((height - overlayHeight) / 2);
              break;
          }
          
          // Composite the text overlay
          sharpImage = sharpImage.composite([
            {
              input: textOverlay,
              left,
              top
            }
          ]);
        } catch (error) {
          throw new Error('sharp-text library not installed. Please install it with: npm install sharp-text');
        }
      } else if (image) {
        // Image watermark
        // Check if the image exists
        if (!await fs.pathExists(image)) {
          throw new Error(`Watermark image not found: ${image}`);
        }
        
        // Load the watermark image
        const watermarkBuffer = await fs.readFile(image);
        
        // Composite the watermark
        sharpImage = sharpImage.composite([
          {
            input: watermarkBuffer,
            gravity: position === 'center' ? 'centre' : position
          }
        ]);
      }
      
      // Save the watermarked image
      await sharpImage.toFile(outputPath);
      
      return outputPath;
    } catch (error) {
      console.error('Error adding watermark:', error);
      return imagePath; // Return original image on error
    }
  }
} 
