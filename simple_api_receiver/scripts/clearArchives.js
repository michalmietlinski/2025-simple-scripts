const fs = require('fs').promises;
const path = require('path');

async function clearDirectory(dirPath) {
    try {
        const entries = await fs.readdir(dirPath, { withFileTypes: true });
        
        for (const entry of entries) {
            const fullPath = path.join(dirPath, entry.name);
            if (entry.isDirectory()) {
                await clearDirectory(fullPath);
                await fs.rmdir(fullPath);
            } else {
                await fs.unlink(fullPath);
            }
        }
    } catch (error) {
        if (error.code !== 'ENOENT') {
            throw error;
        }
    }
}

async function clearArchives() {
    const archivesPath = path.join(__dirname, '..', 'archives');
    try {
        await clearDirectory(archivesPath);
        await fs.mkdir(archivesPath, { recursive: true });
        console.log('Archives cleared successfully');
    } catch (error) {
        console.error('Error clearing archives:', error);
        process.exit(1);
    }
}

clearArchives(); 
