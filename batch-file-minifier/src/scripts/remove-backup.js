const fs = require('fs').promises;
const path = require('path');
const readline = require('readline');
const { BACKUP_DIR } = require('../utils/constants');
const { shouldSkipDirectory } = require('../utils/directoryUtils');

const rl = readline.createInterface({
    input: process.stdin,
    output: process.stdout
});

const question = (query) => new Promise((resolve) => rl.question(query, resolve));

async function findBackupDirs(startPath, isCurrentDir = false) {
    const backupDirs = [];
    
    // First check if the current path itself is a backup directory
    const currentDirName = path.basename(startPath);
    if (currentDirName === BACKUP_DIR) {
        backupDirs.push(startPath);
        return backupDirs;
    }
    
    async function scan(currentPath) {
        try {
            const entries = await fs.readdir(currentPath, { withFileTypes: true });
            
            for (const entry of entries) {
                // Skip non-directories and ignored directories
                if (!entry.isDirectory()) continue;
                
                const fullPath = path.join(currentPath, entry.name);
                
                // Check if this is a backup directory
                if (entry.name === BACKUP_DIR) {
                    console.log(`Found backup directory: ${path.relative(process.cwd(), fullPath)}`);
                    backupDirs.push(fullPath);
                    continue; // Don't scan inside backup directories
                }
                
                // Skip ignored directories but allow scanning others
                if (!shouldSkipDirectory(entry.name, isCurrentDir)) {
                    await scan(fullPath);
                }
            }
        } catch (error) {
            console.error(`Error scanning ${currentPath}: ${error.message}`);
        }
    }
    
    await scan(startPath);
    
    // Debug output
    if (backupDirs.length === 0) {
        console.log('Debug: No backup directories found. Searched in:', startPath);
        try {
            const allDirs = await fs.readdir(startPath);
            console.log('Debug: Directory contents:', allDirs);
        } catch (error) {
            console.log('Debug: Error reading directory:', error.message);
        }
    }
    
    return backupDirs;
}

async function removeDirectory(dirPath) {
    try {
        const entries = await fs.readdir(dirPath, { withFileTypes: true });
        
        // First, recursively handle all contents
        for (const entry of entries) {
            const fullPath = path.join(dirPath, entry.name);
            
            if (entry.isDirectory()) {
                await removeDirectory(fullPath);
            } else {
                try {
                    await fs.unlink(fullPath);
                    console.log(`✓ Deleted file: ${path.relative(process.cwd(), fullPath)}`);
                } catch (error) {
                    console.error(`Error deleting file ${fullPath}: ${error.message}`);
                }
            }
        }
        
        // Then try to remove the directory itself
        try {
            await fs.rmdir(dirPath);
            console.log(`✓ Removed directory: ${path.relative(process.cwd(), dirPath)}`);
            return true;
        } catch (error) {
            console.error(`Error removing directory ${dirPath}: ${error.message}`);
            return false;
        }
    } catch (error) {
        console.error(`Error accessing ${dirPath}: ${error.message}`);
        return false;
    }
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

        console.log('\nSearching for backup directories...');
        const backupDirs = await findBackupDirs(directory, isCurrentDir);
        
        if (backupDirs.length === 0) {
            console.log('No backup directories found.');
            rl.close();
            return;
        }

        console.log(`\nFound ${backupDirs.length} backup director${backupDirs.length > 1 ? 'ies' : 'y'}:`);
        backupDirs.forEach(dir => console.log(path.relative(process.cwd(), dir)));

        console.log('\n⚠ WARNING: This will permanently delete all backup directories and their contents!');
        const confirm = await question('Are you sure? (type YES to confirm): ');

        if (confirm === 'YES') {
            console.log('\nRemoving backup directories...');
            
            let successCount = 0;
            for (const backupDir of backupDirs) {
                const success = await removeDirectory(backupDir);
                if (success) successCount++;
            }

            console.log(`\nBackup cleanup complete! Successfully removed ${successCount} of ${backupDirs.length} directories.`);
        } else {
            console.log('Operation cancelled.');
        }

    } catch (error) {
        console.error('Error:', error.message);
    } finally {
        rl.close();
    }
}

main(); 
