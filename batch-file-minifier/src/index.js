const fs = require('fs').promises;
const path = require('path');
const { question, promptForOutputMode, promptForSuffix, rl } = require('./utils/prompts');
const { findImagesRecursively } = require('./services/directoryScanner');
const { processImage } = require('./services/imageProcessor');
const { createBackup } = require('./services/backupService');
const { getOutputPath } = require('./utils/fileSystem');
const { DEFAULT_MAX_SIZE, BACKUP_DIR } = require('./utils/constants');

async function main() {
    try {
        const directory = await question('Enter directory path (press Enter for current): ') || '.';
        const isCurrentDir = directory === '.';
        
        try {
            await fs.access(directory);
        } catch {
            throw new Error('Directory does not exist!');
        }

        const maxSize = parseInt(await question(`Enter maximum dimension (default ${DEFAULT_MAX_SIZE}px): `)) || DEFAULT_MAX_SIZE;
        const { mode: outputMode, backup: createBackups } = await promptForOutputMode();
        const { useSuffix, customSuffix } = await promptForSuffix();

        console.log('\nSearching for images...');
        const { images, directories } = await findImagesRecursively(directory, isCurrentDir);
        
        if (images.length === 0) {
            console.log('No supported images found.');
            return;
        }

        console.log(`\nFound ${images.length} images in ${directories.length} directories...\n`);

        for (const imagePath of images) {
            if (outputMode === 3 && createBackups) {
                const backupSuccess = await createBackup(imagePath, directory);
                if (!backupSuccess && !useSuffix) {
                    console.log(`Skipping ${imagePath} due to backup failure`);
                    continue;
                }
            }

            const outputPath = await getOutputPath(
                imagePath,
                directory,
                outputMode,
                maxSize,
                useSuffix,
                customSuffix
            );
            
            await processImage(imagePath, outputPath, maxSize);
        }

        if (createBackups) {
            console.log(`\nBackups created in: ${path.resolve(path.dirname(directory), BACKUP_DIR)}`);
        }
        console.log('\nAll images processed!');

    } catch (error) {
        console.error('Error:', error.message);
    } finally {
        rl.close();
    }
}

main(); 
