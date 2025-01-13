const { IGNORED_DIRS } = require('./constants');

function shouldSkipDirectory(dirName, isCurrentDir = false) {
    return IGNORED_DIRS.includes(dirName) || (isCurrentDir && dirName === 'node_modules');
}

module.exports = {
    shouldSkipDirectory
}; 
