const express = require('express');
const fs = require('fs').promises;
const path = require('path');

const app = express();
const PORT = 3005;

// Function to move existing logs to archives
async function archiveExistingLogs() {
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

        const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
        const filename = `${req.method}_${timestamp}_request.json`;
        const logsDir = path.join(__dirname, 'logs');
        await fs.mkdir(logsDir, { recursive: true });
        await fs.writeFile(
            path.join(logsDir, filename),
            JSON.stringify(requestData, null, 2)
        );
        console.log('Request received:', requestData);
        res.json({ 
            message: 'Request logged successfully',
            timestamp: requestData.timestamp
        });

    } catch (error) {
        console.error('Error processing request:', error);
        res.status(500).json({ error: 'Internal server error' });
    }
});

app.listen(PORT, () => {
    console.log(`Server is running on port ${PORT}`);
}); 
