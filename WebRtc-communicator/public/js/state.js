// State management
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
        generateId: () => crypto.randomUUID()
    }
}; 
