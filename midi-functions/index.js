const midi = require('midi');
const readline = require('readline');
const fs = require('fs');
const path = require('path');
const { actions } = require('./actions');

const config = JSON.parse(fs.readFileSync(path.join(__dirname, 'config.json'), 'utf8'));

const rl = readline.createInterface({
    input: process.stdin,
    output: process.stdout
});

// Volume control methods
const volumeControl = {
    powershell: (value) => {
        const volumePercent = Math.round((value / 127) * 100);
        exec(`powershell -c "$volume = New-Object -ComObject Shell.Application; $volume.Windows()[0].Document.Application.Volume = ${volumePercent}"`);
    },
    nircmd: (value) => {
        exec(`nircmd.exe setsysvolume ${Math.round((value / 127) * 65535)}`);
    },
    wscript: (value) => {
        const script = `
        Set WshShell = CreateObject("WScript.Shell")
        WshShell.Run "sndvol.exe"
        WScript.Sleep 500
        WshShell.SendKeys ${Math.round((value / 127) * 100)}
        WshShell.SendKeys "{ENTER}"`;
        
        fs.writeFileSync('temp_vol.vbs', script);
        exec('cscript //nologo temp_vol.vbs', () => fs.unlinkSync('temp_vol.vbs'));
    }
};

// Command executor
function executeCommand(command, params) {
    if (command && actions[command.action]) {
        actions[command.action](params, command);
    }
}

function handleMidiMessage(deltaTime, message) {
    const [command, note, velocity] = message;
    const channel = command & 0x0F;
    const type = command & 0xF0;

    switch(type) {
        case 0x90: // Note On
            if (velocity > 0) {
                // Always pass to note handler, don't execute single note commands immediately
                actions.note(note, velocity, true);
            } else {
                // Note Off with velocity 0
                actions.note(note, 0, false);
            }
            break;
            
        case 0x80: // Note Off
            actions.note(note, velocity, false);
            break;
            
        case 0xB0: // Control Change
            const controlCommand = config.controllerCommands?.[note];
            if (controlCommand) {
                executeCommand(controlCommand, velocity);
            } else {
                console.log(`Control Change - Controller: ${note}, Value: ${velocity}, Channel: ${channel}`);
            }
            break;
            
        default:
            console.log('Other message:', message);
    }
}

async function main() {
    const input = new midi.Input();
    const portCount = input.getPortCount();

    if (portCount === 0) {
        console.log('No MIDI devices found');
        rl.close();
        return;
    }

    console.log('\nAvailable MIDI devices:');
    for (let i = 0; i < portCount; i++) {
        console.log(`${i}: ${input.getPortName(i)}`);
    }

    // Open first port if only one device
    const portToUse = portCount === 1 ? 0 : await new Promise(resolve => {
        rl.question('\nSelect device number: ', answer => {
            resolve(parseInt(answer) || 0);
        });
    });

    try {
        input.openPort(portToUse);
        console.log(`\nConnected to ${input.getPortName(portToUse)}`);
        
        input.on('message', handleMidiMessage);
        
        console.log('Listening for MIDI messages... (Press Ctrl+C to exit)\n');

        process.on('SIGINT', () => {
            input.closePort();
            rl.close();
            process.exit();
        });
    } catch (err) {
        console.error('Failed to open MIDI port:', err.message);
        rl.close();
    }
}

main(); 
