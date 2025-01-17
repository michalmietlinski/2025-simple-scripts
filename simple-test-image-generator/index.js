import inquirer from 'inquirer';
import sharp from 'sharp';
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));

const questions = [
    {
        type: 'list',
        name: 'dimensions',
        message: 'Select image dimensions:',
        choices: [
            { name: 'Full HD (1920x1080)', value: { width: 1920, height: 1080 } },
            { name: '4K (3840x2160)', value: { width: 3840, height: 2160 } },
            { name: 'Custom', value: 'custom' }
        ],
        default: 0
    },
    {
        type: 'number',
        name: 'customWidth',
        message: 'Enter custom width:',
        default: 1920,
        when: (answers) => answers.dimensions === 'custom',
        validate: (value) => value > 0 ? true : 'Please enter a positive number'
    },
    {
        type: 'number',
        name: 'customHeight',
        message: 'Enter custom height:',
        default: 1080,
        when: (answers) => answers.dimensions === 'custom',
        validate: (value) => value > 0 ? true : 'Please enter a positive number'
    },
    {
        type: 'input',
        name: 'color',
        message: 'Enter color (name or hex code):',
        default: 'white',
        validate: (value) => value.length > 0 ? true : 'Please enter a color'
    },
    {
        type: 'input',
        name: 'filename',
        message: 'Enter base filename:',
        default: 'test-image',
        validate: (value) => value.length > 0 ? true : 'Please enter a filename'
    },
    {
        type: 'number',
        name: 'count',
        message: 'How many images do you want to generate?',
        default: 1,
        validate: (value) => value > 0 ? true : 'Please enter a positive number'
    },
    {
        type: 'confirm',
        name: 'numbered',
        message: 'Add centered number to images?',
        default: false
    },
    {
        type: 'input',
        name: 'numberColor',
        message: 'Enter color for the number (name or hex code):',
        default: 'black',
        when: (answers) => answers.numbered,
        validate: (value) => value.length > 0 ? true : 'Please enter a color'
    }
];

const outputDir = path.join(__dirname, 'output');
if (!fs.existsSync(outputDir)) {
    fs.mkdirSync(outputDir);
}

async function generateImage(width, height, color, filename, index, numbered, numberColor) {
    const svg = numbered ? `
        <svg width="${width}" height="${height}">
            <rect width="100%" height="100%" fill="${color}"/>
            <text 
                x="50%" 
                y="50%" 
                font-family="Arial" 
                font-size="${Math.min(width, height) / 2}px" 
                fill="${numberColor}" 
                text-anchor="middle" 
                dominant-baseline="middle"
            >
                ${index + 1}
            </text>
        </svg>
    ` : '';

    const image = numbered ? 
        sharp(Buffer.from(svg))
            .resize(width, height) :
        sharp({
            create: {
                width: width,
                height: height,
                channels: 4,
                background: color
            }
        });

    await image
        .png()
        .toFile(path.join(outputDir, `${filename}-${index + 1}.png`));
}

async function main() {
    try {
        const answers = await inquirer.prompt(questions);
        
        const dimensions = answers.dimensions === 'custom' 
            ? { width: answers.customWidth, height: answers.customHeight }
            : answers.dimensions;

        console.log(`\nGenerating ${answers.count} images (${dimensions.width}x${dimensions.height}) in color: ${answers.color}`);
        if (answers.numbered) {
            console.log(`Adding centered numbers in color: ${answers.numberColor}`);
        }
        
        for (let i = 0; i < answers.count; i++) {
            await generateImage(
                dimensions.width, 
                dimensions.height, 
                answers.color, 
                answers.filename, 
                i,
                answers.numbered,
                answers.numberColor
            );
            console.log(`Generated image ${i + 1} of ${answers.count}`);
        }
        
        console.log('\nDone! Images saved to output directory.');
    } catch (error) {
        console.error('An error occurred:', error);
    }
}

main(); 
