const midi = require('midi');
const readline = require('readline');

const rl = readline.createInterface({
    input: process.stdin,
    output: process.stdout
});

function handleMidiMessage(deltaTime, message) {
    const [command, note, velocity] = message;
    const channel = command & 0x0F;
    const type = command & 0xF0;

    switch(type) {
        case 0x90: // Note On
            if (velocity > 0) {
                console.log(`Note On - Note: ${note}, Velocity: ${velocity}, Channel: ${channel}`);
            } else {
                console.log(`Note Off - Note: ${note} (velocity 0), Channel: ${channel}`);
            }
            break;
        case 0x80: // Note Off
            console.log(`Note Off - Note: ${note}, Velocity: ${velocity}, Channel: ${channel}`);
            break;
        case 0xB0: // Control Change
            console.log(`Control Change - Controller: ${note}, Value: ${velocity}, Channel: ${channel}`);
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
