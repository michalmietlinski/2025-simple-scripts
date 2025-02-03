import { AppState, CONFIG } from './state/AppState.js';
import { UI } from './ui/UIManager.js';
import { ConnectionHandler } from './handlers/ConnectionHandler.js';
import { ConnectionUIHandler } from './handlers/ConnectionUIHandler.js';
import { ChatUIHandler } from './handlers/ChatUIHandler.js';
import { displayAllConversations, loadConversationHistory, mergeMessages } from './utils/MessageUtils.js';
import { downloadFileFromData } from './utils/FileUtils.js';
import { ApiService } from './services/ApiService.js';

// Message handling
async function handleSendMessage() {
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
}

// Connection management
async function connect() {
    const peerId = document.getElementById('peerId').value.trim();
    if (!peerId || peerId === AppState.user) {
        UI.updateStatus('Invalid peer ID');
        return;
    }
    
    AppState.connection.peerUsername = peerId;
    const conversationId = AppState.messages.getConversationId(AppState.user, peerId);
    if (!conversationId) {
        UI.updateStatus('Invalid conversation setup');
        return;
    }
    
    AppState.connection.currentPeer = conversationId;
    
    try {
        await ConnectionHandler.initialize(peerId);
        await loadConversationHistory(conversationId);
        UI.toggleVisibility('chatPanel', true);
    } catch (error) {
        console.error('Connection failed:', error);
        UI.updateStatus('Failed to establish connection');
    }
}

function copyConnectionInfo() {
    const infoElement = document.getElementById('connectionInfoDisplay');
    infoElement.select();
    document.execCommand('copy');
    const button = document.querySelector('#connectionInfo button');
    const originalText = button.textContent;
    button.textContent = 'Copied!';
    setTimeout(() => button.textContent = originalText, 2000);
}

// Initialize app
document.addEventListener('DOMContentLoaded', () => {
    ChatUIHandler.setupEventListeners();

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
});

// Register user function
window.registerUser = async function(username) {
    if (!username) username = document.getElementById('username').value;
    if (!username) return;

    try {
        const data = await ApiService.post(CONFIG.api.endpoints.register, { username });
        if (data.success) {
            AppState.user = username;
            UI.toggleVisibility('userSetup', false);
            
            // Show conversations panel first
            document.getElementById('userId').textContent = username;
            UI.toggleVisibility('statusPanel', true);
            await displayAllConversations();
            
            // Show connection panel after conversations are loaded
            UI.toggleVisibility('connectionPanel', true);
        }
    } catch (error) {
        console.error('Registration failed:', error);
        UI.updateStatus('Registration failed');
    }
};

// Export window functions
Object.assign(window, {
    connect: ConnectionUIHandler.handleConnect,
    handleOffer: ConnectionHandler.handleOffer.bind(ConnectionHandler),
    sendMessage: ChatUIHandler.handleSendMessage.bind(ChatUIHandler),
    downloadFileFromData,
    copyConnectionInfo: ConnectionUIHandler.handleCopyConnectionInfo
});
