import { AppState, CONFIG } from '../state/AppState.js';
import { UI } from '../ui/UIManager.js';
import { ApiService } from '../services/ApiService.js';

export const MessageHandler = {
    sentMessages: new Set(),
    
    getMessageId(msg) {
        return msg.id || this.getMessageHash(msg);
    },

    getMessageHash(msg) {
        if (msg.type === 'file_share') {
            return `${msg.sender}-${msg.timestamp}-${msg.fileName}`;
        }
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

            const messageHash = this.getMessageHash(messageData);
            if (!overwrite && this.sentMessages.has(messageHash)) {
                return;
            }
            this.sentMessages.add(messageHash);
            
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
            timestamp,
            synced: !!AppState.connection.dataChannel?.readyState === 'open'
        };

        const messageElement = document.createElement('div');
        messageElement.className = `message ${sender === AppState.user ? 'sent' : 'received'}`;
        messageElement.setAttribute('data-message-id', messageData.id);
        messageElement.innerHTML = `
            ${sender}: ${message}
            ${!messageData.synced ? '<span class="pending-sync">⌛</span>' : ''}
        `;
        UI.elements.messagesContainer.appendChild(messageElement);
        UI.elements.messagesContainer.scrollTop = UI.elements.messagesContainer.scrollHeight;

        if (shouldSave) {
            await this.save(AppState.connection.currentPeer, messageData);
            
            if (!messageData.synced) {
                AppState.messages.pendingSync.add(AppState.connection.currentPeer);
                this.updateConversationStatus(AppState.connection.currentPeer);
            }
        }

        return messageData;
    },

    async markMessageAsSynced(messageId) {
        const messageElement = document.querySelector(`[data-message-id="${messageId}"]`);
        if (messageElement) {
            const syncIcon = messageElement.querySelector('.pending-sync');
            if (syncIcon) {
                syncIcon.remove();
            }
        }

        // Update message in storage
        const conversationId = AppState.messages.getConversationId(
            AppState.user,
            AppState.connection.currentPeer || AppState.connection.peerUsername
        );

        if (!conversationId) return;

        try {
            const response = await ApiService.get(CONFIG.api.endpoints.getConversation(AppState.user, conversationId));
            if (response.success) {
                const messages = response.messages.map(msg => {
                    if (msg.id === messageId) {
                        return { ...msg, synced: true };
                    }
                    return msg;
                });

                await ApiService.post(CONFIG.api.endpoints.saveChatMessage, {
                    username: AppState.user,
                    peerId: conversationId,
                    data: messages,
                    overwrite: true
                });

                // Remove from pending sync if no more unsynced messages
                const hasUnsynced = messages.some(msg => !msg.synced);
                if (!hasUnsynced) {
                    AppState.messages.pendingSync.delete(conversationId);
                    this.updateConversationStatus(conversationId);
                }
            }
        } catch (error) {
            console.error('Error updating message sync status:', error);
        }
    },

    async handleMessageSync(messageData) {
        if (messageData.type === 'message_ack') {
            await this.markMessageAsSynced(messageData.messageId);
            return;
        }

        // For received messages, send acknowledgment
        const ack = {
            type: 'message_ack',
            messageId: messageData.id,
            sender: AppState.user
        };

        if (AppState.connection.dataChannel?.readyState === 'open') {
            AppState.connection.dataChannel.send(JSON.stringify(ack));
        }

        // Check if we already have this message
        const messageHash = this.getMessageHash(messageData);
        if (this.sentMessages.has(messageHash)) {
            return;
        }

        // Save received message as already synced
        await this.save(AppState.connection.currentPeer, {
            ...messageData,
            synced: true
        });
    },

    async handleFileUpload(file) {
        try {
            const formData = new FormData();
            formData.append('file', file);
            formData.append('sender', AppState.user);

            const response = await fetch(
                `${CONFIG.api.base}${CONFIG.api.endpoints.uploadFile(AppState.user, AppState.connection.currentPeer)}`,
                {
                    method: 'POST',
                    body: formData
                }
            );
            const result = await response.json();

            if (!result.success) {
                throw new Error('Failed to upload file');
            }

            const fileData = {
                type: 'file_share',
                sender: AppState.user,
                file: result.file,
                timestamp: Date.now(),
                id: AppState.messages.generateId(),
                fileName: file.name,
                fileSize: file.size,
                fileId: result.file.id,
                filePath: result.file.path,
                synced: !!AppState.connection.dataChannel?.readyState === 'open'
            };

            // Save message once
            await this.save(AppState.connection.currentPeer, fileData);

            // Update UI
            await this.addToChat(`Shared file: ${file.name}`, AppState.user, false);
            await this.addFileMessage(result.file, AppState.user, false);

            // Send to peer if connected
            if (AppState.connection.dataChannel?.readyState === 'open') {
                AppState.connection.dataChannel.send(JSON.stringify(fileData));
            }
        } catch (error) {
            console.error('File handling failed:', error);
            UI.updateStatus('Failed to process file');
        }
    },

    async addFileMessage(fileInfo, sender, shouldSave = true) {
        const messageElement = document.createElement('div');
        messageElement.className = `message system`;
        messageElement.textContent = `${sender} shared file: ${fileInfo.name}`;
        UI.elements.messagesContainer.appendChild(messageElement);

        const fileElement = document.createElement('div');
        fileElement.className = `message file ${sender === AppState.user ? 'sent' : 'received'}`;
        
        const conversationId = AppState.messages.getConversationId(AppState.user, AppState.connection.peerUsername);
        const fileName = fileInfo.filePath || fileInfo.path || fileInfo.name;
        const downloadUrl = `${CONFIG.api.base}${CONFIG.api.endpoints.downloadFile(sender, conversationId, fileName)}`;
        
        fileElement.innerHTML = `
            <div class="file-info">
                <span>📎 ${fileInfo.name} (${this.formatFileSize(fileInfo.size)})</span>
                <a href="${downloadUrl}" class="file-download" target="_blank">
                    Download
                </a>
            </div>
        `;
        
        UI.elements.messagesContainer.appendChild(fileElement);
        UI.elements.messagesContainer.scrollTop = UI.elements.messagesContainer.scrollHeight;
        
        // Update files list
        await this.refreshFilesList();
    },

    async refreshFilesList() {
        const filesList = document.getElementById('files-list');
        if (!filesList) return;

        try {
            const conversationId = AppState.messages.getConversationId(
                AppState.user, 
                AppState.connection.currentPeer || AppState.connection.peerUsername
            );
            
            if (!conversationId) {
                filesList.innerHTML = '<div class="error">No active conversation</div>';
                return;
            }

            const response = await fetch(`${CONFIG.api.base}/files/${AppState.user}/${conversationId}/list`);
            const data = await response.json();

            if (!data.success) throw new Error('Failed to load files');

            filesList.innerHTML = '';
            data.files.forEach(file => {
                const fileItem = document.createElement('div');
                fileItem.className = 'file-item';
                const downloadUrl = `${CONFIG.api.base}${CONFIG.api.endpoints.downloadFile(file.sender, conversationId, file.path)}`;
                
                fileItem.innerHTML = `
                    <span class="file-name">${file.name}</span>
                    <a href="${downloadUrl}" target="_blank" title="Download ${file.name}">⬇️</a>
                `;
                filesList.appendChild(fileItem);
            });

            if (data.files.length === 0) {
                filesList.innerHTML = '<div style="padding: 10px; color: #666;">No files shared yet</div>';
            }
        } catch (error) {
            console.error('Error loading files:', error);
            filesList.innerHTML = '<div class="error" style="padding: 10px; color: #f44336;">Failed to load files: ' + error.message + '</div>';
        }
    },

    formatFileSize(bytes) {
        if (bytes < 1024) return bytes + ' B';
        if (bytes < 1048576) return (bytes / 1024).toFixed(1) + ' KB';
        return (bytes / 1048576).toFixed(1) + ' MB';
    },

    updateConversationStatus(conversationId) {
        const conversationElement = document.querySelector(`[data-conversation-id="${conversationId}"]`);
        if (conversationElement) {
            const statusElement = conversationElement.querySelector('.sync-status');
            if (statusElement) {
                statusElement.textContent = AppState.messages.pendingSync.has(conversationId) ? 
                    '⌛ Pending sync' : '✓ Synced';
            }
        }
    }
}; 
