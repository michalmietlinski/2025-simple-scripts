const fs = require('fs').promises;
const path = require('path');
const inquirer = require('inquirer');

const PRESETS_FILE = path.join(__dirname, '../config/presets.json');

async function ensurePresetsFile() {
    try {
        await fs.mkdir(path.dirname(PRESETS_FILE), { recursive: true });
        try {
            await fs.access(PRESETS_FILE);
        } catch {
            await fs.writeFile(PRESETS_FILE, JSON.stringify({}, null, 2));
        }
    } catch (error) {
        console.error('Error initializing presets file:', error);
        process.exit(1);
    }
}

async function loadPresets() {
    try {
        const data = await fs.readFile(PRESETS_FILE, 'utf8');
        return JSON.parse(data);
    } catch (error) {
        return {};
    }
}

async function savePreset() {
    const presets = await loadPresets();
    
    const answers = await inquirer.prompt([
        {
            type: 'input',
            name: 'name',
            message: 'Enter preset name:',
            validate: input => input.trim().length > 0
        },
        {
            type: 'input',
            name: 'dimensions',
            message: 'Enter dimensions (comma-separated numbers, e.g., 800,1024,2048):',
            validate: input => {
                const dims = input.split(',').map(d => parseInt(d.trim()));
                return dims.every(d => !isNaN(d) && d > 0) ? true : 'Please enter valid numbers';
            }
        }
    ]);

    const dimensions = answers.dimensions.split(',').map(d => parseInt(d.trim()));
    presets[answers.name] = dimensions;

    await fs.writeFile(PRESETS_FILE, JSON.stringify(presets, null, 2));
    console.log(`Preset "${answers.name}" saved successfully!`);
}

async function main() {
    await ensurePresetsFile();
    
    const action = await inquirer.prompt([
        {
            type: 'list',
            name: 'choice',
            message: 'What would you like to do?',
            choices: [
                'Create new preset',
                'View existing presets',
                'Delete preset',
                'Exit'
            ]
        }
    ]);

    switch (action.choice) {
        case 'Create new preset':
            await savePreset();
            break;
        case 'View existing presets':
            const presets = await loadPresets();
            console.log('\nExisting presets:');
            Object.entries(presets).forEach(([name, dimensions]) => {
                console.log(`${name}: ${dimensions.join(', ')}`);
            });
            break;
        case 'Delete preset':
            const presetList = await loadPresets();
            if (Object.keys(presetList).length === 0) {
                console.log('No presets available to delete.');
                break;
            }
            const deleteAnswer = await inquirer.prompt([
                {
                    type: 'list',
                    name: 'preset',
                    message: 'Select preset to delete:',
                    choices: Object.keys(presetList)
                }
            ]);
            delete presetList[deleteAnswer.preset];
            await fs.writeFile(PRESETS_FILE, JSON.stringify(presetList, null, 2));
            console.log(`Preset "${deleteAnswer.preset}" deleted successfully!`);
            break;
    }
}

main().catch(console.error); 
