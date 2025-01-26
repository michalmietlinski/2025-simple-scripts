import React from 'react';

function ComparisonForm({ 
  prompt, 
  setPrompt, 
  handleSubmit, 
  selectedModels, 
  availableModels, 
  handleModelToggle, 
  modelsLoading, 
  modelsError,
  clearForm 
}) {
  return (
    <>
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
        <div className="form-buttons">
          <button 
            className="clear-form"
            type="button"
            onClick={clearForm}
            disabled={!prompt && selectedModels.length === 0}
          >
            Clear Form
          </button>
          <button 
            type="submit" 
            disabled={!prompt || selectedModels.length === 0}
          >
            Compare Responses
          </button>
        </div>
      </form>
    </>
  );
}

export default ComparisonForm; 
