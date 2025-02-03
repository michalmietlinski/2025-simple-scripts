import { AppState, CONFIG } from '../state/AppState.js';
import { UI } from '../ui/UIManager.js';
import { MessageHandler } from './MessageHandler.js';
import { ApiService } from '../services/ApiService.js';
import { mergeMessages } from '../utils/MessageUtils.js';

export function setupDataChannelHandlers(channel) {
    if (!channel) return;

    channel.binaryType = 'arraybuffer';
    channel.bufferedAmountLowThreshold = 65535;

    channel.onopen = async () => {
        UI.updateStatus('Connected');
        UI.toggleVisibility('connectionPanel', false);
        UI.toggleVisibility('chatPanel', true);

        // Send any offline messages
        const offlineMessages = AppState.messages.offline.get(AppState.connection.currentPeer) || [];
        for (const msg of offlineMessages) {
            channel.send(JSON.stringify(msg));
        }
        AppState.messages.offline.delete(AppState.connection.currentPeer);

        // Request message sync
        channel.send(JSON.stringify({
            type: 'sync_request',
            sender: AppState.user
        }));
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
                        await MessageHandler.save(AppState.connection.currentPeer, {
                            sender: messageData.sender,
                            message: messageData.content,
                            timestamp: messageData.timestamp
                        });
                        MessageHandler.addToChat(messageData.content, messageData.sender);
                        
                        // Send acknowledgment
                        channel.send(JSON.stringify({
                            type: 'message_ack',
                            messageId,
                            sender: AppState.user
                        }));
                        
                        UI.updateStatus('Message received');
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
                        UI.updateStatus('Messages synced');
                    }
                    break;
                    
                case 'sync_response':
                    await mergeMessages(messageData.messages);
                    UI.updateStatus('Messages synced');
                    break;

                case 'file_share':
                    await MessageHandler.save(AppState.connection.currentPeer, {
                        type: 'file_share',
                        sender: messageData.sender,
                        fileName: messageData.file.name,
                        fileSize: messageData.file.size,
                        fileId: messageData.file.id,
                        filePath: messageData.file.path,
                        timestamp: messageData.timestamp
                    });
                    await MessageHandler.addToChat(
                        `Shared file: ${messageData.file.name}`, 
                        messageData.sender,
                        false
                    );
                    MessageHandler.addFileMessage(messageData.file, messageData.sender);
                    UI.updateStatus('File received');
                    break;
                    
                case 'message_ack':
                    const pendingElement = document.querySelector(`[data-message-id="${messageData.messageId}"]`);
                    if (pendingElement) {
                        const syncIcon = pendingElement.querySelector('.pending-sync');
                        if (syncIcon) syncIcon.remove();
                    }
                    break;
                    
                default:
                    console.warn('Unknown message type:', messageData.type);
            }
        } catch (error) {
            console.error('Error handling message:', error);
            UI.updateStatus('Failed to process message');
        }
    };

    channel.onerror = (error) => {
        console.error('Data channel error:', error);
        UI.updateStatus('Connection error');
    };

    channel.onclose = () => {
        UI.updateStatus('Disconnected');
        UI.toggleVisibility('chatPanel', false);
        UI.toggleVisibility('connectionPanel', true);
        AppState.connection.dataChannel = null;
    };
} 
