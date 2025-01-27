import dotenv from 'dotenv';
import express from 'express';
import OpenAI from 'openai';
import cors from 'cors';
import fs from 'fs';
import fsPromises from 'fs/promises';
import path from 'path';
import { fileURLToPath } from 'url';
import { dirname } from 'path';

// Get __dirname equivalent in ES modules
const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

dotenv.config();

const app = express();

// Update CORS configuration to be more specific
app.use(cors({
  origin: 'http://localhost:3000', // React app's URL
  methods: ['GET', 'POST', 'DELETE'],
  credentials: true
}));

app.use(express.json());

const openai = new OpenAI({
  apiKey: process.env.OPENAI_API_KEY
});

// Create logs directory if it doesn't exist
const logsDir = path.join(__dirname, 'logs');
if (!fs.existsSync(logsDir)) {
  fs.mkdirSync(logsDir);
}

// Add new constants for thread logs
const THREAD_LOGS_DIR = path.join(__dirname, 'threadLogs');

// Ensure thread logs directory exists
async function ensureThreadLogsDir() {
  try {
    await fsPromises.access(THREAD_LOGS_DIR);
  } catch {
    await fsPromises.mkdir(THREAD_LOGS_DIR);
  }
}

// Initialize thread logs directory
ensureThreadLogsDir();

// Function to save conversation to file
const saveConversation = (models, prompt, responses) => {
  const now = new Date();
  const dateStr = now.toISOString().split('T')[0];
  const timeStr = now.toISOString().split('T')[1].replace(/:/g, '-').split('.')[0];
  const modelNames = models.join('_vs_');
  
  const fileName = `${dateStr}_${timeStr}_${modelNames}.json`;
  const filePath = path.join(logsDir, dateStr);
  
  // Create date directory if it doesn't exist
  if (!fs.existsSync(filePath)) {
    fs.mkdirSync(filePath, { recursive: true });
  }
  
  const conversationData = {
    timestamp: now.toISOString(),
    prompt,
    responses: responses.map(r => ({
      model: r.model,
      response: r.response
    }))
  };
  
  fs.writeFileSync(
    path.join(filePath, fileName),
    JSON.stringify(conversationData, null, 2)
  );
  
  return fileName;
};

// Move health check endpoint to the top of routes
app.get('/api/health', (req, res) => {
  res.set('Access-Control-Allow-Origin', 'http://localhost:3000');
  res.json({ status: 'ok', timestamp: new Date().toISOString() });
});

// Endpoint to fetch available models
app.get('/api/models', async (req, res) => {
  try {
    const models = await openai.models.list();
    // Filter for chat models only and sort by name
    const chatModels = models.data
      .filter(model => model.id.includes('gpt'))
      .sort((a, b) => a.id.localeCompare(b.id));
    res.json(chatModels);
  } catch (error) {
    console.error('Error fetching models:', error);
    res.status(500).json({ error: error.message });
  }
});

app.post('/api/chat', async (req, res) => {
  try {
    const { models, prompt, previousMessages = [] } = req.body;
    const responses = [];

    // Get responses from all models
    for (const model of models) {
      const completion = await openai.chat.completions.create({
        model,
        messages: [{ role: 'user', content: prompt }],
        temperature: 0.7,
      });
      
      console.log('Full API Response:', JSON.stringify(completion, null, 2));
      
      responses.push({
        model,
        response: completion.choices[0].message.content
      });
    }

    // Save conversation to file
    const fileName = saveConversation(models, prompt, responses);
    console.log('\n💾 Saved conversation to:', fileName);

    res.json({ 
      responses,
      fileName 
    });
  } catch (error) {
    console.error('\n❌ Error in /api/chat:', error);
    res.status(500).json({ error: error.message });
  }
});

// Endpoint to fetch conversation logs
app.get('/api/logs', async (req, res) => {
  try {
    const logs = [];
    // Read all date directories
    const dates = fs.readdirSync(logsDir);
    
    dates.forEach(date => {
      const dateDir = path.join(logsDir, date);
      if (fs.statSync(dateDir).isDirectory()) {
        // Read all conversation files for this date
        const files = fs.readdirSync(dateDir);
        files.forEach(file => {
          const filePath = path.join(dateDir, file);
          const conversation = JSON.parse(fs.readFileSync(filePath, 'utf8'));
          logs.push({
            date,
            fileName: file,
            ...conversation
          });
        });
      }
    });
    
    // Sort by timestamp, most recent first
    logs.sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp));
    res.json(logs);
  } catch (error) {
    console.error('Error fetching logs:', error);
    res.status(500).json({ error: error.message });
  }
});

// Endpoint to delete a specific conversation
app.delete('/api/logs/:date/:filename', async (req, res) => {
  try {
    const { date, filename } = req.params;
    const filePath = path.join(logsDir, date, filename);
    
    if (fs.existsSync(filePath)) {
      fs.unlinkSync(filePath);
      
      // Remove date directory if empty
      const dateDir = path.join(logsDir, date);
      if (fs.readdirSync(dateDir).length === 0) {
        fs.rmdirSync(dateDir);
      }
      
      res.json({ message: 'Conversation deleted successfully' });
    } else {
      res.status(404).json({ error: 'Conversation not found' });
    }
  } catch (error) {
    console.error('Error deleting conversation:', error);
    res.status(500).json({ error: error.message });
  }
});

// Endpoint to clear all history
app.delete('/api/logs', async (req, res) => {
  try {
    const dates = fs.readdirSync(logsDir);
    
    dates.forEach(date => {
      const dateDir = path.join(logsDir, date);
      if (fs.statSync(dateDir).isDirectory()) {
        fs.rmSync(dateDir, { recursive: true, force: true });
      }
    });
    
    res.json({ message: 'All history cleared successfully' });
  } catch (error) {
    console.error('Error clearing history:', error);
    res.status(500).json({ error: error.message });
  }
});

