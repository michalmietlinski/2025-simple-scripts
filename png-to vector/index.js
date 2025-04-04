const fs = require('fs-extra');
const path = require('path');
const Jimp = require('jimp');
const potrace = require('potrace');

// Default directories
const DEFAULT_INPUT_DIR = path.join(__dirname, 'input');
const DEFAULT_OUTPUT_DIR = path.join(__dirname, 'output');

// Get directories from command line arguments or use defaults
const inputDir = process.argv[2] || DEFAULT_INPUT_DIR;
const outputDir = process.argv[3] || DEFAULT_OUTPUT_DIR;

// Configuration
const MAX_CONCURRENT = 4; // Maximum number of concurrent conversions
const RECURSIVE = true; // Whether to scan subdirectories for PNG files

// Supported image formats
const SUPPORTED_EXTENSIONS = ['.png', '.jpg', '.jpeg'];

// Ensure directories exist
console.log('Checking directories...');
if (!fs.existsSync(inputDir)) {
  console.log(`Creating input directory: ${inputDir}`);
  fs.ensureDirSync(inputDir);
}

if (!fs.existsSync(outputDir)) {
  console.log(`Creating output directory: ${outputDir}`);
  fs.ensureDirSync(outputDir);
}
console.log('Directories ready.');

// Configuration for potrace
const potraceParams = {
  threshold: 128,
  color: '#000000',
  background: 'transparent',
  turdSize: 2,
  turnPolicy: potrace.Potrace.TURNPOLICY_MINORITY
};

/**
 * Check if a file has a supported image extension
 * @param {string} filename - File name to check
 * @returns {boolean} - Whether the file has a supported extension
 */
function isSupportedImageFile(filename) {
  const ext = path.extname(filename).toLowerCase();
  return SUPPORTED_EXTENSIONS.includes(ext);
}

/**
 * Find all supported image files in a directory and its subdirectories
 * @param {string} dir - Directory to scan
 * @param {boolean} recursive - Whether to scan subdirectories
 * @returns {Promise<Array>} - Array of file paths
 */
async function findImageFiles(dir, recursive = RECURSIVE) {
  let results = [];
  
  try {
    const items = await fs.readdir(dir);
    
    for (const item of items) {
      const itemPath = path.join(dir, item);
      const stats = await fs.stat(itemPath);
      
      if (stats.isDirectory() && recursive) {
        // Recursively scan subdirectories
        const subResults = await findImageFiles(itemPath, recursive);
        results = results.concat(subResults);
      } else if (stats.isFile() && isSupportedImageFile(item)) {
        // Add supported image file to results
        results.push(itemPath);
      }
    }
  } catch (err) {
    console.error(`Error scanning directory ${dir}: ${err.message}`);
  }
  
  return results;
}

/**
 * Convert an image file to SVG using potrace
 * @param {string} inputPath - Path to input image file
 * @param {string} outputPath - Path to output SVG file
 * @returns {Promise} - Promise that resolves when conversion is complete
 */
function convertImageToSvg(inputPath, outputPath) {
  return new Promise((resolve, reject) => {
    // Use the potrace.trace function instead of creating a new instance
    potrace.trace(inputPath, potraceParams, (err, svg) => {
      if (err) {
        reject(err);
        return;
      }
      
      // Create output directory if it doesn't exist
      const outputDir = path.dirname(outputPath);
      fs.ensureDirSync(outputDir);
      
      // Write SVG to file
      fs.writeFile(outputPath, svg, (writeErr) => {
        if (writeErr) {
          reject(writeErr);
          return;
        }
        resolve();
      });
    });
  });
}

/**
 * Process files in batches with limited concurrency
 * @param {Array} items - Array of items to process
 * @param {Function} processor - Function to process each item
 * @param {Number} concurrentLimit - Maximum number of concurrent operations
 * @returns {Promise<Array>} - Results of processing
 */
async function processBatch(items, processor, concurrentLimit = MAX_CONCURRENT) {
  const results = [];
  
  // Process in batches
  for (let i = 0; i < items.length; i += concurrentLimit) {
    const batch = items.slice(i, i + concurrentLimit);
    const batchPromises = batch.map(processor);
    
    // Wait for current batch to complete
    const batchResults = await Promise.all(batchPromises);
    results.push(...batchResults);
    
    // Simple progress indicator
    console.log(`Progress: ${Math.min(i + concurrentLimit, items.length)} of ${items.length} files processed`);
  }
  
  return results;
}

/**
 * Process all supported image files in the input directory
 */
async function processAllImageFiles() {
  try {
    console.log(`Scanning for image files (${SUPPORTED_EXTENSIONS.join(', ')}) in ${inputDir}${RECURSIVE ? ' (including subdirectories)' : ''}...`);
    
    // Find all image files
    const imageFilePaths = await findImageFiles(inputDir);
    
    if (imageFilePaths.length === 0) {
      console.log(`No supported image files found in ${inputDir}`);
      console.log(`Please place your image files in the input directory: ${inputDir}`);
      return;
    }
    
    console.log(`Found ${imageFilePaths.length} image files to convert`);
    console.log(`Converting with concurrency of ${MAX_CONCURRENT} files at a time`);
    
    // Create a processor function
    const processFile = async (filePath) => {
      // Get relative path from input directory
      const relPath = path.relative(inputDir, filePath);
      const filename = path.basename(filePath);
      
      // Create corresponding output path
      const outputPath = path.join(
        outputDir, 
        relPath.replace(/\.(png|jpg|jpeg)$/i, '.svg')
      );
      
      console.log(`Converting ${relPath} to SVG...`);
      try {
        await convertImageToSvg(filePath, outputPath);
        console.log(`Successfully converted ${relPath} to SVG`);
        return { file: relPath, success: true };
      } catch (error) {
        console.error(`Error converting ${relPath}: ${error.message}`);
        return { file: relPath, success: false, error: error.message };
      }
    };
    
    // Process files in batches
    const results = await processBatch(imageFilePaths, processFile);
    
    // Summary
    const successful = results.filter(r => r.success).length;
    console.log(`\nConversion complete: ${successful} of ${imageFilePaths.length} files converted successfully`);
    
    if (successful < imageFilePaths.length) {
      console.log(`Failed to convert ${imageFilePaths.length - successful} files`);
      
      // List failed files
      const failedFiles = results.filter(r => !r.success);
      if (failedFiles.length > 0) {
        console.log('\nFailed files:');
        failedFiles.forEach(result => {
          console.log(`- ${result.file}: ${result.error}`);
        });
        
        console.log('\nTips for troubleshooting:');
        console.log('- Check if images are corrupted');
        console.log('- Try adjusting the threshold parameter in potraceParams');
        console.log('- For large images, you might need more memory');
      }
    }
  } catch (error) {
    console.error(`Error processing files: ${error.message}`);
  }
}

// Run the main function
console.log(`
Image to SVG Converter
===================
Supported formats: ${SUPPORTED_EXTENSIONS.join(', ')}
Input directory: ${inputDir}
Output directory: ${outputDir}
`);

// Instructions for usage
if (process.argv.length <= 2) {
  console.log(`
Usage: 
  node index.js [inputDir] [outputDir]

Example:
  node index.js ./my-images ./my-svgs
  
  If no directories are provided, defaults are used:
  - Input: ${DEFAULT_INPUT_DIR}
  - Output: ${DEFAULT_OUTPUT_DIR}
  
  Place your image files in the input directory and run this script.
  Converted SVG files will be saved to the output directory.
`);
}

// Start the conversion process
processAllImageFiles(); 
