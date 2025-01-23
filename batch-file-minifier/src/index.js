const fs = require('fs').promises;
const path = require('path');
const { question, promptForOutputMode, promptForSuffix, rl } = require('./utils/prompts');
const { findImagesRecursively } = require('./services/directoryScanner');
const { processImage } = require('./services/imageProcessor');
const { createBackup } = require('./services/backupService');
const { getOutputPath } = require('./utils/fileSystem');
const { DEFAULT_MAX_SIZE, BACKUP_DIR } = require('./utils/constants');
const { getPresets } = require('./utils/presets');
const inquirer = require('inquirer');

async function main() {
    try {
        const directory = await question('Enter directory path (press Enter for current): ') || '.';
        const isCurrentDir = directory === '.';
        
        try {
            await fs.access(directory);
        } catch {
            throw new Error('Directory does not exist!');
        }

        const choices = await inquirer.prompt([
            {
                type: 'list',
                name: 'mode',
                message: 'How would you like to specify the dimensions?',
                choices: ['Enter manually', 'Use preset']
            }
        ]);

        let dimensions = [];
        let forceOutputSettings = false;

        if (choices.mode === 'Use preset') {
            const presets = await getPresets();
            if (Object.keys(presets).length === 0) {
                console.log('No presets available. Please create one first using "npm run preset"');
                process.exit(1);
            }

            const presetChoice = await inquirer.prompt([
                {
                    type: 'list',
                    name: 'preset',
                    message: 'Select a preset:',
                    choices: Object.keys(presets)
                }
            ]);

            dimensions = presets[presetChoice.preset];
            // Force output settings if preset has multiple dimensions
            forceOutputSettings = dimensions.length > 1;
        } else {
            const answer = await inquirer.prompt([
                {
                    type: 'input',
                    name: 'dimension',
                    message: 'Enter maximum dimension:',
                    validate: input => !isNaN(input) && parseInt(input) > 0
                }
            ]);
            dimensions = [parseInt(answer.dimension)];
        }

        // If using multi-dimension preset, force output settings
        const { mode: outputMode, backup: createBackups } = forceOutputSettings 
            ? { mode: 2, backup: false }
            : await promptForOutputMode();
            
        const { useSuffix, customSuffix } = forceOutputSettings
            ? { useSuffix: true, customSuffix: '' }
            : await promptForSuffix();

        if (forceOutputSettings) {
            console.log('\nNote: Using preset with multiple dimensions - output will be created in subdirectories with size suffixes.');
        }

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

            for (const dimension of dimensions) {
                const outputPath = await getOutputPath(
                    imagePath,
                    directory,
                    outputMode,
                    dimension,
                    useSuffix,
                    customSuffix
                );
                
                console.log(`Processing ${path.basename(imagePath)} to ${dimension}px...`);
                await processImage(imagePath, outputPath, dimension);
                console.log(`✓ Created: ${path.basename(outputPath)}`);
            }
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
