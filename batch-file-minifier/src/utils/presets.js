const fs = require('fs').promises;
const path = require('path');

const PRESETS_FILE = path.join(__dirname, '../config/presets.json');

async function getPresets() {
    try {
        const data = await fs.readFile(PRESETS_FILE, 'utf8');
        return JSON.parse(data);
    } catch (error) {
        return {};
    }
}

async function getPresetDimensions(presetName) {
    const presets = await getPresets();
    return presets[presetName] || null;
}

module.exports = {
    getPresets,
    getPresetDimensions
}; 
