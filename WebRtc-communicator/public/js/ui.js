// UI Helper functions
export const UI = {
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
