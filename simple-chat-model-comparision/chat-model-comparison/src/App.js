import React from 'react';
import { BrowserRouter, Routes, Route, Link } from 'react-router-dom';
import ModelComparison from './components/ModelComparison';
import ThreadedComparison from './components/ThreadedComparison';
import './App.css';

function App() {
  return (
    <BrowserRouter>
      <div className="app-container">
        <nav className="sidebar">
          <ul>
            <li><Link to="/">Model Comparison</Link></li>
            <li><Link to="/threaded">Threaded Comparison</Link></li>
          </ul>
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
