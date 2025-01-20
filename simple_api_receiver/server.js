const express = require('express');
const fs = require('fs').promises;
const path = require('path');
const notifier = require('node-notifier');

const app = express();
const PORT = 3005;
const SAVE_LOGS = process.env.SAVE_LOGS !== 'false';
const NOTIFY = process.env.NOTIFY === 'true';

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
            
            const yearDir = path.join(archiveDir, year);
            const monthDir = path.join(yearDir, month);
            const dayDir = path.join(monthDir, day);
            
            await fs.mkdir(yearDir, { recursive: true });
            await fs.mkdir(monthDir, { recursive: true });
            await fs.mkdir(dayDir, { recursive: true });

            const oldPath = path.join(logsDir, file);
            const newPath = path.join(dayDir, file);
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
        icon: path.join(__dirname, 'assets', 'icon.png'), // Optional: you can add an icon
        timeout: 5
    });
}

archiveExistingLogs();

app.use(express.json());
app.use(express.raw({ type: '*/*' }));

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

        if (SAVE_LOGS) {
            const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
            const filename = `${req.method}_${timestamp}_request.json`;
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
            notifications: NOTIFY ? 'enabled' : 'disabled'
        });

    } catch (error) {
        console.error('Error processing request:', error);
        res.status(500).json({ error: 'Internal server error' });
    }
});

app.listen(PORT, () => {
    console.log(`Server is running on port ${PORT}`);
    console.log(`Logging is ${SAVE_LOGS ? 'enabled' : 'disabled'}`);
    console.log(`Notifications are ${NOTIFY ? 'enabled' : 'disabled'}`);
}); 
