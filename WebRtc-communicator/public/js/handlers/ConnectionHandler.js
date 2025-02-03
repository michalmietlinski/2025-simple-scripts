import { AppState, CONFIG } from '../state/AppState.js';
import { UI } from '../ui/UIManager.js';
import { setupDataChannelHandlers } from './DataChannelHandler.js';
import { loadConversationHistory } from '../utils/MessageUtils.js';

export const ConnectionHandler = {
    async initialize(peerId) {
        try {
            AppState.connection.rtc = new RTCPeerConnection(CONFIG.rtc);
            AppState.connection.dataChannel = AppState.connection.rtc.createDataChannel('messageChannel');
            setupDataChannelHandlers(AppState.connection.dataChannel);
            
            // Create and set local description
            const offer = await AppState.connection.rtc.createOffer();
            await AppState.connection.rtc.setLocalDescription(offer);
            
            // Collect ICE candidates
            const iceCandidates = [];
            await new Promise(resolve => {
                AppState.connection.rtc.onicecandidate = event => {
                    if (event.candidate) {
                        iceCandidates.push(event.candidate);
                    } else {
                        resolve();
                    }
                };
            });

            // Create connection info
            const connectionInfo = {
                type: offer.type,
                sdp: offer.sdp,
                iceCandidates,
                userId: AppState.user,
                peerId: AppState.connection.peerUsername
            };
            
            document.getElementById('connectionInfoDisplay').value = JSON.stringify(connectionInfo);
            UI.toggleVisibility('connectionInfo', true);
            UI.updateStatus('Ready to connect. Share the connection info.');
        } catch (error) {
            console.error('Connection initialization failed:', error);
            UI.updateStatus('Connection failed');
        }
    },

    async handleOffer(connectionData) {
        try {
            const data = JSON.parse(connectionData);
            UI.updateStatus('Processing connection...');

            // Handle answer
            if (data.type === 'answer') {
                await AppState.connection.rtc.setRemoteDescription(data);
                for (const candidate of data.iceCandidates || []) {
                    await AppState.connection.rtc.addIceCandidate(candidate);
                }
                UI.updateStatus('Connection established');
                UI.toggleVisibility('connectionInfo', false);
                return;
            }

            // Handle offer
            if (data.userId && data.peerId) {
                AppState.connection.peerUsername = data.userId;
                AppState.connection.currentPeer = AppState.messages.getConversationId(AppState.user, data.userId);
            }

            // Create new connection
            AppState.connection.rtc = new RTCPeerConnection(CONFIG.rtc);
            AppState.connection.rtc.ondatachannel = event => {
                AppState.connection.dataChannel = event.channel;
                setupDataChannelHandlers(AppState.connection.dataChannel);
            };

            // Set remote description and ICE candidates
            await AppState.connection.rtc.setRemoteDescription(data);
            for (const candidate of data.iceCandidates || []) {
                await AppState.connection.rtc.addIceCandidate(candidate);
            }

            // Create and set local description (answer)
            const answer = await AppState.connection.rtc.createAnswer();
            await AppState.connection.rtc.setLocalDescription(answer);

            // Collect ICE candidates for answer
            const iceCandidates = [];
            await new Promise(resolve => {
                AppState.connection.rtc.onicecandidate = event => {
                    if (event.candidate) {
                        iceCandidates.push(event.candidate);
                    } else {
                        resolve();
                    }
                };
            });

            // Create answer info
            const answerInfo = {
                type: answer.type,
                sdp: answer.sdp,
                iceCandidates
            };

            document.getElementById('connectionInfoDisplay').value = JSON.stringify(answerInfo);
            UI.toggleVisibility('connectionInfo', true);
            UI.updateStatus('Ready to connect. Share the connection info.');

            await loadConversationHistory(AppState.connection.currentPeer);
        } catch (error) {
            console.error('Error handling connection:', error);
            UI.updateStatus('Failed to process connection');
        }
    }
}; 
