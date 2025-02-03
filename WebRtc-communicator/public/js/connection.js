import { AppState } from './state.js';
import { CONFIG } from './config.js';
import { UI } from './ui.js';
import { ApiService } from './api.js';
import { MessageHandler } from './message.js';
import { mergeMessages, loadConversationHistory } from './conversation.js';
import { DomUtils, JsonUtils, ErrorUtils } from './utils.js';

// Connection management
export async function connect() {
    const peerId = DomUtils.getValue('peerId');
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
        const { message } = ErrorUtils.handleError(error, 'connect', 'Failed to establish connection');
        UI.updateStatus(message);
    }
}

export async function handleOffer(connectionData) {
    try {
        const { data, error } = JsonUtils.safeParseJson(connectionData);
        if (error) {
            throw error;
        }

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
                const { data: jsonData } = JsonUtils.safeStringifyJson(fullAnswer);
                DomUtils.setValue('connectionInfoDisplay', jsonData);
                UI.toggleVisibility('connectionInfo', true);
                UI.updateStatus('Share the answer with the other peer');
            }
        };
        
        await loadConversationHistory(AppState.connection.currentPeer);
        UI.toggleVisibility('chatPanel', true);
        
    } catch (error) {
        const { message } = ErrorUtils.handleError(error, 'handleOffer', 'Failed to establish connection');
        UI.updateStatus(message);
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
            const { message } = ErrorUtils.handleError(error, 'initialize', 'Connection initialization failed');
            UI.updateStatus(message);
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
            
            const { data: jsonData } = JsonUtils.safeStringifyJson(fullOffer);
            DomUtils.setValue('connectionInfoDisplay', jsonData);
            UI.toggleVisibility('connectionInfo', true);
            UI.updateStatus('Ready to connect. Share the connection info.');
        } catch (error) {
            const { message } = ErrorUtils.handleError(error, 'createFullOffer', 'Failed to create connection info');
            UI.updateStatus(message);
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
            ErrorUtils.handleError(error, 'channel.onopen');
        }
    };

    channel.onmessage = async event => {
        try {
            const { data: messageData, error } = JsonUtils.safeParseJson(event.data);
            if (error) throw error;
            
            switch (messageData.type) {
                case 'message':
                    const messageId = MessageHandler.getMessageId({
                        sender: messageData.sender,
                        message: messageData.content,
                        timestamp: messageData.timestamp
                    });
                    
                    if (!MessageHandler.sentMessages.has(messageId)) {
                        // Save the message first
                        await MessageHandler.save(AppState.connection.currentPeer, {
                            sender: messageData.sender,
                            message: messageData.content,
                            timestamp: messageData.timestamp
                        });
                        // Then display it
                        MessageHandler.addToChat(messageData.content, messageData.sender, false);
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
                    // Save file message first
                    await MessageHandler.save(AppState.connection.currentPeer, {
                        type: 'file_share',
                        sender: messageData.sender,
                        fileName: messageData.file.name,
                        fileSize: messageData.file.size,
                        fileId: messageData.file.id,
                        timestamp: messageData.timestamp
                    });
                    // Then display it
                    await MessageHandler.addToChat(
                        `Shared file: ${messageData.file.name}`, 
                        messageData.sender,
                        false
                    );
                    MessageHandler.addFileMessage(messageData.file, messageData.sender);
                    break;
                    
                default:
                    console.warn('Unknown message type:', messageData.type);
            }
        } catch (error) {
            ErrorUtils.handleError(error, 'channel.onmessage');
        }
    };

    channel.onerror = (error) => {
        ErrorUtils.handleError(error, 'channel.onerror');
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
