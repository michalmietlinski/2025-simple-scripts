import { AppState } from '../state/AppState.js';
import { UI } from '../ui/UIManager.js';
import { MessageHandler } from './MessageHandler.js';

export const ChatUIHandler = {
    async handleSendMessage() {
        const message = UI.elements.messageInput.value.trim();
        if (!message || !AppState.connection.currentPeer) return;

        const timestamp = Date.now();
        const messageData = {
            type: 'message',
            content: message,
            sender: AppState.user,
            timestamp
        };

        // Save message locally first
        await MessageHandler.save(AppState.connection.currentPeer, {
            sender: AppState.user,
            message,
            timestamp
        });

        MessageHandler.addToChat(message, AppState.user, false);
        UI.clearInput(UI.elements.messageInput);

        // Try to send message
        try {
            if (AppState.connection.dataChannel?.readyState === 'open') {
                AppState.connection.dataChannel.send(JSON.stringify(messageData));
            } else {
                const offlineMessages = AppState.messages.offline;
                if (!offlineMessages.has(AppState.connection.currentPeer)) {
                    offlineMessages.set(AppState.connection.currentPeer, []);
                }
                offlineMessages.get(AppState.connection.currentPeer).push(messageData);
                UI.updateStatus('Message saved (offline)');
            }
        } catch (error) {
            console.error('Error sending message:', error);
            UI.updateStatus('Failed to send message');
        }
    },

    async handleFileSelect(event) {
        const file = event.target.files[0];
        if (file) {
            await MessageHandler.handleFileUpload(file);
        }
        event.target.value = ''; // Reset input
    },

    setupEventListeners() {
        // Send button
        const sendButton = document.querySelector('#chatControls button');
        if (sendButton) {
            sendButton.onclick = this.handleSendMessage;
        }

        // Enter key handler
        UI.elements.messageInput?.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') this.handleSendMessage();
        });

        // File input handler
        const fileInput = document.getElementById('fileInput');
        if (fileInput) {
            fileInput.addEventListener('change', this.handleFileSelect);
        }

        // File button handler
        const fileButton = document.querySelector('.file-button');
        if (fileButton) {
            fileButton.onclick = () => document.getElementById('fileInput').click();
        }
    }
}; 
