// State management
const AppState = {
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
        }
    }
};

// Configuration
const CONFIG = {
    rtc: {
        iceServers: [{ urls: 'stun:stun.l.google.com:19302' }]
    },
    api: {
        base: '/api',
        endpoints: {
            register: '/user/register',
            saveChatMessage: '/conversation/save',
            getConversation: (username, peerId) => `/conversation/${username}/${peerId}`,
            getAllConversations: (username) => `/conversations/${username}`
        }
    }
};

// UI Helper functions
const UI = {
    elements: {
        get messageInput() { return document.getElementById('messageInput') },
        get messagesContainer() { return document.getElementById('messages') },
        get connectionStatus() { return document.querySelector('#connectionStatus span') },
        get conversationsContainer() { return document.getElementById('conversationsContainer') }
    },
    
    toggleVisibility: (elementId, show) => {
        document.getElementById(elementId).classList.toggle('hidden', !show);
    },
    
    updateStatus: (status) => {
        UI.elements.connectionStatus.textContent = status;
    },
    
    clearInput: (element) => {
        element.value = '';
    }
};

// API Service
const ApiService = {
    async post(endpoint, data) {
        try {
            const response = await fetch(`${CONFIG.api.base}${endpoint}`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(data)
            });
            return await response.json();
        } catch (error) {
            console.error(`API Error (${endpoint}):`, error);
            throw error;
        }
    },

    async get(endpoint) {
        try {
            const response = await fetch(`${CONFIG.api.base}${endpoint}`);
            return await response.json();
        } catch (error) {
            console.error(`API Error (${endpoint}):`, error);
            throw error;
        }
    }
};

// Message handling
const MessageHandler = {
    sentMessages: new Set(), // Track message IDs we've already handled

    getMessageId(msg) {
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

    addToChat(message, sender, shouldSave = true) {
        const messageElement = document.createElement('div');
        messageElement.className = `message ${sender === AppState.user ? 'sent' : 'received'}`;
        messageElement.textContent = `${sender}: ${message}`;
        UI.elements.messagesContainer.appendChild(messageElement);
        UI.elements.messagesContainer.scrollTop = UI.elements.messagesContainer.scrollHeight;

        if (shouldSave) {
            const messageData = {
                sender,
                message,
                timestamp: Date.now()
            };
            this.save(AppState.connection.currentPeer, messageData);
        }
    }
};

// Connection handling
const ConnectionHandler = {
    async initialize(peerId) {
        try {
            AppState.connection.rtc = new RTCPeerConnection(CONFIG.rtc);
            AppState.connection.dataChannel = AppState.connection.rtc.createDataChannel('messageChannel');
            
            setupDataChannelHandlers(AppState.connection.dataChannel);
            await this.setupIceHandling();
            
            const offer = await AppState.connection.rtc.createOffer();
            await AppState.connection.rtc.setLocalDescription(offer);
            UI.updateStatus('Gathering connection info...');
        } catch (error) {
            console.error('Connection initialization failed:', error);
            UI.updateStatus('Connection failed');
        }
    },

    async setupIceHandling() {
        const iceCandidates = [];
        AppState.connection.rtc.onicecandidate = event => {
            if (event.candidate) {
                iceCandidates.push(event.candidate);
            } else {
                this.createFullOffer(iceCandidates);
            }
        };
    },

    async createFullOffer(iceCandidates) {
        try {
            const offer = AppState.connection.rtc.localDescription;
            const fullOffer = {
                type: offer.type,
                sdp: offer.sdp,
                iceCandidates,
                userId: AppState.user,
                peerId: AppState.connection.peerUsername
            };
            
            document.getElementById('connectionInfoDisplay').value = JSON.stringify(fullOffer);
            UI.toggleVisibility('connectionInfo', true);
            UI.updateStatus('Ready to connect. Share the connection info.');
        } catch (error) {
            console.error('Error creating offer:', error);
            UI.updateStatus('Failed to create connection info');
        }
    },

    async handleAnswer(connectionData) {
        try {
            const data = JSON.parse(connectionData);
            await AppState.connection.rtc.setRemoteDescription({
                type: 'answer',
                sdp: data.sdp
            });

            if (data.iceCandidates) {
                for (const candidate of data.iceCandidates) {
                    await AppState.connection.rtc.addIceCandidate(candidate);
                }
            }

            UI.updateStatus('Connection established');
            UI.toggleVisibility('connectionInfo', false);
        } catch (error) {
            console.error('Error handling answer:', error);
            UI.updateStatus('Failed to establish connection');
        }
    }
};

// Event handlers
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

// Initialize app
document.addEventListener('DOMContentLoaded', () => {
    // Update send button onclick
    const sendButton = document.querySelector('#chatControls button');
    if (sendButton) {
        sendButton.onclick = handleSendMessage;
    }

    // Add enter key handler
    UI.elements.messageInput?.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') handleSendMessage();
    });
});

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

