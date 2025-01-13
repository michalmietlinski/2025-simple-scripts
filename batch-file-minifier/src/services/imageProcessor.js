const sharp = require('sharp');
const fs = require('fs').promises;
const path = require('path');

async function processImage(inputPath, outputPath, maxSize) {
    try {
        const metadata = await sharp(inputPath).metadata();
        
        const aspectRatio = metadata.width / metadata.height;
        let newWidth, newHeight;
        
        if (metadata.width > metadata.height) {
            newWidth = Math.min(maxSize, metadata.width);
            newHeight = Math.round(newWidth / aspectRatio);
        } else {
            newHeight = Math.min(maxSize, metadata.height);
            newWidth = Math.round(newHeight * aspectRatio);
        }

        if (metadata.width <= maxSize && metadata.height <= maxSize) {
            console.log(`⚠ Skipping ${path.basename(inputPath)} - already smaller than ${maxSize}px`);
            return;
        }

        if (outputPath === inputPath) {
            const tempPath = inputPath + '.temp';
            await sharp(inputPath)
                .resize(newWidth, newHeight, { fit: 'inside' })
                .toFile(tempPath);
            
            await fs.unlink(inputPath);
            await fs.rename(tempPath, inputPath);
        } else {
            await fs.mkdir(path.dirname(outputPath), { recursive: true });
            await sharp(inputPath)
                .resize(newWidth, newHeight, { fit: 'inside' })
                .toFile(outputPath);
        }
        
        console.log(`✓ Processed: ${path.relative(process.cwd(), outputPath)} (${newWidth}x${newHeight})`);
    } catch (error) {
        console.error(`✗ Error processing ${inputPath}: ${error.message}`);
    }
}

module.exports = {
    processImage
}; 
