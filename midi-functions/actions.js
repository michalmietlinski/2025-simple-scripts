const { exec } = require('child_process');
const fs = require('fs');
const robot = require('robotjs');

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
    }
};

// Action handlers
const actions = {
    console: (params, config) => {
        if (Array.isArray(config.params)) {
            console.log(...config.params);
        } else {
            console.log(params, config.params);
        }
    },
    keyboard: (params, config) => {
        if (keyboardControl[config.shortcut]) {
            keyboardControl[config.shortcut]();
        }
    }
};

module.exports = {
    actions,
    keyboardControl
}; 
