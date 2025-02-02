const express = require('express');
const ws = require('ws');
const fs = require('fs');
const path = require('path');
const cors = require('cors');

const app = express();
const port = 3000;

// Middleware
app.use(cors());
app.use(express.json());
app.use(express.static(path.join(__dirname, 'public')));

// Basic user sessions store
const activeUsers = new Map();

// File storage structure
const DATA_DIR = 'userdata';
fs.mkdirSync(DATA_DIR, { recursive: true });

// Routes
app.post('/api/user/register', (req, res) => {
    const { username } = req.body;
    const userDir = path.join(DATA_DIR, username);
    
    fs.mkdirSync(userDir, { recursive: true });
    activeUsers.set(username, {
        lastSeen: Date.now(),
        syncStatus: {}
    });
    
    res.json({ success: true, username });
});

app.post('/api/conversation/save', (req, res) => {
    const { username, peerId, data, overwrite } = req.body;
    const conversationPath = path.join(DATA_DIR, username, `${peerId}.json`);
    
    try {
        let messages = [];
        if (fs.existsSync(conversationPath) && !overwrite) {
            const fileContent = fs.readFileSync(conversationPath, 'utf8');
            try {
                messages = JSON.parse(fileContent);
                if (!Array.isArray(messages)) {
                    messages = [messages];
                }
            } catch (err) {
                console.error('Error parsing messages:', err);
                messages = [];
            }
        }

        if (Array.isArray(data)) {
            messages = data; // For overwriting with merged messages
        } else {
            messages.push(data);
        }

        fs.writeFileSync(conversationPath, JSON.stringify(messages, null, 2));
        res.json({ success: true });
    } catch (err) {
        console.error('Error saving conversation:', err);
        res.status(500).json({ success: false, error: err.message });
    }
});

app.get('/api/conversation/:username/:peerId', (req, res) => {
    const { username, peerId } = req.params;
    const conversationPath = path.join(DATA_DIR, username, `${peerId}.json`);
    
    try {
        if (fs.existsSync(conversationPath)) {
            const messages = JSON.parse(fs.readFileSync(conversationPath, 'utf8'));
            res.json({ success: true, messages });
        } else {
            res.json({ success: true, messages: [] });
        }
    } catch (err) {
        res.status(500).json({ success: false, error: err.message });
    }
});

// Add this helper function
function isValidConversationId(id) {
    return id && id.includes('-') && id.split('-').length === 2;
}

// Update the conversations endpoint
app.get('/api/conversations/:username', (req, res) => {
    const { username } = req.params;
    const userDir = path.join(DATA_DIR, username);
    
    try {
        const files = fs.readdirSync(userDir);
        const conversations = {};
        
        files.forEach(file => {
            if (file.endsWith('.json')) {
                const peerId = file.replace('.json', '');
                // Only include valid conversation IDs
                if (isValidConversationId(peerId)) {
                    const messages = JSON.parse(fs.readFileSync(path.join(userDir, file), 'utf8'));
                    conversations[peerId] = messages;
                } else {
                    // Optionally clean up invalid files
                    fs.unlinkSync(path.join(userDir, file));
                }
            }
        });
        
        res.json({ success: true, conversations });
    } catch (err) {
        res.status(500).json({ success: false, error: err.message });
    }
});

app.listen(port, () => {
    console.log(`Server running on port ${port}`);
}); 
