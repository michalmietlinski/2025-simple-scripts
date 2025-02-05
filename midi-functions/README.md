# MIDI Keyboard Shortcuts

A simple Node.js script for handling MIDI input from my keyboard and converting it to system keyboard shortcuts. Perfect for testing different approaches to MIDI input handling and automation.

## Features

### Keyboard Shortcuts
- **Note 48**: Ctrl+A (Select All)
- **Note 49**: Alt+Shift+C
- **Note 50**: Ctrl+C (Copy)
- **Note 51**: Ctrl+X (Cut)
- **Note 52**: Ctrl+V (Paste)
- **Note 72**: Left Arrow
- **Note 73/75**: Up Arrow
- **Note 74**: Down Arrow
- **Note 76**: Right Arrow
- **Note 77**: Space
- **Note 79**: Enter

## Installation

1. Install Node.js (v20.10.0 or later recommended)
2. Clone this repository
3. Install dependencies:
```bash
npm install
```

## Usage

Start the script:
```bash
npm start
```

The script will:
1. List available MIDI devices
2. Let you select a device (or automatically connect if only one is available)
3. Start listening for MIDI input
4. Convert MIDI notes to keyboard shortcuts

## Requirements
- Node.js
- A MIDI keyboard/controller
- Windows 10 (tested on 10.0.19045)

## Dependencies
- midi: ^2.0.0 (for MIDI device handling)
- robotjs: ^0.6.0 (for keyboard simulation)
- readline: ^1.3.0 (for device selection)

## Attempted Approaches & Limitations

### Device Discovery & Connection
Several approaches were tried for MIDI device handling:

1. **WebMIDI API**
   - Required browser environment
   - Limited access to raw MIDI data
   - Not suitable for system-wide control

2. **Serial Port Communication**
   - Complex protocol implementation needed
   - Inconsistent device enumeration
   - Required different handling for each device type

3. **USB Direct Communication**
   - Required low-level USB access
   - Device-specific protocols needed
   - Permissions issues on Windows

4. **node-midi Library**
   - Finally worked reliably
   - Simple API for device discovery
   - Consistent behavior across devices

### Volume Control
Several approaches were tried for controlling system volume but none worked reliably:

1. **node-audio-windows**
   - Required node-gyp which failed to install
   - Complex setup requirements
   - Not maintained for newer Node.js versions

2. **win-audio**
   - Build failed due to native dependencies
   - Required specific Windows SDK versions
   - Installation issues with Node.js v20

3. **PowerShell Commands**
   - Inconsistent behavior with external audio interfaces
   - Slow response time
   - Required elevated privileges

4. **nircmd**
   - Required external software installation
   - Limited support for modern audio devices
   - Not reliable with external audio interfaces

### GUI Feedback
Electron-based GUI was removed because:
- Overcomplicated the simple script
- Added heavy dependencies
- Not necessary for basic functionality

## Current Implementation
- Uses node-midi for reliable device discovery
- Simple device selection interface
- Automatic connection to single devices
- Handles device disconnection gracefully
- Works with both USB and traditional MIDI ports

## Notes
- Currently supports basic keyboard shortcuts and arrow keys
- Designed for personal use and testing different MIDI input approaches
- Easy to extend with new shortcuts via config.json

## Future Ideas
- Add support for more keyboard shortcuts
- Implement different types of actions
- Add support for MIDI velocity
- Add support for multiple MIDI devices 
