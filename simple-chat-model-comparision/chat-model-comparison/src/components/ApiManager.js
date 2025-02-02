import React, { useState, useEffect } from 'react';
import axios from 'axios';
import './ApiManager.css';

const API_CHANGE_EVENT = 'api-config-changed';

function ApiManager() {
  const [apis, setApis] = useState([]);
  const [newApiKey, setNewApiKey] = useState('');
  const [newApiName, setNewApiName] = useState('');
  const [newProvider, setNewProvider] = useState('openai');
  const [newApiUrl, setNewApiUrl] = useState('');
  const [isAdding, setIsAdding] = useState(false);

  useEffect(() => {
    fetchApis();
  }, []);

  const fetchApis = async () => {
    try {
      const response = await axios.get('http://localhost:3001/api/provider-apis');
      setApis(response.data);
    } catch (error) {
      console.error('Error fetching APIs:', error);
    }
  };

  const notifyApiChange = () => {
    window.dispatchEvent(new Event(API_CHANGE_EVENT));
  };

  const addApi = async (e) => {
    e.preventDefault();
    if (newApiKey && newApiName) {
      try {
        await axios.post('http://localhost:3001/api/provider-apis', {
          name: newApiName,
          key: newApiKey,
          provider: newProvider,
          url: newApiUrl
        });
        
        setNewApiKey('');
        setNewApiName('');
        setNewProvider('openai');
        setNewApiUrl('');
        setIsAdding(false);
        await fetchApis();
        notifyApiChange();
      } catch (error) {
        console.error('Error adding API:', error);
      }
    }
  };

  const removeApi = async (id) => {
    try {
      await axios.delete(`http://localhost:3001/api/provider-apis/${id}`);
      await fetchApis();
      notifyApiChange();
    } catch (error) {
      console.error('Error removing API:', error);
    }
  };

  const toggleApiStatus = async (id, currentActive) => {
    try {
      await axios.patch(`http://localhost:3001/api/provider-apis/${id}`, {
        active: !currentActive
      });
      await fetchApis();
      notifyApiChange();
    } catch (error) {
      console.error('Error toggling API status:', error);
    }
  };

  return (
    <div className="api-manager">
      <div className="api-header">
        <h3>API Keys</h3>
        <button 
          className="add-api-button"
          onClick={() => setIsAdding(!isAdding)}
        >
          {isAdding ? '−' : '+'}
        </button>
      </div>

      {isAdding && (
        <form onSubmit={addApi} className="add-api-form">
          <input
            type="text"
            placeholder="API Name"
            value={newApiName}
            onChange={(e) => setNewApiName(e.target.value)}
          />
          <select
            value={newProvider}
            onChange={(e) => setNewProvider(e.target.value)}
          >
            <option value="openai">OpenAI</option>
            <option value="deepseek">DeepSeek</option>
            <option value="anthropic">Anthropic</option>
            <option value="custom">Custom Provider</option>
          </select>
          {newProvider === 'custom' && (
            <input
              type="text"
              placeholder="API URL (e.g., https://api.example.com/v1)"
              value={newApiUrl}
              onChange={(e) => setNewApiUrl(e.target.value)}
            />
          )}
          <input
            type="password"
            placeholder="API Key"
            value={newApiKey}
            onChange={(e) => setNewApiKey(e.target.value)}
          />
          <button type="submit">Add</button>
        </form>
      )}

      <div className="api-list">
        {apis.map(api => (
          <div key={api.id} className="api-item">
            <div className="api-item-header">
              <span className="api-name">
                {api.name}
                <span className="api-provider">({api.provider})</span>
              </span>
             
              <div className="api-controls">
                <button
                  className={`status-toggle ${api.active ? 'active' : ''}`}
                  onClick={() => toggleApiStatus(api.id, api.active)}
                >
                  {api.active ? 'Active' : 'Inactive'}
                </button>
                <button
                  className="remove-api"
                  onClick={() => removeApi(api.id)}
                >
                  ×
                </button>
              </div>
            </div>
			{api.url && (
                <div className="api-url">{api.url}</div>
              )}
            <div className="api-key">
              {api.key.replace(/./g, '•')}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

export { API_CHANGE_EVENT };
export default ApiManager; 
