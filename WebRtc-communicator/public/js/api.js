import { CONFIG } from './config.js';

// API Service
export const ApiService = {
    async post(endpoint, data) {
        try {
            const response = await fetch(`${CONFIG.api.base}${endpoint}`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(data)
            });
            return await response.json();
        } catch (error) {
            console.error(`API Error (${endpoint}):`, error);
            throw error;
        }
    },

    async get(endpoint) {
        try {
            const response = await fetch(`${CONFIG.api.base}${endpoint}`);
            return await response.json();
        } catch (error) {
            console.error(`API Error (${endpoint}):`, error);
            throw error;
        }
    }
}; 
