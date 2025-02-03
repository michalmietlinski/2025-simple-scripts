import { UI } from '../ui/UIManager.js';

export function downloadFileFromData(fileId, data, fileName) {
    try {
        if (!data) {
            UI.updateStatus('File data not available');
            return;
        }

        const link = document.createElement('a');
        link.href = data;
        link.download = fileName;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
    } catch (error) {
        console.error('File download failed:', error);
        UI.updateStatus('Failed to download file');
    }
} 
