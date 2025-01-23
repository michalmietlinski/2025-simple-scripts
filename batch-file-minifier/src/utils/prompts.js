const readline = require('readline');
const inquirer = require('inquirer');

const rl = readline.createInterface({
    input: process.stdin,
    output: process.stdout
});

function question(query) {
    return new Promise(resolve => rl.question(query, resolve));
}

async function promptForOutputMode() {
    const { mode } = await inquirer.prompt([
        {
            type: 'list',
            name: 'mode',
            message: 'Select output mode:',
            choices: [
                { name: 'Create new output directory', value: 1 },
                { name: 'Create output directory within each input directory', value: 2 },
                { name: 'Overwrite original files', value: 3 }
            ]
        }
    ]);

    let backup = false;
    if (mode === 3) {
        const { createBackup } = await inquirer.prompt([
            {
                type: 'confirm',
                name: 'createBackup',
                message: 'Create backups of original files?',
                default: true
            }
        ]);
        backup = createBackup;
    }

    return { mode, backup };
}

async function promptForSuffix() {
    const { useSuffix } = await inquirer.prompt([
        {
            type: 'confirm',
            name: 'useSuffix',
            message: 'Add size suffix to output files?',
            default: true
        }
    ]);

    let customSuffix = '';
    if (useSuffix) {
        const { suffix } = await inquirer.prompt([
            {
                type: 'input',
                name: 'suffix',
                message: 'Enter custom suffix (press Enter for default size suffix):',
            }
        ]);
        customSuffix = suffix;
    }

    return { useSuffix, customSuffix };
}

module.exports = {
    rl,
    question,
    promptForOutputMode,
    promptForSuffix
};
