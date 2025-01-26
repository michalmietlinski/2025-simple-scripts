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

  return (
    <div className="model-comparison">
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
