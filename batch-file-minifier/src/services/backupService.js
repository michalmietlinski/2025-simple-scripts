const fs = require('fs').promises;
const path = require('path');
const { BACKUP_DIR } = require('../utils/constants');

async function createBackup(imagePath, baseDir) {
    try {
        const relativePath = path.relative(baseDir, imagePath);
        const backupPath = path.join(
            path.dirname(baseDir),
            BACKUP_DIR,
            relativePath
        );
        
        await fs.mkdir(path.dirname(backupPath), { recursive: true });
        await fs.copyFile(imagePath, backupPath);
        console.log(`✓ Backup created: ${path.relative(process.cwd(), backupPath)}`);
        return true;
    } catch (error) {
        console.error(`✗ Error creating backup for ${imagePath}: ${error.message}`);
        return false;
    }
}

module.exports = {
    createBackup
}; 
