import { AppState } from '../state/AppState.js';
import { UI } from '../ui/UIManager.js';
import { ConnectionHandler } from './ConnectionHandler.js';
import { loadConversationHistory } from '../utils/MessageUtils.js';

export const ConnectionUIHandler = {
    async handleConnect() {
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
    },

    handleCopyConnectionInfo() {
        const infoElement = document.getElementById('connectionInfoDisplay');
        infoElement.select();
        document.execCommand('copy');
        const button = document.querySelector('#connectionInfo button');
        const originalText = button.textContent;
        button.textContent = 'Copied!';
        setTimeout(() => button.textContent = originalText, 2000);
    }
}; 
