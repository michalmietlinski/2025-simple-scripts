import React from 'react';
import './ThreadedChat.css';

function ThreadedChat({ 
  messages, 
  selectedModels,
  loading,
  layout = 'stacked',
  fullWidth = false
}) {
  const groupedMessages = [];
  for (let i = 0; i < messages.length; i++) {
    if (messages[i].role === 'user') {
      const responses = messages
        .slice(i + 1, i + 1 + selectedModels.length)
        .filter(m => m.role === 'assistant');
      groupedMessages.push({
        question: messages[i],
        responses
      });
      i += selectedModels.length;
    }
  }

  return (
    <div className={`threaded-chat ${fullWidth ? 'full-width' : ''}`}>
      <div className="chat-messages">
        {[...groupedMessages].reverse().map((group, index) => (
          <div key={index} className="conversation-turn">
            <div className="message user">
              <div className="message-content">{group.question.content}</div>
            </div>
            
            <div className={`responses ${layout}`}>
              {group.responses.map((response, rIndex) => (
                <div key={rIndex} className="message assistant">
                  <div className="model-name">{response.model}</div>
                  <div className="message-content">{response.content}</div>
                </div>
              ))}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

export default ThreadedChat; 
