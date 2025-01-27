import dotenv from 'dotenv';
import express from 'express';
import OpenAI from 'openai';
import cors from 'cors';
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';
import { dirname } from 'path';

// Get __dirname equivalent in ES modules
const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

dotenv.config();

const app = express();
app.use(cors());
app.use(express.json());

const openai = new OpenAI({
  apiKey: process.env.OPENAI_API_KEY
});

// Create logs directory if it doesn't exist
const logsDir = path.join(__dirname, 'logs');
if (!fs.existsSync(logsDir)) {
  fs.mkdirSync(logsDir);
}

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
    const { models, prompt } = req.body;
    const responses = [];

    // Get responses from all models
    for (const model of models) {
      const completion = await openai.chat.completions.create({
        model,
        messages: [{ role: 'user', content: prompt }],
        temperature: 0.7,
      });
      
      responses.push({
        model,
        response: completion.choices[0].message.content
      });
    }

    // Save conversation to file
    const fileName = saveConversation(models, prompt, responses);

    res.json({ 
      responses,
      fileName 
    });
  } catch (error) {
    console.error('Error:', error);
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

const PORT = process.env.PORT || 3001;
app.listen(PORT, () => {
  console.log(`Server running on port ${PORT}`);
}); 
