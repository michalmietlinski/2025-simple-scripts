import { UI } from './ui.js';
import { MessageHandler } from './message.js';
import { handleSendMessage } from './main.js';

// Event handlers setup
export function setupEventHandlers() {
    // Update send button onclick
    const sendButton = document.querySelector('#chatControls button');
    if (sendButton) {
        sendButton.onclick = handleSendMessage;
    }

    // Add enter key handler
    UI.elements.messageInput?.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') handleSendMessage();
    });

    // Add file input handler
    const fileInput = document.getElementById('fileInput');
    if (fileInput) {
        fileInput.addEventListener('change', async (e) => {
            const file = e.target.files[0];
            if (file) {
                await MessageHandler.handleFileUpload(file);
            }
            e.target.value = ''; // Reset input
        });
    }

    // Add file button handler
    const fileButton = document.querySelector('.file-button');
    if (fileButton) {
        fileButton.onclick = () => document.getElementById('fileInput').click();
    }
} 
