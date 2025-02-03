import { handleSendMessage } from './message.js';
import { connect, handleOffer } from './connection.js';
import { setupEventHandlers } from './events.js';
import './exports.js';

export { handleSendMessage, connect, handleOffer };

// Initialize app
document.addEventListener('DOMContentLoaded', setupEventHandlers);
