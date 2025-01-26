import React from 'react';

function HistoryPanel({ 
  showHistory, 
  setShowHistory, 
  logs, 
  logsLoading, 
  loadConversation, 
  deleteConversation, 
  clearAllHistory,
  deletingLogs 
}) {
  return (
    <>
      <div className="controls">
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
    </>
  );
}

export default HistoryPanel; 
