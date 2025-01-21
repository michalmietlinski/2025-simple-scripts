const express = require('express');
const fs = require('fs').promises;
const path = require('path');
const notifier = require('node-notifier');
const readline = require('readline');

const app = express();
let PORT = 3005;
const SAVE_LOGS = process.env.SAVE_LOGS !== 'false';
const NOTIFY = process.env.NOTIFY === 'true';

let REDIRECT_URL = null;

async function getUserChoice() {
    const rl = readline.createInterface({
        input: process.stdin,
        output: process.stdout
    });

    const getPort = () => new Promise((resolve) => {
        rl.question('Enter port number (default: 3005): ', (port) => {
            const portNum = parseInt(port);
            if (port === '' || (portNum >= 1 && portNum <= 65535)) {
                resolve(port === '' ? 3005 : portNum);
            } else {
                console.log('Invalid port. Please enter a number between 1 and 65535.');
                resolve(getPort());
            }
        });
    });

    const getRedirectUrl = () => new Promise((resolve) => {
        rl.question('Enter the target URL (e.g., http://example.com): ', (url) => {
            try {
                const targetUrl = new URL(url);
                // Check if redirect URL would create a loop
                const targetPort = targetUrl.port || (targetUrl.protocol === 'https:' ? '443' : '80');
                if (targetUrl.hostname === 'localhost' && parseInt(targetPort) === PORT) {
                    console.log('Error: Cannot redirect to the same address and port this app is running on.');
                    resolve(getRedirectUrl());
                } else {
                    resolve(url);
                }
            } catch (error) {
                console.log('Invalid URL format. Please enter a valid URL.');
                resolve(getRedirectUrl());
            }
        });
    });

    PORT = await getPort();

    return new Promise((resolve) => {
        rl.question('Do you want to redirect requests to an external URL? (y/n): ', async (answer) => {
            if (answer.toLowerCase() === 'y') {
                REDIRECT_URL = await getRedirectUrl();
                rl.close();
                resolve();
            } else {
                rl.close();
                resolve();
            }
        });
    });
}

// Function to sanitize path for filesystem
function sanitizePath(pathStr) {
    return pathStr.replace(/[^a-zA-Z0-9-_]/g, '_').replace(/_{2,}/g, '_');
}

// Function to move existing logs to archives
async function archiveExistingLogs() {
    if (!SAVE_LOGS) return;
    try {
        const logsDir = path.join(__dirname, 'logs');
        const archiveDir = path.join(__dirname, 'archives');

        await fs.mkdir(logsDir, { recursive: true });
        await fs.mkdir(archiveDir, { recursive: true });

        const files = await fs.readdir(logsDir);
        
        for (const file of files) {
            const dateMatch = file.match(/\d{4}-\d{2}-\d{2}/);
            if (!dateMatch) continue;

            const dateStr = dateMatch[0];
            const [year, month, day] = dateStr.split('-');
            
            // Extract endpoint from filename
            const endpointMatch = file.match(/_endpoint_(.+)\.json$/);
            const endpoint = endpointMatch ? endpointMatch[1] : 'root';
            
            const yearDir = path.join(archiveDir, year);
            const monthDir = path.join(yearDir, month);
            const dayDir = path.join(monthDir, day);
            const endpointDir = path.join(dayDir, endpoint);
            
            await fs.mkdir(yearDir, { recursive: true });
            await fs.mkdir(monthDir, { recursive: true });
            await fs.mkdir(dayDir, { recursive: true });
            await fs.mkdir(endpointDir, { recursive: true });

            const oldPath = path.join(logsDir, file);
            const newPath = path.join(endpointDir, file);
            await fs.rename(oldPath, newPath);
        }

        console.log('Successfully archived existing logs');
    } catch (error) {
        console.error('Error archiving logs:', error);
    }
}

