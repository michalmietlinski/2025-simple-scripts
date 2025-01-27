import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { v4 as uuidv4 } from 'uuid';
import ComparisonForm from './ComparisonForm';
import ThreadedChat from './ThreadedChat';
import ThreadHistoryPanel from './ThreadHistoryPanel';
import './ThreadedComparison.css';

function ThreadedComparison() {
  const [availableModels, setAvailableModels] = useState([]);
  const [selectedModels, setSelectedModels] = useState([]);
  const [prompt, setPrompt] = useState('');
  const [loading, setLoading] = useState({});
  const [messages, setMessages] = useState([]);
  const [modelsLocked, setModelsLocked] = useState(false);
  const [modelsLoading, setModelsLoading] = useState(true);
  const [modelsError, setModelsError] = useState(null);
  const [threadId, setThreadId] = useState(null);
  const [showHistory, setShowHistory] = useState(false);
  const [threads, setThreads] = useState([]);
  const [threadsLoading, setThreadsLoading] = useState(false);
  const [deletingThreads, setDeletingThreads] = useState({});
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [chatLayout, setChatLayout] = useState('stacked');
  const [isFullWidth, setIsFullWidth] = useState(false);

  useEffect(() => {
    const fetchModels = async () => {
      try {
        setModelsLoading(true);
        const response = await axios.get('http://localhost:3001/api/models');
        const models = response.data.map(model => ({
          id: model.id,
          name: formatModelName(model.id)
        }));
        setAvailableModels(models);
      } catch (error) {
        console.error('Error fetching models:', error);
        setModelsError('Failed to load available models');
      } finally {
        setModelsLoading(false);
      }
    };

    fetchModels();
  }, []);

  useEffect(() => {
    fetchThreads();
  }, []);

  const formatModelName = (modelId) => {
    return modelId
      .replace('gpt-', 'GPT-')
      .split('-')
      .map(word => word === 'turbo' ? 'Turbo' : word)
      .join(' ');
  };

  const handleModelToggle = (modelId) => {
    if (!modelsLocked) {
      setSelectedModels(prev => 
        prev.includes(modelId)
          ? prev.filter(id => id !== modelId)
          : [...prev, modelId]
      );
    }
  };

  const fetchThreads = async () => {
    try {
      setThreadsLoading(true);
      const response = await axios.get('http://localhost:3001/api/threads');
      setThreads(response.data.threads);
    } catch (error) {
      console.error('Error fetching threads:', error);
    } finally {
      setThreadsLoading(false);
    }
  };

  const loadThread = async (threadId) => {
    try {
      const response = await axios.get(`http://localhost:3001/api/thread-history/${threadId}`);
      
      // Get unique models from the thread history
      const uniqueModels = [...new Set(
        response.data.messages
          .filter(msg => msg.role === 'assistant')
          .map(msg => msg.model)
      )];
      
      // Set the models used in this thread
      setSelectedModels(uniqueModels);
      setMessages(response.data.messages);
      setThreadId(threadId);
      setModelsLocked(true);
      setShowHistory(false);
    } catch (error) {
      console.error('Error loading thread:', error);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!modelsLocked) {
      setModelsLocked(true);
      setThreadId(uuidv4());
    }

    try {
      setIsSubmitting(true);
      selectedModels.forEach(model => {
        setLoading(prev => ({ ...prev, [model]: true }));
      });

      const previousMessages = messages.map(msg => ({
        role: msg.role,
        content: msg.content
      }));

      const response = await axios.post('http://localhost:3001/api/thread-chat', {
        models: selectedModels,
        prompt,
        previousMessages,
        threadId
      });

      setMessages(prev => [...prev, {
        role: 'user',
        content: prompt
      }]);

      response.data.responses.forEach(r => {
        setMessages(prev => [...prev, {
          role: 'assistant',
          model: r.model,
          content: r.response
        }]);
      });

      setPrompt('');
      fetchThreads();

    } catch (error) {
      console.error('Error:', error);
    } finally {
      setIsSubmitting(false);
      selectedModels.forEach(model => {
        setLoading(prev => ({ ...prev, [model]: false }));
      });
    }
  };

  const deleteThread = async (threadId) => {
    try {
      setDeletingThreads(prev => ({ ...prev, [threadId]: true }));
      await axios.delete(`http://localhost:3001/api/thread/${threadId}`);
      setThreads(prev => prev.filter(t => t.id !== threadId));
    } catch (error) {
      console.error('Error deleting thread:', error);
    } finally {
      setDeletingThreads(prev => ({ ...prev, [threadId]: false }));
    }
  };

  const clearAllThreads = async () => {
    if (window.confirm('Are you sure you want to clear all threads? This cannot be undone.')) {
      try {
        await axios.delete('http://localhost:3001/api/threads');
        setThreads([]);
      } catch (error) {
        console.error('Error clearing threads:', error);
      }
    }
  };

  const clearForm = () => {
    if (modelsLocked && 
        window.confirm('This will clear the entire thread and allow you to start a new one. Continue?')) {
      setMessages([]);
      setModelsLocked(false);
      setPrompt('');
      setThreadId(null);
      setSelectedModels([]);
    } else if (!modelsLocked) {
      setPrompt('');
      setSelectedModels([]);
    }
  };

  return (
    <div className={`threaded-comparison ${isFullWidth ? 'full-width' : ''}`}>
      <h1>Threaded Model Comparison</h1>
      
      <div className="chat-controls">
        <label>
          <input
            type="checkbox"
            checked={isFullWidth}
            onChange={(e) => setIsFullWidth(e.target.checked)}
          />
          Full Width
        </label>
        
        <div className="layout-toggle">
          <label>
            <input
              type="radio"
              name="layout"
              value="stacked"
              checked={chatLayout === 'stacked'}
              onChange={(e) => setChatLayout(e.target.value)}
            />
            Stacked
          </label>
          <label>
            <input
              type="radio"
              name="layout"
              value="grid"
              checked={chatLayout === 'grid'}
              onChange={(e) => setChatLayout(e.target.value)}
            />
            Side by Side
          </label>
        </div>
      </div>

      <ThreadHistoryPanel
        showHistory={showHistory}
        setShowHistory={setShowHistory}
        threads={threads}
        threadsLoading={threadsLoading}
        loadThread={loadThread}
        deleteThread={deleteThread}
        clearAllThreads={clearAllThreads}
        deletingThreads={deletingThreads}
      />

      <ComparisonForm
        prompt={prompt}
        setPrompt={setPrompt}
        handleSubmit={handleSubmit}
        selectedModels={selectedModels}
        availableModels={availableModels}
        handleModelToggle={handleModelToggle}
        modelsLoading={modelsLoading}
        modelsError={modelsError}
        clearForm={clearForm}
        modelsLocked={modelsLocked}
        isSubmitting={isSubmitting}
      />
      
      <ThreadedChat
        messages={messages}
        selectedModels={selectedModels}
        loading={loading}
        layout={chatLayout}
        fullWidth={isFullWidth}
      />
    </div>
  );
}

export default ThreadedComparison; 