// New endpoint for threaded chat
app.post('/api/thread-chat', async (req, res) => {
  const { models, prompt, previousMessages, threadId } = req.body;
  const timestamp = new Date().toISOString();
  const responses = [];

  try {
    // Check if this is a new thread
    const filePath = path.join(THREAD_LOGS_DIR, `${threadId}.json`);
    const nullFilePath = path.join(THREAD_LOGS_DIR, 'null.json');
    const isNewThread = !fs.existsSync(filePath);
    
    // If this is a new thread and null.json exists, check if it's the continuation
    if (isNewThread && fs.existsSync(nullFilePath)) {
      try {
        const nullContent = await fsPromises.readFile(nullFilePath, 'utf-8');
        const nullLogs = nullContent.trim().split('\n').map(line => JSON.parse(line));
        const lastLog = nullLogs[nullLogs.length - 1];
        
        // If the previous messages match the null.json content, this is a continuation
        if (previousMessages.length > 0 && 
            previousMessages[0].content === lastLog.prompt) {
          // Move null.json content to the new thread file
          await fsPromises.rename(nullFilePath, filePath);
          console.log('Converted null.json to thread:', threadId);
        }
      } catch (error) {
        console.error('Error handling null.json:', error);
      }
    }

    // Now continue with normal thread processing
    for (const model of models) {
      const messages = [...previousMessages, { role: 'user', content: prompt }];
      const completion = await openai.chat.completions.create({
        model,
        messages,
        temperature: 0.7,
      });

      const response = completion.choices[0].message.content;
      responses.push({ model, response });

      // Log the conversation
      const logEntry = {
        timestamp,
        threadId,
        model,
        prompt,
        response,
        messages,
        firstPrompt: isNewThread && !fs.existsSync(filePath) ? prompt : undefined
      };

      await fsPromises.appendFile(
        filePath,
        JSON.stringify(logEntry) + '\n'
      );
    }

    res.json({ responses });
  } catch (error) {
    console.error('Error:', error);
    res.status(500).json({ error: 'Failed to process request' });
  }
});

// Endpoint to load thread history
app.get('/api/thread-history/:threadId', async (req, res) => {
  const { threadId } = req.params;
  
  try {
    const filePath = path.join(THREAD_LOGS_DIR, `${threadId}.json`);
    const fileExists = await fsPromises.access(filePath)
      .then(() => true)
      .catch(() => false);

    if (!fileExists) {
      return res.json({ messages: [] });
    }

    const fileContent = await fsPromises.readFile(filePath, 'utf-8');
    const logs = fileContent
      .trim()
      .split('\n')
      .map(line => JSON.parse(line));

    // Create messages array with proper order
    const messages = [];
    // Group logs by prompt to handle multiple models
    const promptGroups = new Map();
    
    logs.forEach(log => {
      if (!promptGroups.has(log.prompt)) {
        promptGroups.set(log.prompt, []);
      }
      promptGroups.get(log.prompt).push(log);
    });

    // Process each prompt group
    promptGroups.forEach((groupLogs) => {
      // Add user message once per prompt
      messages.push({ 
        role: 'user', 
        content: groupLogs[0].prompt 
      });
      
      // Add all model responses for this prompt
      groupLogs.forEach(log => {
        messages.push({
          role: 'assistant',
          model: log.model,
          content: log.response
        });
      });
    });

    res.json({ messages });
  } catch (error) {
    console.error('Error:', error);
    res.status(500).json({ error: 'Failed to load thread history' });
  }
});

// Endpoint to list all threads
app.get('/api/threads', async (req, res) => {
  try {
    const files = await fsPromises.readdir(THREAD_LOGS_DIR);
    const threads = await Promise.all(files.map(async file => {
      const filePath = path.join(THREAD_LOGS_DIR, file);
      const content = await fsPromises.readFile(filePath, 'utf-8');
      const firstLine = content.split('\n')[0];
      const firstEntry = JSON.parse(firstLine);
      const threadId = path.parse(file).name;
      
      return {
        id: threadId,
        shortId: threadId.slice(-8), // Get last 8 characters
        firstPrompt: firstEntry.prompt,
        timestamp: firstEntry.timestamp
      };
    }));
    
    // Sort by timestamp, newest first
    threads.sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp));
    
    res.json({ threads });
  } catch (error) {
    console.error('Error:', error);
    res.status(500).json({ error: 'Failed to list threads' });
  }
});

// Delete specific thread
app.delete('/api/thread/:threadId', async (req, res) => {
  const { threadId } = req.params;
  
  try {
    const filePath = path.join(THREAD_LOGS_DIR, `${threadId}.json`);
    await fsPromises.unlink(filePath);
    res.json({ message: 'Thread deleted successfully' });
  } catch (error) {
    console.error('Error:', error);
    res.status(500).json({ error: 'Failed to delete thread' });
  }
});

// Delete all threads
app.delete('/api/threads', async (req, res) => {
  try {
    const files = await fsPromises.readdir(THREAD_LOGS_DIR);
    await Promise.all(
      files.map(file => 
        fsPromises.unlink(path.join(THREAD_LOGS_DIR, file))
      )
    );
    res.json({ message: 'All threads deleted successfully' });
  } catch (error) {
    console.error('Error:', error);
    res.status(500).json({ error: 'Failed to delete all threads' });
  }
});

const PORT = process.env.PORT || 3001;
app.listen(PORT, () => {
  console.log(`Server running on port ${PORT}`);
}); 
