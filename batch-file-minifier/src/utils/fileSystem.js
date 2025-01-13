const fs = require('fs').promises;
const path = require('path');

async function ensureDirectoryExists(dirPath) {
    try {
        await fs.access(dirPath);
    } catch {
        await fs.mkdir(dirPath, { recursive: true });
    }
}

async function getOutputPath(inputPath, baseDir, outputMode, maxSize, useSuffix, customSuffix) {
    const parsedPath = path.parse(inputPath);
    let newName = parsedPath.name;
    
    if (useSuffix) {
        newName += `_${customSuffix || maxSize}`;
    }
    newName += parsedPath.ext;

    switch (outputMode) {
        case 1:
            return path.join(
                path.dirname(baseDir),
                'output',
                path.relative(baseDir, path.dirname(inputPath)),
                newName
            );
        case 2:
            return path.join(
                path.dirname(inputPath),
                'output',
                newName
            );
        case 3:
            return useSuffix 
                ? path.join(path.dirname(inputPath), newName)
                : inputPath;
        default:
            return inputPath;
    }
}

module.exports = {
    ensureDirectoryExists,
    getOutputPath
}; 
