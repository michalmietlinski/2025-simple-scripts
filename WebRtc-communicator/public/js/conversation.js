import { AppState } from './state.js';
import { CONFIG } from './config.js';
import { UI } from './ui.js';
import { ApiService } from './api.js';
import { MessageHandler } from './message.js';
import { ErrorUtils } from './utils.js';

// Helper function to get message signature for deduplication
function getMessageSignature(msg) {
    if (msg.type === 'file_share') {
        return `${msg.timestamp}-${msg.fileName}`;
    }
    return `${msg.timestamp}-${msg.message || msg.content}`;
}

// Helper function to clean up duplicates
function removeDuplicateMessages(messages) {
    const uniqueMessages = new Map();
    const signatures = new Set();

    messages.forEach(msg => {
        const signature = getMessageSignature(msg);
        if (!signatures.has(signature)) {
            signatures.add(signature);
            uniqueMessages.set(signature, msg);
        }
    });

    return Array.from(uniqueMessages.values())
        .sort((a, b) => a.timestamp - b.timestamp);
}

export async function loadConversationHistory(peerId) {
    try {
        const conversationId = AppState.messages.getConversationId(AppState.user, AppState.connection.peerUsername);
        const response = await ApiService.get(CONFIG.api.endpoints.getConversation(AppState.user, conversationId));
        
        if (response.success && response.messages) {
            // Clean up duplicates before displaying
            const cleanMessages = removeDuplicateMessages(response.messages);
            
            // Save cleaned up messages if we removed any duplicates
            if (cleanMessages.length < response.messages.length) {
                await MessageHandler.save(conversationId, cleanMessages, true);
            }

            UI.elements.messagesContainer.innerHTML = '';
            MessageHandler.sentMessages.clear();
            
            cleanMessages.forEach(msg => {
                const messageId = MessageHandler.getMessageId(msg);
                MessageHandler.sentMessages.add(messageId);
                
                // Handle file messages differently
                if (msg.type === 'file_share') {
                    MessageHandler.addToChat(`Shared file: ${msg.fileName}`, msg.sender, false);
                    MessageHandler.addFileMessage({
                        name: msg.fileName,
                        path: msg.fileId,
                        size: msg.fileSize
                    }, msg.sender);
                } else {
                    MessageHandler.addToChat(msg.message, msg.sender, false);
                }
            });
        }
    } catch (error) {
        const { message } = ErrorUtils.handleError(error, 'loadConversationHistory', 'Failed to load conversation');
        UI.updateStatus(message);
    }
}

export async function displayAllConversations() {
    try {
        const response = await ApiService.get(CONFIG.api.endpoints.getAllConversations(AppState.user));
        if (!response.success) return;

        const container = UI.elements.conversationsContainer;
        container.innerHTML = '';
        
        const conversations = Object.entries(response.conversations);
        
        if (conversations.length === 0) {
            container.innerHTML = '<div class="no-conversations">No conversations yet. Start a new one!</div>';
            return;
        }
        
        conversations.forEach(([peerId, messages]) => {
            if (!peerId.includes('-')) return;
            
            const peerNames = peerId.split('-');
            const otherUser = peerNames.find(name => name !== AppState.user);
            if (!otherUser) return;
            
            const lastMessage = messages[messages.length - 1];
            const conversationDiv = document.createElement('div');
            conversationDiv.className = 'conversation-item';
            
            const lastMessagePreview = lastMessage ? 
                `<p class="last-message">${lastMessage.sender}: ${lastMessage.message}</p>` : '';
            
            conversationDiv.innerHTML = `
                <div class="conversation-header">
                    <h5>${otherUser}</h5>
                    <small>${messages.length} messages</small>
                </div>
                ${lastMessagePreview}
            `;
            
            conversationDiv.onclick = async () => {
                // Highlight selected conversation
                document.querySelectorAll('.conversation-item').forEach(item => {
                    item.classList.remove('selected');
                });
                conversationDiv.classList.add('selected');
                
                AppState.connection.currentPeer = peerId;
                AppState.connection.peerUsername = otherUser;
                await loadConversationHistory(peerId);
                UI.toggleVisibility('chatPanel', true);
                document.getElementById('peerId').value = otherUser;
            };
            
            container.appendChild(conversationDiv);
        });
    } catch (error) {
        console.error('Error loading conversations:', error);
        UI.updateStatus('Failed to load conversations');
    }
}

export async function mergeMessages(remoteMessages) {
    try {
        const response = await ApiService.get(
            CONFIG.api.endpoints.getConversation(AppState.user, AppState.connection.currentPeer)
        );
        const localMessages = response.success ? response.messages : [];

        // Clean up duplicates in both local and remote messages first
        const cleanLocalMessages = removeDuplicateMessages(localMessages);
        const cleanRemoteMessages = removeDuplicateMessages(remoteMessages);

        // Merge cleaned messages
        const uniqueMessages = new Map();
        const signatures = new Set();
        
        [...cleanLocalMessages, ...cleanRemoteMessages].forEach(msg => {
            const signature = getMessageSignature(msg);
            if (!signatures.has(signature)) {
                signatures.add(signature);
                uniqueMessages.set(signature, msg);
            }
        });

        const mergedMessages = Array.from(uniqueMessages.values())
            .sort((a, b) => a.timestamp - b.timestamp);

        // Save if we have new messages or removed duplicates
        if (mergedMessages.length !== localMessages.length) {
            await MessageHandler.save(AppState.connection.currentPeer, mergedMessages, true);
        }
        
        // Clear and reload the chat
        UI.elements.messagesContainer.innerHTML = '';
        MessageHandler.sentMessages.clear();
        
        mergedMessages.forEach(msg => {
            const messageId = MessageHandler.getMessageId(msg);
            MessageHandler.sentMessages.add(messageId);
            if (msg.type === 'file_share') {
                MessageHandler.addToChat(`Shared file: ${msg.fileName}`, msg.sender, false);
                MessageHandler.addFileMessage({
                    name: msg.fileName,
                    path: msg.fileId,
                    size: msg.fileSize
                }, msg.sender);
            } else {
                MessageHandler.addToChat(msg.message || msg.content, msg.sender, false);
            }
        });
    } catch (error) {
        const { message } = ErrorUtils.handleError(error, 'mergeMessages', 'Failed to sync messages');
        UI.updateStatus(message);
    }
} 
