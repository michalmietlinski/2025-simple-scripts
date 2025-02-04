# WebRTC Chat Playground

A simple WebRTC-based chat application created as a testing/learning playground. This project demonstrates basic WebRTC peer-to-peer communication with features like:

- Direct peer-to-peer messaging
- File sharing
- Offline message support
- Message history
- Conversation management

## Status

⚠️ **Note: This is a testing/playground project**

This project was created for learning and experimentation purposes. It has served its purpose and will not be actively expanded. Feel free to use it as a reference for understanding basic WebRTC concepts and implementation.

## Features Implemented

- ✅ WebRTC peer connection setup
- ✅ Direct messaging between peers
- ✅ File sharing capabilities
- ✅ Message history and synchronization
- ✅ Basic UI for chat and connections
- ✅ Offline message support
- ✅ Conversation management

## Technical Stack

- Frontend: Vanilla JavaScript (ES6+) with modules
- Backend: Simple Node.js server for signaling
- WebRTC for peer-to-peer communication
- No external dependencies for core functionality

## Project Structure

The project follows a modular architecture with clear separation of concerns:

```
public/js/
  ├── api.js         (API service)
  ├── config.js      (configuration)
  ├── connection.js  (WebRTC handling)
  ├── conversation.js (conversation management)
  ├── events.js      (event handlers)
  ├── exports.js     (window exports)
  ├── main.js        (main orchestrator)
  ├── message.js     (message handling)
  ├── state.js       (app state)
  ├── ui.js          (UI helpers)
  └── utils.js       (utilities)
```

## Learning Outcomes

This project helped in understanding:
- WebRTC peer connection setup and management
- Real-time data channels
- Message synchronization strategies
- Modular JavaScript architecture
- State management without frameworks 
