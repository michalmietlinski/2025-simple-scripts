import { AppState } from './state.js';
import { CONFIG } from './config.js';
import { UI } from './ui.js';
import { ApiService } from './api.js';
import { MessageHandler } from './message.js';
import { mergeMessages, loadConversationHistory } from './conversation.js';

// Connection management
export async function connect() {
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

export async function handleOffer(connectionData) {
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

// Connection handling
export const ConnectionHandler = {
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

// Helper function for setting up data channel handlers
export function setupDataChannelHandlers(channel) {
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
                    
                case 'file_share':
                    // Add file share message to chat
                    await MessageHandler.addToChat(
                        `Shared file: ${messageData.file.name}`, 
                        messageData.sender
                    );
                    MessageHandler.addFileMessage(messageData.file, messageData.sender);
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
