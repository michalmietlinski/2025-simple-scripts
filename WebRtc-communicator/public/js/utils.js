// File operations
export const FileUtils = {
    formatSize(bytes) {
        if (bytes < 1024) return bytes + ' B';
        if (bytes < 1048576) return (bytes / 1024).toFixed(1) + ' KB';
        return (bytes / 1048576).toFixed(1) + ' MB';
    }
};

// JSON operations
export const JsonUtils = {
    safeParseJson(data) {
        try {
            return { data: JSON.parse(data), error: null };
        } catch (error) {
            console.error('JSON parse error:', error);
            return { data: null, error };
        }
    },

    safeStringifyJson(data) {
        try {
            return { data: JSON.stringify(data), error: null };
        } catch (error) {
            console.error('JSON stringify error:', error);
            return { data: null, error };
        }
    }
};

// DOM operations
export const DomUtils = {
    getElement(id) {
        const element = document.getElementById(id);
        if (!element) {
            console.warn(`Element with id '${id}' not found`);
        }
        return element;
    },

    getValue(id) {
        const element = this.getElement(id);
        return element ? element.value.trim() : '';
    },

    setValue(id, value) {
        const element = this.getElement(id);
        if (element) {
            element.value = value;
        }
    },

    copyToClipboard(text) {
        const textarea = document.createElement('textarea');
        textarea.value = text;
        document.body.appendChild(textarea);
        textarea.select();
        document.execCommand('copy');
        document.body.removeChild(textarea);
    }
};

// Error handling
export const ErrorUtils = {
    handleError(error, context, fallbackMessage = 'Operation failed') {
        console.error(`Error in ${context}:`, error);
        return {
            message: error.message || fallbackMessage,
            context,
            timestamp: Date.now()
        };
    }
}; 
