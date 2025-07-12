import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import './App.css';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

function App() {
  const [messages, setMessages] = useState([]);
  const [inputMessage, setInputMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [ollamaHealth, setOllamaHealth] = useState({ status: 'checking' });
  const [availableModels, setAvailableModels] = useState([]);
  const [selectedModel, setSelectedModel] = useState('llama3.2:latest');
  const [streamingEnabled, setStreamingEnabled] = useState(false);
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  useEffect(() => {
    checkOllamaHealth();
    fetchModels();
    loadChatHistory();
  }, []);

  const checkOllamaHealth = async () => {
    try {
      const response = await axios.get(`${API}/ollama/health`);
      setOllamaHealth(response.data);
    } catch (error) {
      console.error('Error checking Ollama health:', error);
      setOllamaHealth({ status: 'error', error: 'Failed to check Ollama status' });
    }
  };

  const fetchModels = async () => {
    try {
      const response = await axios.get(`${API}/ollama/models`);
      if (response.data.models) {
        setAvailableModels(response.data.models);
      }
    } catch (error) {
      console.error('Error fetching models:', error);
    }
  };

  const loadChatHistory = async () => {
    try {
      const response = await axios.get(`${API}/chat/history`);
      const history = response.data.slice(0, 10).reverse(); // Get last 10 messages
      const formattedHistory = history.flatMap(chat => [
        { type: 'user', content: chat.message, timestamp: chat.timestamp },
        { type: 'assistant', content: chat.response, timestamp: chat.timestamp, model: chat.model }
      ]);
      setMessages(formattedHistory);
    } catch (error) {
      console.error('Error loading chat history:', error);
    }
  };

  const sendMessage = async () => {
    if (!inputMessage.trim()) return;

    const userMessage = {
      type: 'user',
      content: inputMessage,
      timestamp: new Date().toISOString()
    };

    setMessages(prev => [...prev, userMessage]);
    setInputMessage('');
    setIsLoading(true);

    try {
      if (streamingEnabled) {
        await handleStreamingResponse(inputMessage);
      } else {
        await handleRegularResponse(inputMessage);
      }
    } catch (error) {
      console.error('Error sending message:', error);
      const errorMessage = {
        type: 'assistant',
        content: 'Sorry, I encountered an error. Please make sure Ollama is running and try again.',
        timestamp: new Date().toISOString(),
        isError: true
      };
      setMessages(prev => [...prev, errorMessage]);
    }

    setIsLoading(false);
  };

  const handleRegularResponse = async (message) => {
    const response = await axios.post(`${API}/ollama/chat`, {
      message: message,
      model: selectedModel,
      stream: false
    });

    const assistantMessage = {
      type: 'assistant',
      content: response.data.response,
      timestamp: new Date().toISOString(),
      model: response.data.model
    };

    setMessages(prev => [...prev, assistantMessage]);
  };

  const handleStreamingResponse = async (message) => {
    const assistantMessage = {
      type: 'assistant',
      content: '',
      timestamp: new Date().toISOString(),
      model: selectedModel,
      isStreaming: true
    };

    setMessages(prev => [...prev, assistantMessage]);

    try {
      const response = await fetch(`${API}/ollama/chat/stream`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          message: message,
          model: selectedModel,
          stream: true
        }),
      });

      const reader = response.body.getReader();
      const decoder = new TextDecoder();

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        const chunk = decoder.decode(value);
        const lines = chunk.split('\n');

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            try {
              const data = JSON.parse(line.slice(6));
              if (data.response) {
                setMessages(prev => prev.map((msg, index) => 
                  index === prev.length - 1 
                    ? { ...msg, content: msg.content + data.response }
                    : msg
                ));
              }
              if (data.done) {
                setMessages(prev => prev.map((msg, index) => 
                  index === prev.length - 1 
                    ? { ...msg, isStreaming: false }
                    : msg
                ));
              }
              if (data.error) {
                setMessages(prev => prev.map((msg, index) => 
                  index === prev.length - 1 
                    ? { ...msg, content: data.error, isError: true, isStreaming: false }
                    : msg
                ));
                break;
              }
            } catch (e) {
              console.error('Error parsing streaming response:', e);
            }
          }
        }
      }
    } catch (error) {
      console.error('Error with streaming response:', error);
      setMessages(prev => prev.map((msg, index) => 
        index === prev.length - 1 
          ? { ...msg, content: 'Error: Failed to stream response from Ollama', isError: true, isStreaming: false }
          : msg
      ));
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  const clearChat = () => {
    setMessages([]);
  };

  const getHealthStatusColor = () => {
    switch (ollamaHealth.status) {
      case 'healthy': return 'text-green-500';
      case 'offline': return 'text-red-500';
      case 'error': return 'text-red-500';
      case 'checking': return 'text-yellow-500';
      default: return 'text-gray-500';
    }
  };

  const getHealthStatusText = () => {
    switch (ollamaHealth.status) {
      case 'healthy': return `Ollama Online (${ollamaHealth.models_available || 0} models)`;
      case 'offline': return 'Ollama Offline';
      case 'error': return 'Ollama Error';
      case 'checking': return 'Checking Ollama...';
      default: return 'Unknown Status';
    }
  };

  return (
    <div className="flex flex-col h-screen bg-gray-900 text-white">
      {/* Header */}
      <div className="bg-gray-800 p-4 border-b border-gray-700">
        <div className="flex items-center justify-between">
          <h1 className="text-2xl font-bold">Ollama Chat Interface</h1>
          <div className="flex items-center space-x-4">
            <div className={`flex items-center space-x-2 ${getHealthStatusColor()}`}>
              <div className="w-3 h-3 rounded-full bg-current"></div>
              <span className="text-sm">{getHealthStatusText()}</span>
            </div>
            <button
              onClick={checkOllamaHealth}
              className="px-3 py-1 bg-blue-600 hover:bg-blue-700 rounded text-sm"
            >
              Refresh
            </button>
          </div>
        </div>
        
        {/* Controls */}
        <div className="flex items-center justify-between mt-4">
          <div className="flex items-center space-x-4">
            <select
              value={selectedModel}
              onChange={(e) => setSelectedModel(e.target.value)}
              className="bg-gray-700 text-white px-3 py-2 rounded"
              disabled={availableModels.length === 0}
            >
              <option value="llama3.2:latest">llama3.2:latest (default)</option>
              {availableModels.map(model => (
                <option key={model.name} value={model.name}>
                  {model.name}
                </option>
              ))}
            </select>
            
            <label className="flex items-center space-x-2">
              <input
                type="checkbox"
                checked={streamingEnabled}
                onChange={(e) => setStreamingEnabled(e.target.checked)}
                className="form-checkbox text-blue-500"
              />
              <span className="text-sm">Streaming</span>
            </label>
          </div>
          
          <button
            onClick={clearChat}
            className="px-4 py-2 bg-red-600 hover:bg-red-700 rounded text-sm"
          >
            Clear Chat
          </button>
        </div>
      </div>

      {/* Chat Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.length === 0 ? (
          <div className="text-center text-gray-400 mt-8">
            <h3 className="text-xl mb-2">Welcome to Ollama Chat!</h3>
            <p>Start a conversation with your local AI assistant.</p>
            {ollamaHealth.status === 'offline' && (
              <div className="mt-4 p-4 bg-yellow-900 border border-yellow-600 rounded">
                <p className="text-yellow-300">
                  Ollama is not running. Please start Ollama on your system and refresh the connection.
                </p>
              </div>
            )}
          </div>
        ) : (
          messages.map((message, index) => (
            <div key={index} className={`flex ${message.type === 'user' ? 'justify-end' : 'justify-start'}`}>
              <div className={`max-w-3xl p-3 rounded-lg ${
                message.type === 'user' 
                  ? 'bg-blue-600 text-white' 
                  : message.isError 
                    ? 'bg-red-900 text-red-100 border border-red-600'
                    : 'bg-gray-700 text-gray-100'
              }`}>
                <div className="whitespace-pre-wrap">
                  {message.content}
                  {message.isStreaming && <span className="animate-pulse">▊</span>}
                </div>
                {message.type === 'assistant' && message.model && (
                  <div className="text-xs text-gray-400 mt-1">
                    Model: {message.model}
                  </div>
                )}
              </div>
            </div>
          ))
        )}
        {isLoading && (
          <div className="flex justify-start">
            <div className="bg-gray-700 text-gray-100 p-3 rounded-lg">
              <div className="flex items-center space-x-2">
                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-500"></div>
                <span>Thinking...</span>
              </div>
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Input Area */}
      <div className="bg-gray-800 p-4 border-t border-gray-700">
        <div className="flex space-x-2">
          <textarea
            value={inputMessage}
            onChange={(e) => setInputMessage(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="Type your message... (Press Enter to send, Shift+Enter for new line)"
            className="flex-1 bg-gray-700 text-white p-3 rounded-lg resize-none focus:outline-none focus:ring-2 focus:ring-blue-500"
            rows="2"
            disabled={isLoading}
          />
          <button
            onClick={sendMessage}
            disabled={isLoading || !inputMessage.trim()}
            className="px-6 py-3 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-600 disabled:cursor-not-allowed rounded-lg font-medium"
          >
            Send
          </button>
        </div>
      </div>
    </div>
  );
}

export default App;