class MidiParser {
    // MIDI Status Bytes (first byte in MIDI message)
    static STATUS = {
        NOTE_OFF: 0x80,
        NOTE_ON: 0x90,
        POLY_AFTERTOUCH: 0xA0,
        CONTROL_CHANGE: 0xB0,
        PROGRAM_CHANGE: 0xC0,
        CHANNEL_AFTERTOUCH: 0xD0,
        PITCH_BEND: 0xE0,
        SYSTEM: 0xF0
    };

    constructor() {
        this.buffer = []; // Store incomplete MIDI messages
    }

    parseMessage(byte) {
        // Add byte to buffer
        this.buffer.push(byte);

        // Check if we have a complete message
        if (this.isCompleteMessage()) {
            const message = this.processMessage();
            this.buffer = []; // Clear buffer
            return message;
        }
        return null;
    }

    isCompleteMessage() {
        if (this.buffer.length === 0) return false;

        const status = this.buffer[0] & 0xF0; // Get status byte without channel
        
        // Different message types have different lengths
        switch(status) {
            case MidiParser.STATUS.NOTE_OFF:
            case MidiParser.STATUS.NOTE_ON:
            case MidiParser.STATUS.POLY_AFTERTOUCH:
            case MidiParser.STATUS.CONTROL_CHANGE:
            case MidiParser.STATUS.PITCH_BEND:
                return this.buffer.length >= 3;
            case MidiParser.STATUS.PROGRAM_CHANGE:
            case MidiParser.STATUS.CHANNEL_AFTERTOUCH:
                return this.buffer.length >= 2;
            default:
                return false;
        }
    }

    processMessage() {
        const status = this.buffer[0] & 0xF0; // Get status byte without channel
        const channel = this.buffer[0] & 0x0F; // Get channel number

        switch(status) {
            case MidiParser.STATUS.NOTE_ON:
                return {
                    type: 'noteOn',
                    channel: channel,
                    note: this.buffer[1],
                    velocity: this.buffer[2]
                };
            case MidiParser.STATUS.NOTE_OFF:
                return {
                    type: 'noteOff',
                    channel: channel,
                    note: this.buffer[1],
                    velocity: this.buffer[2]
                };
            case MidiParser.STATUS.CONTROL_CHANGE:
                return {
                    type: 'controlChange',
                    channel: channel,
                    controller: this.buffer[1],
                    value: this.buffer[2]
                };
            // Add more message types as needed
            default:
                return {
                    type: 'unknown',
                    data: this.buffer
                };
        }
    }
}

module.exports = MidiParser; 
