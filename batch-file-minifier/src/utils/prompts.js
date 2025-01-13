const readline = require('readline');

const rl = readline.createInterface({
    input: process.stdin,
    output: process.stdout
});

const question = (query) => new Promise((resolve) => rl.question(query, resolve));

async function promptForOutputMode() {
    console.log('\nOutput options:');
    console.log('1. Create new output directory');
    console.log('2. Create output directory within each input directory');
    console.log('3. Overwrite original files');
    
    while (true) {
        const choice = await question('Choose output mode (1-3): ');
        if (['1', '2', '3'].includes(choice)) {
            if (choice === '3') {
                console.log('\n⚠ WARNING: This will overwrite your original images!');
                const confirm = await question('Create backup before overwriting? (Y/n): ');
                if (confirm.toLowerCase() !== 'n') {
                    return { mode: parseInt(choice), backup: true };
                }
                const finalConfirm = await question('Are you sure you want to proceed without backup? (type YES to confirm): ');
                if (finalConfirm !== 'YES') {
                    console.log('Operation cancelled. Please choose another option.');
                    continue;
                }
            }
            return { mode: parseInt(choice), backup: false };
        }
        console.log('Please enter 1, 2, or 3');
    }
}

async function promptForSuffix() {
    const useSuffix = (await question('Add suffix to processed images? (y/N): ')).toLowerCase() === 'y';
    
    if (useSuffix) {
        const customSuffix = await question('Enter suffix (press Enter for dimension): ');
        return {
            useSuffix: true,
            customSuffix: customSuffix.trim()
        };
    }
    
    return {
        useSuffix: false,
        customSuffix: ''
    };
}

module.exports = {
    rl,
    question,
    promptForOutputMode,
    promptForSuffix
};
