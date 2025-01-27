import React from 'react';
import './ThreadHistoryPanel.css';

function ThreadHistoryPanel({ 
  showHistory, 
  setShowHistory, 
  threads,
  threadsLoading,
  loadThread,
  deleteThread,
  clearAllThreads,
  deletingThreads 
}) {
  const formatDate = (timestamp) => {
    const date = new Date(timestamp);
    return date.toLocaleDateString() + ' ' + date.toLocaleTimeString([], { 
      hour: '2-digit', 
      minute: '2-digit' 
    });
  };

  const truncatePrompt = (prompt, maxLength = 100) => {
    return prompt.length > maxLength 
      ? prompt.substring(0, maxLength) + '...'
      : prompt;
  };

  return (
    <>
      <div className="controls">
        <button 
          className="history-toggle"
          onClick={() => setShowHistory(!showHistory)}
        >
          {showHistory ? 'Hide Threads' : 'Show Threads'}
        </button>
      </div>

      {showHistory && (
        <div className="thread-history-panel">
          <h2>
            Thread History
            {threads.length > 0 && (
              <button 
                className="clear-all-history"
                onClick={clearAllThreads}
              >
                Clear All Threads
              </button>
            )}
          </h2>
          
          {threadsLoading ? (
            <div className="loading">Loading threads...</div>
          ) : threads.length === 0 ? (
            <div className="no-history">No previous threads found</div>
          ) : (
            <div className="thread-list">
              {threads.map((thread) => (
                <div key={thread.id} className="thread-item" onClick={() => loadThread(thread.id)}>
                  <div className="thread-header">
                    <div className="thread-info">
                      <span className="thread-timestamp">{formatDate(thread.timestamp)}</span>
                      <span className="thread-id">#{thread.shortId}</span>
                    </div>
                    <button
                      className="delete-thread"
                      onClick={(e) => {
                        e.stopPropagation();
                        deleteThread(thread.id);
                      }}
                      disabled={deletingThreads[thread.id]}
                    >
                      {deletingThreads[thread.id] ? 'Deleting...' : '×'}
                    </button>
                  </div>
                  <div className="thread-prompt">{truncatePrompt(thread.firstPrompt)}</div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </>
  );
}

export default ThreadHistoryPanel; 
