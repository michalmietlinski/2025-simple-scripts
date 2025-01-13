const fs = require('fs').promises;
const path = require('path');
const readline = require('readline');
const { SUPPORTED_FORMATS, IGNORED_DIRS } = require('../utils/constants');
const { shouldSkipDirectory } = require('../utils/directoryUtils');

const rl = readline.createInterface({
    input: process.stdin,
    output: process.stdout
});

const question = (query) => new Promise((resolve) => rl.question(query, resolve));

async function findSuffixedImages(directory, targetSuffix, isCurrentDir = false) {
    const images = [];
    
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
                        const baseName = path.basename(entry.name, ext);
                        
                        if (targetSuffix) {
                            if (baseName.endsWith(`_${targetSuffix}`)) {
                                images.push(fullPath);
                            }
                        } else if (baseName.includes('_')) {
                            images.push(fullPath);
                        }
                    }
                }
            }
        } catch (error) {
            console.error(`Error scanning ${currentPath}: ${error.message}`);
        }
    }
    
    await scan(directory);
    return images;
}

async function promptForSuffix() {
    console.log('\nSuffix options:');
    console.log('1. Remove all suffixed images');
    console.log('2. Remove images with specific suffix');
    
    const choice = await question('Choose option (1-2): ');
    
    if (choice === '2') {
        const suffix = await question('Enter suffix to remove (e.g., "small" for files ending with _small): ');
        return suffix.trim();
    }
    
    return '';
}

async function main() {
    try {
        const directory = await question('Enter directory path (press Enter for current): ') || '.';
        const isCurrentDir = directory === '.';
        
        try {
            await fs.access(directory);
        } catch {
            throw new Error('Directory does not exist!');
        }

        const targetSuffix = await promptForSuffix();

        console.log('\nSearching for images...');
        const images = await findSuffixedImages(directory, targetSuffix, isCurrentDir);
        
        if (images.length === 0) {
            console.log(targetSuffix 
                ? `No images found with suffix "_${targetSuffix}".`
                : 'No suffixed images found.');
            return;
        }

        console.log(`\nFound ${images.length} image${images.length > 1 ? 's' : ''}:`);
        images.forEach(img => console.log(path.relative(process.cwd(), img)));

        console.log('\n⚠ WARNING: This will permanently delete these files!');
        const confirm = await question('Are you sure? (type YES to confirm): ');

        if (confirm === 'YES') {
            console.log('\nDeleting files...');
            
            for (const imagePath of images) {
                try {
                    await fs.unlink(imagePath);
                    console.log(`✓ Deleted: ${path.relative(process.cwd(), imagePath)}`);
                } catch (error) {
                    console.error(`✗ Error deleting ${imagePath}: ${error.message}`);
                }
            }
            
            console.log('\nChecking for empty output directories...');
            const outputDirs = new Set(images.map(img => path.dirname(img)));
            
            for (const dir of outputDirs) {
                try {
                    const files = await fs.readdir(dir);
                    if (files.length === 0) {
                        await fs.rmdir(dir);
                        console.log(`✓ Removed empty directory: ${path.relative(process.cwd(), dir)}`);
                    }
                } catch (error) {
                    // Ignore errors when trying to remove directories
                }
            }

            console.log('\nCleanup complete!');
        } else {
            console.log('Operation cancelled.');
        }

    } catch (error) {
        console.error('Error:', error.message);
    } finally {
        rl.close();
    }
}

// Start the program
main();
