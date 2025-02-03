import { AppState } from './state.js';
import { CONFIG } from './config.js';
import { UI } from './ui.js';
import { ApiService } from './api.js';
import { MessageHandler } from './message.js';
import { ConnectionHandler } from './connection.js';
import { displayAllConversations } from './conversation.js';
import { connect, handleOffer, handleSendMessage } from './main.js';

// Register user function
export async function registerUser(username) {
    if (!username) username = document.getElementById('username').value;
    if (!username) return;

    try {
        const data = await ApiService.post(CONFIG.api.endpoints.register, { username });
        if (data.success) {
            AppState.user = username;
            UI.toggleVisibility('userSetup', false);
            
            // Show conversations panel first
            document.getElementById('userId').textContent = username;
            await displayAllConversations();
            UI.toggleVisibility('statusPanel', true);
            
            // Show connection panel after conversations are loaded
            UI.toggleVisibility('connectionPanel', true);
        }
    } catch (error) {
        console.error('Registration failed:', error);
        UI.updateStatus('Registration failed');
    }
}

// Copy connection info function
export function copyConnectionInfo() {
    const infoElement = document.getElementById('connectionInfoDisplay');
    infoElement.select();
    document.execCommand('copy');
    const button = document.querySelector('#connectionInfo button');
    const originalText = button.textContent;
    button.textContent = 'Copied!';
    setTimeout(() => button.textContent = originalText, 2000);
}

// File download function
export function downloadFileFromData(fileId, data, fileName) {
    try {
        if (!data) {
            UI.updateStatus('File data not available');
            return;
        }

        const link = document.createElement('a');
        link.href = data;
        link.download = fileName;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
    } catch (error) {
        console.error('File download failed:', error);
        UI.updateStatus('Failed to download file');
    }
}

// Assign all exports to window object
Object.assign(window, {
    registerUser,
    connect,
    handleOffer,
    sendMessage: handleSendMessage,
    copyConnectionInfo,
    downloadFileFromData
}); 
