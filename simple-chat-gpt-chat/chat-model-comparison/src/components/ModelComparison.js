import React, { useState, useEffect } from 'react';
import axios from 'axios';
import './ModelComparison.css';

function ModelComparison() {
  const [prompt, setPrompt] = useState('');
  const [responses, setResponses] = useState({});
  const [loading, setLoading] = useState({});
  const [savedFileName, setSavedFileName] = useState(null);
  const [availableModels, setAvailableModels] = useState([]);
  const [selectedModels, setSelectedModels] = useState([]);
  const [modelsLoading, setModelsLoading] = useState(true);
  const [modelsError, setModelsError] = useState(null);
  const [logs, setLogs] = useState([]);
  const [logsLoading, setLogsLoading] = useState(false);
  const [showHistory, setShowHistory] = useState(false);
  const [deletingLogs, setDeletingLogs] = useState({});

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
        // Select first two models by default if available
        if (models.length > 0) {
          setSelectedModels([models[0].id, models.length > 1 ? models[1].id : models[0].id]);
        }
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
    const fetchLogs = async () => {
      try {
        setLogsLoading(true);
        const response = await axios.get('http://localhost:3001/api/logs');
        setLogs(response.data);
      } catch (error) {
        console.error('Error fetching logs:', error);
      } finally {
        setLogsLoading(false);
      }
    };

    fetchLogs();
  }, []);

  const formatModelName = (modelId) => {
    return modelId
      .replace('gpt-', 'GPT-')
      .split('-')
      .map(word => word === 'turbo' ? 'Turbo' : word)
      .join(' ');
  };

  const handleModelToggle = (modelId) => {
    setSelectedModels(prev => 
      prev.includes(modelId)
        ? prev.filter(id => id !== modelId)
        : [...prev, modelId]
    );
  };

  const fetchResponses = async () => {
    try {
      selectedModels.forEach(model => {
        setLoading(prev => ({ ...prev, [model]: true }));
      });

      const response = await axios.post('http://localhost:3001/api/chat', {
        models: selectedModels,
        prompt,
      });

      const newResponses = {};
      response.data.responses.forEach(r => {
        newResponses[r.model] = r.response;
      });

      setResponses(newResponses);
      setSavedFileName(response.data.fileName);

    } catch (error) {
      const errorResponses = {};
      selectedModels.forEach(model => {
        errorResponses[model] = `Error: ${error.message}`;
      });
      setResponses(errorResponses);
    } finally {
      selectedModels.forEach(model => {
        setLoading(prev => ({ ...prev, [model]: false }));
      });
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setResponses({});
    setSavedFileName(null);
    
    await fetchResponses();
  };

  const loadConversation = (conversation) => {
    setPrompt(conversation.prompt);
    const models = conversation.responses.map(r => r.model);
    setSelectedModels(models);
    const newResponses = {};
    conversation.responses.forEach(r => {
      newResponses[r.model] = r.response;
    });
    setResponses(newResponses);
    setSavedFileName(conversation.fileName);
    setShowHistory(false);
  };

  const clearForm = () => {
    setPrompt('');
    setResponses({});
    setSavedFileName(null);
  };

  const deleteConversation = async (date, fileName, event) => {
    // Prevent triggering loadConversation when clicking delete button
    event.stopPropagation();
    
    try {
      setDeletingLogs(prev => ({ ...prev, [fileName]: true }));
      await axios.delete(`http://localhost:3001/api/logs/${date}/${fileName}`);
      setLogs(prev => prev.filter(log => log.fileName !== fileName));
    } catch (error) {
      console.error('Error deleting conversation:', error);
    } finally {
      setDeletingLogs(prev => ({ ...prev, [fileName]: false }));
    }
  };

  const clearAllHistory = async () => {
    if (window.confirm('Are you sure you want to clear all history? This cannot be undone.')) {
      try {
        await axios.delete('http://localhost:3001/api/logs');
        setLogs([]);
      } catch (error) {
        console.error('Error clearing history:', error);
      }
    }
  };

  return (
    <div className="model-comparison">
      <div className="controls">
        <button 
          className="clear-form"
          onClick={clearForm}
          disabled={!prompt && Object.keys(responses).length === 0}
        >
          Clear Form
        </button>
        <button 
          className="history-toggle"
          onClick={() => setShowHistory(!showHistory)}
        >
          {showHistory ? 'Hide History' : 'Show History'}
        </button>
      </div>

      {showHistory && (
        <div className="history-panel">
          <h2>
            Conversation History
            {logs.length > 0 && (
              <button 
                className="clear-all-history"
                onClick={clearAllHistory}
              >
                Clear All History
              </button>
            )}
          </h2>
          {logsLoading ? (
            <div className="loading">Loading history...</div>
          ) : logs.length === 0 ? (
            <div className="no-history">No previous conversations found</div>
          ) : (
            <div className="history-list">
              {logs.map((log, index) => (
                <div key={index} className="history-item" onClick={() => loadConversation(log)}>
                  <div className="history-date">
                    {new Date(log.timestamp).toLocaleString()}
                    <button
                      className="delete-conversation"
                      onClick={(e) => deleteConversation(log.date, log.fileName, e)}
                      disabled={deletingLogs[log.fileName]}
                    >
                      {deletingLogs[log.fileName] ? 'Deleting...' : '×'}
                    </button>
                  </div>
                  <div className="history-prompt">{log.prompt.substring(0, 100)}...</div>
                  <div className="history-models">
                    Models: {log.responses.map(r => r.model).join(', ')}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      <div className="model-selection">
        {modelsLoading ? (
          <div className="loading">Loading available models...</div>
        ) : modelsError ? (
          <div className="error">{modelsError}</div>
        ) : availableModels.map(model => (
          <label key={model.id}>
            <input
              type="checkbox"
              checked={selectedModels.includes(model.id)}
              onChange={() => handleModelToggle(model.id)}
            />
            {model.name}
          </label>
        ))}
      </div>

      <form onSubmit={handleSubmit}>
        <textarea
          value={prompt}
          onChange={(e) => setPrompt(e.target.value)}
          placeholder="Enter your prompt here..."
          rows={4}
        />
        <button type="submit" disabled={!prompt || selectedModels.length === 0}>
          Compare Responses
        </button>
      </form>

      {savedFileName && (
        <div className="save-info">
          Conversation saved to: {savedFileName}
        </div>
      )}

      <div className="responses-grid">
        {selectedModels.map(model => (
          <div key={model} className="response-card">
            <h3>{availableModels.find(m => m.id === model)?.name || model}</h3>
            {loading[model] ? (
              <div className="loading">Loading...</div>
            ) : (
              <pre>{responses[model] || 'No response yet'}</pre>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}

export default ModelComparison; 
