const sharp = require('sharp');
const fs = require('fs');
const path = require('path');

// Create input and output directories if they don't exist
const inputDir = path.join(__dirname, 'input');
const outputDir = path.join(__dirname, 'output');

if (!fs.existsSync(inputDir)) {
    fs.mkdirSync(inputDir);
}
if (!fs.existsSync(outputDir)) {
    fs.mkdirSync(outputDir);
}

// Watch for new files in the input directory
console.log('Watching for WebP files in the input directory...');

fs.watch(inputDir, (eventType, filename) => {
    if (filename && filename.toLowerCase().endsWith('.webp')) {
        const inputPath = path.join(inputDir, filename);
        const outputPath = path.join(outputDir, filename.replace('.webp', '.jpg'));

        // Ensure the file exists and is fully written
        setTimeout(() => {
            if (fs.existsSync(inputPath)) {
                convertWebPtoJPG(inputPath, outputPath);
            }
        }, 100);
    }
});

function convertWebPtoJPG(inputPath, outputPath) {
    sharp(inputPath)
        .jpeg({ quality: 90 })
        .toFile(outputPath)
        .then(() => {
            console.log(`Converted ${path.basename(inputPath)} to JPG`);
        })
        .catch(err => {
            console.error(`Error converting ${path.basename(inputPath)}:`, err);
        });
}

console.log(`Place WebP files in the '${inputDir}' directory to convert them to JPG`);
console.log(`Converted files will appear in the '${outputDir}' directory`); 
