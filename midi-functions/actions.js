const { exec } = require('child_process');
const fs = require('fs');
const robot = require('robotjs');
const clipboardy = require('clipboardy');

// Note state tracking
const noteState = {
    activeNotes: new Set(),    // Currently held notes
    completeChord: new Set(),  // All notes that were part of this chord attempt
    lastNoteTime: 0,
    SEQUENCE_TIMEOUT: 1000     // ms to reset sequence
};

// Debug logging
function debugLog(...args) {
    console.log('[DEBUG]', ...args);
}

// Helper function to temporarily set clipboard and paste
async function pasteText(text) {
    try {
        const originalClipboard = await clipboardy.read(); // Save current clipboard
        await clipboardy.write(text);
        robot.keyToggle('control', 'down');
        robot.keyTap('v');
        robot.keyToggle('control', 'up');
        await clipboardy.write(originalClipboard); // Restore original clipboard
    } catch (error) {
        console.error('Clipboard operation failed:', error);
        // Try direct typing as fallback
        robot.typeString(text);
    }
}

// Keyboard shortcuts
const keyboardControl = {
    ctrlC: () => {
        robot.keyToggle('control', 'down');
        robot.keyTap('c');
        robot.keyToggle('control', 'up');
    },
    ctrlV: () => {
        robot.keyToggle('control', 'down');
        robot.keyTap('v');
        robot.keyToggle('control', 'up');
    },
    ctrlX: () => {
        robot.keyToggle('control', 'down');
        robot.keyTap('x');
        robot.keyToggle('control', 'up');
    },
    altShiftC: () => {
        robot.keyToggle('alt', 'down');
        robot.keyToggle('shift', 'down');
        robot.keyTap('c');
        robot.keyToggle('shift', 'up');
        robot.keyToggle('alt', 'up');
    },
    ctrlA: () => {
        robot.keyToggle('control', 'down');
        robot.keyTap('a');
        robot.keyToggle('control', 'up');
    },
    enter: () => {
        robot.keyTap('enter');
    },
    space: () => {
        robot.keyTap('space');
    },
    up: () => {
        robot.keyTap('up');
    },
    down: () => {
        robot.keyTap('down');
    },
    left: () => {
        robot.keyTap('left');
    },
    right: () => {
        robot.keyTap('right');
    },
    pasteNiechSpierdala: async () => {
        await pasteText("niech spierdala");
    }
};

// Note handling
function handleNoteOn(note, velocity) {
    const now = Date.now();
    debugLog('Note On:', note, 'Velocity:', velocity);
    
    // Reset if too much time has passed
    if (now - noteState.lastNoteTime > noteState.SEQUENCE_TIMEOUT) {
        debugLog('Resetting due to timeout');
        noteState.completeChord.clear();
    }
    
    // Add note to both active and complete sets
    noteState.activeNotes.add(note);
    noteState.completeChord.add(note);
    noteState.lastNoteTime = now;
    
    debugLog('Active notes:', Array.from(noteState.activeNotes));
    debugLog('Complete chord:', Array.from(noteState.completeChord));
}

function handleNoteOff(note) {
    debugLog('Note Off:', note);
    noteState.activeNotes.delete(note);
    
    // Only check and execute when all notes are released
    if (noteState.activeNotes.size === 0) {
        debugLog('All notes released, checking complete chord');
        
        if (noteState.completeChord.size === 1) {
            // Single note case
            const singleNote = Array.from(noteState.completeChord)[0];
            debugLog('Single note released:', singleNote);
            const config = JSON.parse(fs.readFileSync('config.json', 'utf8'));
            const noteCommand = config.noteCommands[singleNote];
            if (noteCommand) {
                debugLog('Executing single note command');
                executeCommand(noteCommand);
            }
        } else {
            // Chord case
            const chord = checkChordPattern();
            if (chord) {
                debugLog('Executing chord command');
                executeCommand(chord);
            }
        }
        // Reset complete chord after execution attempt
        noteState.completeChord.clear();
    }
}

function checkChordPattern() {
    debugLog('Checking chord pattern');
    const sortedNotes = Array.from(noteState.completeChord).sort((a, b) => a - b);
    const pattern = sortedNotes.join(',');
    debugLog('Checking pattern:', pattern);
    
    // Check if this pattern matches any chord in config
    const config = JSON.parse(fs.readFileSync('config.json', 'utf8'));
    const chordCommand = config.chordCommands?.[pattern];
    
    if (chordCommand) {
        debugLog('Chord detected:', chordCommand.description);
        return chordCommand;
    }
    return null;
}

function executeCommand(command) {
    debugLog('Executing command:', command);
    if (command.action === 'keyboard' && keyboardControl[command.shortcut]) {
        keyboardControl[command.shortcut]();
    } else if (command.action === 'console') {
        if (Array.isArray(command.params)) {
            console.log(...command.params);
        } else {
            console.log(command.params);
        }
    }
}

// Action handlers
const actions = {
    console: (params, config) => {
        debugLog('Console action called with:', params, config);
        if (Array.isArray(config.params)) {
            console.log(...config.params);
        } else {
            console.log(params, config.params);
        }
    },
    keyboard: (params, config) => {
        debugLog('Keyboard action called with:', config.shortcut);
        if (keyboardControl[config.shortcut]) {
            keyboardControl[config.shortcut]();
        }
    },
    note: (params, velocity, isNoteOn) => {
        if (isNoteOn) {
            handleNoteOn(params, velocity);
        } else {
            handleNoteOff(params);
        }
    }
};

module.exports = {
    actions,
    keyboardControl
}; 
