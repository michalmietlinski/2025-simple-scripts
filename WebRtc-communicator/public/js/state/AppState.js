export const AppState = {
    user: null,
    connection: {
        rtc: null,
        dataChannel: null,
        peerUsername: null,
        currentPeer: null
    },
    messages: {
        offline: new Map(),
        getConversationId: (user1, user2) => {
            if (!user1 || !user2) return null;
            return [user1, user2].sort().join('-');
        },
        generateId: () => crypto.randomUUID(),
        pendingSync: new Set()
    },
    async loadConversation(peerId) {
        try {
            const conversationId = this.messages.getConversationId(this.user, peerId);
            const response = await ApiService.get(CONFIG.api.endpoints.getConversation(this.user, conversationId));
            
            if (response.success) {
                UI.elements.messagesContainer.innerHTML = '';
                response.messages.forEach(msg => {
                    if (msg.type === 'file_share') {
                        MessageHandler.addFileMessage(msg.file || {
                            name: msg.fileName,
                            size: msg.fileSize,
                            path: msg.filePath
                        }, msg.sender);
                    } else {
                        MessageHandler.addToChat(msg.message, msg.sender, false);
                    }
                });
                await MessageHandler.refreshFilesList();
            }
        } catch (error) {
            console.error('Error loading conversation:', error);
            UI.updateStatus('Failed to load conversation');
        }
    }
};

export const CONFIG = {
    rtc: {
        iceServers: [{ urls: 'stun:stun.l.google.com:19302' }]
    },
    api: {
        base: '/api',
        endpoints: {
            register: '/user/register',
            saveChatMessage: '/conversation/save',
            getConversation: (username, peerId) => `/conversation/${username}/${peerId}`,
            getAllConversations: (username) => `/conversations/${username}`,
            uploadFile: (username, conversationId) => `/files/${username}/${conversationId}/upload`,
            downloadFile: (username, conversationId, filename) => `/files/${username}/${conversationId}/download/${filename}`
        }
    }
};

async function loadConversation(peerId) {
    try {
        const conversationId = AppState.messages.getConversationId(AppState.user, peerId);
        const response = await ApiService.get(CONFIG.api.endpoints.getConversation(AppState.user, conversationId));
        
        if (response.success) {
            UI.elements.messagesContainer.innerHTML = '';
            response.messages.forEach(msg => {
                if (msg.type === 'file_share') {
                    MessageHandler.addFileMessage(msg.file || {
                        name: msg.fileName,
                        size: msg.fileSize,
                        path: msg.filePath
                    }, msg.sender);
                } else {
                    MessageHandler.addToChat(msg.message, msg.sender, false);
                }
            });
            await MessageHandler.refreshFilesList();
        }
    } catch (error) {
        console.error('Error loading conversation:', error);
        UI.updateStatus('Failed to load conversation');
    }
} 
