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

// Volume control methods
const volumeControl = {
    powershell: (value) => {
        const volumePercent = Math.round((value / 127) * 100);
        exec(`powershell -c "$audio = Get-AudioDevice -Playback; Set-AudioDevice -ID $audio.ID -Volume ${volumePercent}"`);
    },
    nircmd: (value) => {
        exec(`nircmd.exe setvolume 0 ${Math.round((value / 127) * 65535)} ${Math.round((value / 127) * 65535)}`);
    },
    wscript: (value) => {
        const script = `
        Set WshShell = CreateObject("WScript.Shell")
        Set oShell = CreateObject("Shell.Application")
        oShell.ToggleDesktop
        WScript.Sleep 100
        WshShell.SendKeys "${Math.round((value / 127) * 100)}"
        WshShell.SendKeys "{ENTER}"
        oShell.ToggleDesktop`;
        
        fs.writeFileSync('temp_vol.vbs', script);
        exec('cscript //nologo temp_vol.vbs', () => fs.unlinkSync('temp_vol.vbs'));
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
    volume: (params, config) => {
        if (process.platform === 'win32') {
            try {
                volumeControl[config.method](params);
            } catch (error) {
                if (config.fallback) {
                    try {
                        volumeControl[config.fallback](params);
                    } catch (fallbackError) {
                        console.error('Volume control failed. Please install nircmd or check system permissions.');
                    }
                }
            }
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
    volumeControl,
    keyboardControl
}; 
