// Configuration
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
            getAllConversations: (username) => `/conversations/${username}`
        }
    }
}; 
