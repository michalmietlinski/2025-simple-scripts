import React from 'react';
import './App.css';
import ModelComparison from './components/ModelComparison';

function App() {
  return (
    <div className="App">
      <header className="App-header">
        <h1>GPT Model Comparison</h1>
      </header>
      <main>
        <ModelComparison />
      </main>
    </div>
  );
}

export default App;
