const fs = require('fs').promises;
const path = require('path');
const { SUPPORTED_FORMATS } = require('../utils/constants');
const { shouldSkipDirectory } = require('../utils/directoryUtils');

async function findImagesRecursively(directory, isCurrentDir = false) {
    const images = [];
    const directories = new Set();
    
    async function scan(currentPath) {
        try {
            const entries = await fs.readdir(currentPath, { withFileTypes: true });
            
            for (const entry of entries) {
                if (entry.isDirectory() && shouldSkipDirectory(entry.name, isCurrentDir)) {
                    continue;
                }

                const fullPath = path.join(currentPath, entry.name);
                
                if (entry.isDirectory()) {
                    await scan(fullPath);
                } else {
                    const ext = path.extname(entry.name).toLowerCase();
                    if (SUPPORTED_FORMATS.includes(ext)) {
                        images.push(fullPath);
                        directories.add(path.dirname(fullPath));
                    }
                }
            }
        } catch (error) {
            console.error(`Error scanning ${currentPath}: ${error.message}`);
        }
    }
    
    await scan(directory);
    return { images, directories: Array.from(directories) };
}

module.exports = {
    findImagesRecursively
}; 
