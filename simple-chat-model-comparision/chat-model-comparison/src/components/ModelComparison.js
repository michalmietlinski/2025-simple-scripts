import React, { useState, useEffect } from 'react';
import axios from 'axios';
import './ModelComparison.css';
import ComparisonForm from './ComparisonForm';
import ResponseGrid from './ResponseGrid';
import HistoryPanel from './HistoryPanel';
import { API_CHANGE_EVENT } from './ApiManager';

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
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [apis, setApis] = useState([]);
  const [selectedApiId, setSelectedApiId] = useState(null);

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

    // Add event listener for API changes
    const handleApiChange = () => {
      fetchModels();
    };
    window.addEventListener(API_CHANGE_EVENT, handleApiChange);

    // Cleanup
    return () => {
      window.removeEventListener(API_CHANGE_EVENT, handleApiChange);
    };
  }, []);

  useEffect(() => {
    const savedApis = localStorage.getItem('apis');
    if (savedApis) {
      const parsedApis = JSON.parse(savedApis);
      setApis(parsedApis);
      const activeApi = parsedApis.find(api => api.active);
      if (activeApi) {
        setSelectedApiId(activeApi.id);
      }
    }
  }, []);

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

  useEffect(() => {
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
      setIsSubmitting(true);
      selectedModels.forEach(model => {
        setLoading(prev => ({ ...prev, [model]: true }));
      });

      const activeApi = apis.find(api => api.id === selectedApiId);
      
      const response = await axios.post('http://localhost:3001/api/chat', {
        models: selectedModels,
        prompt,
        apiKey: activeApi?.key
      });
	  console.log(response.data);
      const newResponses = {};
      response.data.responses.forEach(r => {
        newResponses[r.model] = r.response;
      });

      setResponses(newResponses);
      setSavedFileName(response.data.fileName);
      fetchLogs();

    } catch (error) {
      const errorResponses = {};
      selectedModels.forEach(model => {
        errorResponses[model] = `Error: ${error.message}`;
      });
      setResponses(errorResponses);
    } finally {
      setIsSubmitting(false);
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
      <HistoryPanel 
        showHistory={showHistory}
        setShowHistory={setShowHistory}
        logs={logs}
        logsLoading={logsLoading}
        loadConversation={loadConversation}
        deleteConversation={deleteConversation}
        clearAllHistory={clearAllHistory}
        deletingLogs={deletingLogs}
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
        isSubmitting={isSubmitting}
      />

      <ResponseGrid 
        selectedModels={selectedModels}
        availableModels={availableModels}
        loading={loading}
        responses={responses}
        savedFileName={savedFileName}
      />
    </div>
  );
}

export default ModelComparison; 
