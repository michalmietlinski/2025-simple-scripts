import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const outputDir = path.join(__dirname, 'output');

if (fs.existsSync(outputDir)) {
    const files = fs.readdirSync(outputDir);
    for (const file of files) {
        fs.unlinkSync(path.join(outputDir, file));
    }
    console.log('Output directory cleaned.');
} else {
    console.log('Output directory does not exist.');
} 
