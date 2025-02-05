# MIDI Functions

A Node.js library for handling MIDI input/output with support for both WebMIDI API and Serial MIDI connections.

## MIDI Protocol Specifications

### Message Structure
Each MIDI message consists of:
- **Status Byte** (1st byte)
  - Bits 7-4: Command type
  - Bits 3-0: Channel number (0-15)
- **Data Bytes** (0-2 bytes depending on message type)
  - Each data byte uses 7 bits (0-127)
  - Bit 7 is always 0 in data bytes

### MIDI Command Types

| Command | Hex | Binary | Description | Data Bytes |
|---------|-----|--------|-------------|------------|
| Note Off | 0x80 | 1000xxxx | Note released | note (0-127), velocity (0-127) |
| Note On | 0x90 | 1001xxxx | Note pressed | note (0-127), velocity (0-127) |
| Poly Aftertouch | 0xA0 | 1010xxxx | Per-note pressure | note (0-127), pressure (0-127) |
| Control Change | 0xB0 | 1011xxxx | Controller value | controller (0-127), value (0-127) |
| Program Change | 0xC0 | 1100xxxx | Program/patch select | program (0-127) |
| Channel Aftertouch | 0xD0 | 1101xxxx | Channel pressure | pressure (0-127) |
| Pitch Bend | 0xE0 | 1110xxxx | Pitch wheel | LSB (0-127), MSB (0-127) |
| System Message | 0xF0 | 1111xxxx | System-specific | Variable |

### Common Control Change (CC) Numbers

| CC Number | Description |
|-----------|-------------|
| 0 | Bank Select (MSB) |
| 1 | Modulation Wheel |
| 7 | Volume |
| 10 | Pan |
| 11 | Expression |
| 64 | Sustain Pedal |
| 65 | Portamento On/Off |
| 71 | Resonance |
| 74 | Cutoff Frequency |

### Note Numbers

| Note Number | Note Name | Frequency (Hz) |
|------------|-----------|----------------|
| 60 | Middle C (C4) | 261.63 |
| 69 | A4 | 440.00 |
| 72 | C5 | 523.25 |

## Installation

```bash
npm install
```

## Usage

### Basic Usage

```javascript
const WebMidiHandler = require('./lib/webMidiHandler');
const SerialMidiHandler = require('./lib/serialMidiHandler');

// Create handler instance
const midi = new WebMidiHandler();

// Initialize and connect
await midi.init();
const devices = midi.listDevices();

// Set up message handler
midi.onMessage((message) => {
    console.log('Received:', message);
});

// Connect to first available device
await midi.connect(0);
```

### Message Types

#### Note Message
```javascript
{
    type: 'noteOn',  // or 'noteOff'
    channel: 0-15,
    note: 0-127,     // 60 = middle C
    velocity: 0-127  // 0 = off, 127 = max
}
```

#### Control Change
```javascript
{
    type: 'controlChange',
    channel: 0-15,
    controller: 0-127,  // CC number
    value: 0-127
}
```

#### Program Change
```javascript
{
    type: 'programChange',
    channel: 0-15,
    program: 0-127
}
```

## MIDI Implementation Details

### Running Status
- When sending multiple messages of the same type on the same channel, the status byte can be omitted after the first message
- Saves bandwidth in high-traffic situations
- Example: Note On sequence
  ```
  90 3C 40  // Note On, note 60, velocity 64
  3E 40     // Note On (same status), note 62, velocity 64
  40 40     // Note On (same status), note 64, velocity 64
  ```

### System Messages

| Message | Hex | Description |
|---------|-----|-------------|
| System Exclusive | F0 | Start of SysEx |
| MIDI Time Code | F1 | Quarter frame |
| Song Position | F2 | Song position pointer |
| Song Select | F3 | Song selection |
| Tune Request | F6 | Tune request |
| End of SysEx | F7 | End of SysEx |
| Timing Clock | F8 | Timing clock (24 ppq) |
| Start | FA | Start sequence |
| Continue | FB | Continue sequence |
| Stop | FC | Stop sequence |
| Active Sensing | FE | Active sensing |
| System Reset | FF | System reset |

## Troubleshooting

### Common Issues

1. **No MIDI Devices Found**
   - Check USB connection
   - Verify device drivers are installed
   - Try different USB port
   - Check if device appears in system MIDI devices

2. **Permission Issues (Linux/Mac)**
   - Add user to `audio` group
   - Check port permissions
   ```bash
   sudo usermod -a -G audio $USER
   ```

3. **WebMIDI Not Working**
   - Check browser compatibility
   - Enable MIDI in browser settings
   - Try Serial MIDI fallback

## Contributing

1. Fork the repository
2. Create your feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

MIT License - feel free to use this code in your projects. 
