import { AppState } from './state.js';
import { CONFIG } from './config.js';
import { UI } from './ui.js';
import { ApiService } from './api.js';

// Message handling
export const MessageHandler = {
    sentMessages: new Set(),
    
    getMessageId(msg) {
        return msg.id || this.getMessageHash(msg);
    },

    getMessageHash(msg) {
        return `${msg.sender}-${msg.timestamp}-${msg.message}`;
    },

    async save(peerId, messageData, overwrite = false) {
        try {
            if (!AppState.user || !AppState.connection.peerUsername) {
                throw new Error('Invalid user or peer information');
            }

            const conversationId = AppState.messages.getConversationId(
                AppState.user, 
                AppState.connection.peerUsername
            );

            if (!conversationId) {
                throw new Error('Invalid conversation ID');
            }

            // If not overwriting, check if we've already handled this message
            if (!overwrite) {
                const messageId = this.getMessageId(messageData);
                if (this.sentMessages.has(messageId)) {
                    return; // Skip if already handled
                }
                this.sentMessages.add(messageId);
            }
            
            // Ensure message has an ID
            if (!messageData.id) {
                messageData.id = AppState.messages.generateId();
            }

            const result = await ApiService.post(CONFIG.api.endpoints.saveChatMessage, {
                username: AppState.user,
                peerId: conversationId,
                data: messageData,
                overwrite
            });
            
            if (!result.success) {
                throw new Error('Failed to save conversation');
            }
        } catch (error) {
            console.error('Error saving conversation:', error);
            UI.updateStatus('Failed to save message');
        }
    },

    async addToChat(message, sender, shouldSave = true) {
        const timestamp = Date.now();
        const messageData = {
            id: AppState.messages.generateId(),
            sender,
            message,
            timestamp
        };

        // Skip if we've already handled this message
        const messageId = this.getMessageId(messageData);
        if (this.sentMessages.has(messageId)) {
            return;
        }

        const messageElement = document.createElement('div');
        messageElement.className = `message ${sender === AppState.user ? 'sent' : 'received'}`;
        messageElement.textContent = `${sender}: ${message}`;
        UI.elements.messagesContainer.appendChild(messageElement);
        UI.elements.messagesContainer.scrollTop = UI.elements.messagesContainer.scrollHeight;

        this.sentMessages.add(messageId);

        if (shouldSave) {
            await this.save(AppState.connection.currentPeer, messageData);
        }
    },

    async handleFileUpload(file) {
        try {
            const reader = new FileReader();
            reader.onload = async (e) => {
                const fileData = {
                    type: 'file_share',
                    sender: AppState.user,
                    file: {
                        name: file.name,
                        type: file.type,
                        size: file.size,
                        data: e.target.result,
                        id: AppState.messages.generateId()
                    },
                    timestamp: Date.now()
                };

                // Save file reference in conversation
                await this.save(AppState.connection.currentPeer, {
                    type: 'file_share',
                    sender: AppState.user,
                    fileName: file.name,
                    fileSize: file.size,
                    fileId: fileData.file.id,
                    timestamp: fileData.timestamp
                });

                // Add file UI elements
                await this.addToChat(`Shared file: ${file.name}`, AppState.user, false);
                this.addFileMessage(fileData.file, AppState.user);

                // Send file through WebRTC
                if (AppState.connection.dataChannel?.readyState === 'open') {
                    AppState.connection.dataChannel.send(JSON.stringify(fileData));
                }
            };
            reader.readAsDataURL(file);
        } catch (error) {
            console.error('File handling failed:', error);
            UI.updateStatus('Failed to process file');
        }
    },

    addFileMessage(fileInfo, sender) {
        // Add file share message to chat history
        const messageElement = document.createElement('div');
        messageElement.className = `message system`;
        messageElement.textContent = `${sender} shared file: ${fileInfo.name}`;
        UI.elements.messagesContainer.appendChild(messageElement);

        // Add file download element
        const fileElement = document.createElement('div');
        fileElement.className = `message file ${sender === AppState.user ? 'sent' : 'received'}`;
        fileElement.innerHTML = `
            <div class="file-info">
                <span>📎 ${fileInfo.name} (${this.formatFileSize(fileInfo.size)})</span>
                <button class="file-download" onclick="downloadFileFromData('${fileInfo.id}', '${fileInfo.data || ''}', '${fileInfo.name}')">
                    Download
                </button>
            </div>
        `;
        
        UI.elements.messagesContainer.appendChild(fileElement);
        UI.elements.messagesContainer.scrollTop = UI.elements.messagesContainer.scrollHeight;
    },

    formatFileSize(bytes) {
        if (bytes < 1024) return bytes + ' B';
        if (bytes < 1048576) return (bytes / 1024).toFixed(1) + ' KB';
        return (bytes / 1048576).toFixed(1) + ' MB';
    }
};

// Message sending functionality
export async function handleSendMessage() {
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