// Function to send notification
function sendNotification(requestData) {
    if (!NOTIFY) return;
    
    notifier.notify({
        title: `New ${requestData.method} Request`,
        message: `Endpoint: ${requestData.path}\nTimestamp: ${requestData.timestamp}`,
        icon: path.join(__dirname, 'assets', 'icon.png'),
        timeout: 5
    });
}

archiveExistingLogs();

app.use(express.raw({ 
    type: '*/*',
    limit: '50mb'
}));

app.use((req, res, next) => {
    req.rawBody = req.body;
    next();
});

app.use(express.json());

app.all('*', async (req, res) => {
    try {
        const requestData = {
            timestamp: new Date().toISOString(),
            method: req.method,
            path: req.path,
            query: req.query,
            headers: req.headers,
            body: req.body
        };

        console.log('Request received:', requestData);
        sendNotification(requestData);
        
        if (REDIRECT_URL) {
            console.log('Redirecting request to:', REDIRECT_URL);
            const targetUrl = new URL(req.path, REDIRECT_URL);
            Object.entries(req.query).forEach(([key, value]) => {
                targetUrl.searchParams.append(key, value);
            });
            
            console.log('Target URL:', targetUrl.toString());
            
            try {
                // Clean up headers to avoid conflicts
                const forwardHeaders = { ...req.headers };
                delete forwardHeaders.host;
                delete forwardHeaders.connection;
                delete forwardHeaders['content-length'];

                const response = await fetch(targetUrl.toString(), {
                    method: req.method,
                    headers: forwardHeaders,
                    body: req.rawBody || req.body,
                });
                
                console.log('Response status:', response.status);

                if (SAVE_LOGS) {
                    const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
                    const sanitizedEndpoint = sanitizePath(req.path);
                    const responseData = {
                        timestamp: new Date().toISOString(),
                        status: response.status,
                        statusText: response.statusText,
                        headers: Object.fromEntries(response.headers),
                        body: await response.clone().text(),
                        originalUrl: targetUrl.toString()
                    };

                    const responseFilename = `${req.method}_${timestamp}_endpoint_${sanitizedEndpoint || 'root'}_response.json`;
                    const logsDir = path.join(__dirname, 'logs');
                    await fs.writeFile(
                        path.join(logsDir, responseFilename),
                        JSON.stringify(responseData, null, 2)
                    );
                }
            } catch (error) {
                console.error('Error forwarding request:', error.message);
            }
        }

        if (SAVE_LOGS) {
            const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
            const sanitizedEndpoint = sanitizePath(req.path);
            const filename = `${req.method}_${timestamp}_endpoint_${sanitizedEndpoint || 'root'}.json`;
            const logsDir = path.join(__dirname, 'logs');
            await fs.mkdir(logsDir, { recursive: true });
            await fs.writeFile(
                path.join(logsDir, filename),
                JSON.stringify(requestData, null, 2)
            );
        }

        res.json({ 
            message: 'Request processed successfully',
            timestamp: requestData.timestamp,
            logging: SAVE_LOGS ? 'enabled' : 'disabled',
            notifications: NOTIFY ? 'enabled' : 'disabled',
            forwarding: REDIRECT_URL ? `enabled to ${REDIRECT_URL}` : 'disabled'
        });

    } catch (error) {
        console.error('Error processing request:', error);
        res.status(500).json({ error: 'Internal server error' });
    }
});

// Modify the startup sequence
async function startServer() {
    await getUserChoice();
    await archiveExistingLogs();
    
    app.listen(PORT, () => {
        console.log(`Server is running on port ${PORT}`);
        console.log(`Logging is ${SAVE_LOGS ? 'enabled' : 'disabled'}`);
        console.log(`Notifications are ${NOTIFY ? 'enabled' : 'disabled'}`);
        if (REDIRECT_URL) {
            console.log(`Request forwarding is enabled to: ${REDIRECT_URL}`);
        }
    });
}

startServer(); 
