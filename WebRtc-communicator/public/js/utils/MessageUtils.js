import { AppState, CONFIG } from '../state/AppState.js';
import { UI } from '../ui/UIManager.js';
import { MessageHandler } from '../handlers/MessageHandler.js';
import { ApiService } from '../services/ApiService.js';

export async function mergeMessages(remoteMessages) {
    try {
        const localMessages = await ApiService.get(
            CONFIG.api.endpoints.getConversation(AppState.user, AppState.connection.currentPeer)
        );
        
        if (!localMessages.success) {
            throw new Error('Failed to fetch local messages');
        }

        // Create a map to deduplicate messages
        const uniqueMessages = new Map();
        
        // Add local messages to map
        (localMessages.messages || []).forEach(msg => {
            const messageId = msg.id || MessageHandler.getMessageId(msg);
            uniqueMessages.set(messageId, msg);
        });
        
        // Add remote messages, overwriting local ones if they exist
        remoteMessages.forEach(msg => {
            const messageId = msg.id || MessageHandler.getMessageId(msg);
            uniqueMessages.set(messageId, msg);
        });
        
        // Convert back to array and sort
        const mergedMessages = Array.from(uniqueMessages.values())
            .sort((a, b) => a.timestamp - b.timestamp);

        // Clear and reload the chat
        UI.elements.messagesContainer.innerHTML = '';
        MessageHandler.sentMessages.clear();
        
        // Remove from pending sync
        AppState.messages.pendingSync.delete(AppState.connection.currentPeer);
        MessageHandler.updateConversationStatus(AppState.connection.currentPeer);
        
        mergedMessages.forEach(msg => {
            const messageId = msg.id || MessageHandler.getMessageId(msg);
            MessageHandler.sentMessages.add(messageId);
            
            if (msg.type === 'file_share') {
                MessageHandler.addToChat(`Shared file: ${msg.fileName}`, msg.sender, false);
                MessageHandler.addFileMessage({
                    name: msg.fileName,
                    path: msg.filePath,
                    size: msg.fileSize,
                    id: msg.fileId
                }, msg.sender);
            } else {
                MessageHandler.addToChat(msg.message, msg.sender, false);
            }
        });
        
        // Update sync status for all messages
        const pendingElements = document.querySelectorAll('.pending-sync');
        pendingElements.forEach(el => el.remove());
        
        // Save the deduplicated messages back to server
        await ApiService.post(CONFIG.api.endpoints.saveChatMessage, {
            username: AppState.user,
            peerId: AppState.connection.currentPeer,
            data: mergedMessages,
            overwrite: true
        });
    } catch (error) {
        console.error('Error merging messages:', error);
        UI.updateStatus('Failed to sync messages');
    }
}

export async function loadConversationHistory(peerId) {
    try {
        const conversationId = AppState.messages.getConversationId(AppState.user, AppState.connection.peerUsername);
        const response = await ApiService.get(CONFIG.api.endpoints.getConversation(AppState.user, conversationId));
        
        if (response.success && response.messages) {
            UI.elements.messagesContainer.innerHTML = '';
            MessageHandler.sentMessages.clear();
            
            response.messages.forEach(msg => {
                const messageId = MessageHandler.getMessageId(msg);
                MessageHandler.sentMessages.add(messageId);
                
                // Handle file messages differently
                if (msg.type === 'file_share') {
                    MessageHandler.addToChat(`Shared file: ${msg.fileName}`, msg.sender, false);
                    MessageHandler.addFileMessage({
                        name: msg.fileName,
                        path: msg.filePath,
                        size: msg.fileSize,
                        id: msg.fileId
                    }, msg.sender);
                } else {
                    MessageHandler.addToChat(msg.message, msg.sender, false);
                }
            });
        }
    } catch (error) {
        console.error('Error loading conversation:', error);
        UI.updateStatus('Failed to load conversation');
    }
}

export async function displayAllConversations() {
    try {
        const response = await ApiService.get(CONFIG.api.endpoints.getAllConversations(AppState.user));
        if (response.success) {
            UI.elements.conversationsContainer.innerHTML = '';
            Object.entries(response.conversations).forEach(([id, messages]) => {
                const peer = id.split('-').find(user => user !== AppState.user);
                const conversationElement = document.createElement('div');
                conversationElement.className = 'conversation-item';
                conversationElement.setAttribute('data-conversation-id', id);
                
                // Only show pending sync if there are actually pending messages
                const hasPendingSync = AppState.messages.pendingSync.has(id) && 
                                     AppState.messages.offline.has(id) &&
                                     AppState.messages.offline.get(id).length > 0;
                
                conversationElement.innerHTML = `
                    <span>${peer}</span>
                    <span class="sync-status">${hasPendingSync ? '⌛ Pending sync' : '✓ Synced'}</span>
                `;
                
                // Add click handler
                conversationElement.addEventListener('click', async () => {
                    AppState.connection.currentPeer = id;
                    AppState.connection.peerUsername = peer;
                    await loadConversationHistory(id);
                    UI.toggleVisibility('chatPanel', true);
                });
                
                UI.elements.conversationsContainer.appendChild(conversationElement);
            });
        }
    } catch (error) {
        console.error('Error loading conversations:', error);
        UI.updateStatus('Failed to load conversations');
    }
} 
