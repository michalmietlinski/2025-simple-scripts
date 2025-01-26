import React from 'react';

function ResponseGrid({ 
  selectedModels, 
  availableModels, 
  loading, 
  responses, 
  savedFileName 
}) {
  return (
    <>
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
    </>
  );
}

export default ResponseGrid; 
