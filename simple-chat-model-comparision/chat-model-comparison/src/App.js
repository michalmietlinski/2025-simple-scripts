import React, { useState, useEffect } from 'react';
import { BrowserRouter, Routes, Route, Link } from 'react-router-dom';
import axios from 'axios';
import ModelComparison from './components/ModelComparison';
import ThreadedComparison from './components/ThreadedComparison';
import './App.css';

function App() {
  const [healthStatus, setHealthStatus] = useState({
    server: 'checking',  // 'checking', 'online', 'offline'
    openai: 'checking'   // 'checking', 'valid', 'invalid'
  });

  useEffect(() => {
    checkHealth();
    const interval = setInterval(checkHealth, 30000); // Check every 30 seconds
    return () => clearInterval(interval);
  }, []);

  const checkHealth = async () => {
    try {
      const response = await axios.get('http://localhost:3001/api/health', {
        timeout: 5000 // 5 second timeout
      });
      if (response.data.status === 'ok') {
        setHealthStatus(prev => ({ ...prev, server: 'online' }));
      } else {
        setHealthStatus(prev => ({ ...prev, server: 'offline' }));
      }
    } catch (error) {
      console.error('Server health check failed:', error);
      setHealthStatus(prev => ({ ...prev, server: 'offline' }));
    }

    try {
      const response = await axios.get('http://localhost:3001/api/models');
      setHealthStatus(prev => ({ 
        ...prev, 
        openai: response.data.length > 0 ? 'valid' : 'invalid' 
      }));
    } catch {
      setHealthStatus(prev => ({ ...prev, openai: 'invalid' }));
    }
  };

  return (
    <BrowserRouter>
      <div className="app-container">
        <nav className="sidebar">
          <div className="status-indicators">
            <div className={`status-item ${healthStatus.server}`}>
              <span className="status-dot"></span>
              Server: {healthStatus.server}
            </div>
            <div className={`status-item ${healthStatus.openai}`}>
              <span className="status-dot"></span>
              OpenAI API: {healthStatus.openai}
            </div>
          </div>

          <div className="nav-section">
            <h3>Navigation</h3>
            <ul>
              <li><Link to="/">Model Comparison</Link></li>
              <li><Link to="/threaded">Threaded Comparison</Link></li>
            </ul>
          </div>

          <div className="help-section">
            <h3>Quick Guide</h3>
            <div className="steps">
              <div className="step">
                <span className="step-number">1</span>
                <p>Select AI models to compare from the available options</p>
              </div>
              <div className="step">
                <span className="step-number">2</span>
                <p>Enter your prompt in the text area</p>
              </div>
              <div className="step">
                <span className="step-number">3</span>
                <p>Click "Compare Responses" to see results</p>
              </div>
              <div className="step">
                <span className="step-number">4</span>
                <p>For threaded chat, continue the conversation after initial response</p>
              </div>
            </div>
          </div>
        </nav>
        <main className="main-content">
          <Routes>
            <Route path="/" element={<ModelComparison />} />
            <Route path="/threaded" element={<ThreadedComparison />} />
          </Routes>
        </main>
      </div>
    </BrowserRouter>
  );
}

export default App;
