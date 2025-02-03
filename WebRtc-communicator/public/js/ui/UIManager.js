export const UI = {
    elements: {
        get messageInput() { return document.getElementById('messageInput') },
        get messagesContainer() { return document.getElementById('messages') },
        get connectionStatus() { return document.querySelector('#connectionStatus span') },
        get conversationsContainer() { return document.getElementById('conversationsContainer') }
    },
    
    toggleVisibility: (elementId, show) => {
        const element = document.getElementById(elementId);
        if (element) {
            if (elementId === 'statusPanel') {
                element.classList.toggle('visible', show);
            } else {
                element.classList.toggle('hidden', !show);
            }
        }
    },
    
    updateStatus: (status) => {
        UI.elements.connectionStatus.textContent = status;
    },
    
    clearInput: (element) => {
        element.value = '';
    }
}; 