async function loadConversationHistory(peerId) {
    try {
        const conversationId = AppState.messages.getConversationId(AppState.user, AppState.connection.peerUsername);
        const response = await ApiService.get(CONFIG.api.endpoints.getConversation(AppState.user, conversationId));
        
        if (response.success && response.messages) {
            UI.elements.messagesContainer.innerHTML = '';
            response.messages.forEach(msg => {
                MessageHandler.addToChat(msg.message, msg.sender, false);
            });
        }
    } catch (error) {
        console.error('Error loading conversation:', error);
        UI.updateStatus('Failed to load conversation');
    }
}

async function handleOffer(connectionData) {
    try {
        const data = JSON.parse(connectionData);
        UI.updateStatus('Processing connection...');
        
        if (data.type === 'answer') {
            return ConnectionHandler.handleAnswer(connectionData);
        }

        if (data.userId && data.peerId) {
            AppState.connection.peerUsername = data.userId;
            AppState.connection.currentPeer = AppState.messages.getConversationId(AppState.user, data.userId);
        }

        AppState.connection.rtc = new RTCPeerConnection(CONFIG.rtc);
        
        AppState.connection.rtc.ondatachannel = event => {
            AppState.connection.dataChannel = event.channel;
            setupDataChannelHandlers(AppState.connection.dataChannel);
        };

        await AppState.connection.rtc.setRemoteDescription({
            type: 'offer',
            sdp: data.sdp
        });

        if (data.iceCandidates) {
            for (const candidate of data.iceCandidates) {
                await AppState.connection.rtc.addIceCandidate(candidate);
            }
        }

        const answer = await AppState.connection.rtc.createAnswer();
        await AppState.connection.rtc.setLocalDescription(answer);
        
        const iceCandidates = [];
        AppState.connection.rtc.onicecandidate = event => {
            if (event.candidate) {
                iceCandidates.push(event.candidate);
            } else {
                const fullAnswer = {
                    type: 'answer',
                    sdp: answer.sdp,
                    iceCandidates,
                    userId: AppState.user,
                    peerId: AppState.connection.peerUsername
                };
                document.getElementById('connectionInfoDisplay').value = JSON.stringify(fullAnswer);
                UI.toggleVisibility('connectionInfo', true);
                UI.updateStatus('Share the answer with the other peer');
            }
        };
        
        await loadConversationHistory(AppState.connection.currentPeer);
        UI.toggleVisibility('chatPanel', true);
        
    } catch (error) {
        console.error('Error handling connection data:', error);
        UI.updateStatus('Connection failed');
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

// Update window exports
Object.assign(window, {
    registerUser: async function(username) {
        if (!username) username = document.getElementById('username').value;
        if (!username) return;

        try {
            const data = await ApiService.post(CONFIG.api.endpoints.register, { username });
            if (data.success) {
                AppState.user = username;
                UI.toggleVisibility('userSetup', false);
                UI.toggleVisibility('connectionPanel', true);
                document.getElementById('userId').textContent = username;
                await displayAllConversations();
            }
        } catch (error) {
            console.error('Registration failed:', error);
            UI.updateStatus('Registration failed');
        }
    },
    connect,
    handleOffer,
    sendMessage: handleSendMessage,
    copyConnectionInfo
});

// Remove old global variables and use AppState instead
function updateStatus(status) {
    UI.updateStatus(status);
}

// Update the HTML to use the new function names

function setupDataChannelHandlers(channel) {
    if (!channel) return;

    // Set channel properties
    channel.binaryType = 'arraybuffer';
    channel.bufferedAmountLowThreshold = 65535;

    channel.onopen = async () => {
        try {
            console.log('Data channel opened');
            UI.updateStatus('Connected');
            UI.toggleVisibility('connectionPanel', false);
            UI.toggleVisibility('chatPanel', true);
            
            // Send sync request only if we're the one who initiated the connection
            if (channel.label === 'messageChannel') {
                await new Promise(resolve => setTimeout(resolve, 1000)); // Give channel time to stabilize
                channel.send(JSON.stringify({
                    type: 'sync_request',
                    sender: AppState.user,
                    conversationId: AppState.connection.currentPeer
                }));
            }
        } catch (error) {
            console.error('Error in channel open handler:', error);
        }
    };

    channel.onmessage = async event => {
        try {
            const messageData = JSON.parse(event.data);
            
            switch (messageData.type) {
                case 'message':
                    const messageId = MessageHandler.getMessageId({
                        sender: messageData.sender,
                        message: messageData.content,
                        timestamp: messageData.timestamp
                    });
                    
                    if (!MessageHandler.sentMessages.has(messageId)) {
                        MessageHandler.addToChat(messageData.content, messageData.sender);
                    }
                    break;
                    
                case 'sync_request':
                    const response = await ApiService.get(
                        CONFIG.api.endpoints.getConversation(AppState.user, AppState.connection.currentPeer)
                    );
                    if (response.success && response.messages) {
                        channel.send(JSON.stringify({
                            type: 'sync_response',
                            messages: response.messages,
                            sender: AppState.user
                        }));
                    }
                    break;
                    
                case 'sync_response':
                    await mergeMessages(messageData.messages);
                    break;
                    
                default:
                    console.warn('Unknown message type:', messageData.type);
            }
        } catch (error) {
            console.error('Error handling message:', error);
        }
    };

    channel.onerror = (error) => {
        console.error('Data channel error:', error);
        UI.updateStatus('Connection error');
    };

    channel.onclose = () => {
        console.log('Data channel closed');
        UI.updateStatus('Disconnected');
        UI.toggleVisibility('chatPanel', false);
        UI.toggleVisibility('connectionPanel', true);
        
        // Clean up connection
        if (AppState.connection.dataChannel) {
            AppState.connection.dataChannel = null;
        }
    };
}

async function displayAllConversations() {
    try {
        const response = await ApiService.get(CONFIG.api.endpoints.getAllConversations(AppState.user));
        if (!response.success) return;

        const container = UI.elements.conversationsContainer;
        container.innerHTML = '';
        
        for (const [peerId, messages] of Object.entries(response.conversations)) {
            // Skip invalid conversation IDs
            if (!peerId.includes('-')) continue;
            
            const peerNames = peerId.split('-');
            const otherUser = peerNames.find(name => name !== AppState.user);
            if (!otherUser) continue;
            
            const conversationDiv = document.createElement('div');
            conversationDiv.className = 'conversation-item';
            conversationDiv.innerHTML = `
                <h5>${otherUser}</h5>
                <small>${messages.length} messages</small>
            `;
            conversationDiv.onclick = async () => {
                AppState.connection.currentPeer = peerId;
                AppState.connection.peerUsername = otherUser;
                await loadConversationHistory(peerId);
                UI.toggleVisibility('chatPanel', true);
                document.getElementById('peerId').value = otherUser;
            };
            container.appendChild(conversationDiv);
        }
    } catch (error) {
        console.error('Error loading conversations:', error);
        UI.updateStatus('Failed to load conversations');
    }
}

async function mergeMessages(remoteMessages) {
    try {
        const response = await ApiService.get(
            CONFIG.api.endpoints.getConversation(AppState.user, AppState.connection.currentPeer)
        );
        const localMessages = response.success ? response.messages : [];

        // Create a map of existing messages to avoid duplicates
        const uniqueMessages = new Map();
        
        // Add local messages first
        localMessages.forEach(msg => {
            const messageId = MessageHandler.getMessageId(msg);
            uniqueMessages.set(messageId, msg);
            MessageHandler.sentMessages.add(messageId); // Track existing messages
        });

        // Add remote messages, overwriting duplicates
        remoteMessages.forEach(msg => {
            const messageId = MessageHandler.getMessageId(msg);
            uniqueMessages.set(messageId, msg);
            MessageHandler.sentMessages.add(messageId); // Track synced messages
        });

        const mergedMessages = Array.from(uniqueMessages.values())
            .sort((a, b) => a.timestamp - b.timestamp);

        // Save merged messages and update display
        await MessageHandler.save(AppState.connection.currentPeer, mergedMessages, true);
        await loadConversationHistory(AppState.connection.currentPeer);
    } catch (error) {
        console.error('Error merging messages:', error);
        UI.updateStatus('Failed to sync messages');
    }
}
