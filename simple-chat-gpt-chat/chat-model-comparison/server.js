require('dotenv').config();
const express = require('express');
const OpenAI = require('openai');
const cors = require('cors');
const fs = require('fs');
const path = require('path');

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

const PORT = process.env.PORT || 3001;
app.listen(PORT, () => {
  console.log(`Server running on port ${PORT}`);
}); 
