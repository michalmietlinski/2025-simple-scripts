const express = require('express');
const ws = require('ws');
const fs = require('fs');
const path = require('path');
const cors = require('cors');
const crypto = require('crypto');
const multer = require('multer');

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

const storage = multer.diskStorage({
    destination: (req, file, cb) => {
        const { username, conversationId } = req.params;
        const dir = path.join(DATA_DIR, username, conversationId, 'files');
        fs.mkdirSync(dir, { recursive: true });
        cb(null, dir);
    },
    filename: (req, file, cb) => {
        cb(null, `${Date.now()}-${file.originalname}`);
    }
});

const upload = multer({ storage });

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

// Add helper function for message deduplication
function deduplicateMessages(messages) {
    const uniqueMessages = new Map();
    
    messages.forEach(msg => {
        const messageId = msg.id || `${msg.sender}-${msg.timestamp}-${msg.message}`;
        if (!uniqueMessages.has(messageId) || msg.id) {
            uniqueMessages.set(messageId, {
                ...msg,
                id: msg.id || crypto.randomUUID()
            });
        }
    });
    
    return Array.from(uniqueMessages.values())
        .sort((a, b) => a.timestamp - b.timestamp);
}

// Update conversation save endpoint
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
            messages = deduplicateMessages([...messages, ...data]);
        } else {
            messages.push({
                ...data,
                id: data.id || crypto.randomUUID()
            });
            messages = deduplicateMessages(messages);
        }

        fs.writeFileSync(conversationPath, JSON.stringify(messages, null, 2));
        res.json({ success: true });
    } catch (err) {
        console.error('Error saving conversation:', err);
        res.status(500).json({ success: false, error: err.message });
    }
});

// Update conversation get endpoint
app.get('/api/conversation/:username/:peerId', (req, res) => {
    const { username, peerId } = req.params;
    const conversationPath = path.join(DATA_DIR, username, `${peerId}.json`);
    
    try {
        if (fs.existsSync(conversationPath)) {
            const messages = JSON.parse(fs.readFileSync(conversationPath, 'utf8'));
            const deduplicatedMessages = deduplicateMessages(messages);
            
            // Save deduped messages back if needed
            if (deduplicatedMessages.length !== messages.length) {
                fs.writeFileSync(conversationPath, JSON.stringify(deduplicatedMessages, null, 2));
            }
            
            res.json({ success: true, messages: deduplicatedMessages });
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

// Add file endpoints
app.post('/api/files/:username/:conversationId/upload', upload.single('file'), (req, res) => {
    try {
        const fileInfo = {
            id: crypto.randomUUID(),
            name: req.file.originalname,
            path: req.file.filename,
            size: req.file.size,
            timestamp: Date.now(),
            sender: req.body.sender
        };
        
        const metadataPath = path.join(
            DATA_DIR, 
            req.params.username, 
            req.params.conversationId, 
            'files.json'
        );
        
        let files = [];
        if (fs.existsSync(metadataPath)) {
            files = JSON.parse(fs.readFileSync(metadataPath));
        }
        
        files.push(fileInfo);
        fs.writeFileSync(metadataPath, JSON.stringify(files, null, 2));
        
        res.json({ success: true, file: fileInfo });
    } catch (error) {
        console.error('File upload error:', error);
        res.status(500).json({ success: false, error: error.message });
    }
});

app.get('/api/files/:username/:conversationId/download/:filename', (req, res) => {
    const filePath = path.join(
        DATA_DIR, 
        req.params.username, 
        req.params.conversationId, 
        'files',
        req.params.filename
    );
    
    if (fs.existsSync(filePath)) {
        res.download(filePath);
    } else {
        res.status(404).json({ success: false, error: 'File not found' });
    }
});

app.listen(port, () => {
    console.log(`Server running on port ${port}`);
}); 
