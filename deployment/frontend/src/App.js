import React, { useState, useEffect } from 'react';
import { Container, Box, Tabs, Tab } from '@mui/material';
import Header from './components/Header';
import ChatInterface from './components/ChatInterface';
import ApiTest from './components/ApiTest';
import ApiService from './services/ApiService';
import { v4 as uuidv4 } from 'uuid';

function App() {
  const [sessionId, setSessionId] = useState(null);
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(false);
  const [tabIndex, setTabIndex] = useState(0);

  const handleTabChange = (event, newIndex) => {
    setTabIndex(newIndex);
  };

  // Initialize chat session on component mount
  useEffect(() => {
    const initializeSession = async () => {
      try {
        const response = await ApiService.createSession();
        setSessionId(response.session_id);
      } catch (error) {
        console.error('Failed to create chat session:', error);
        // Use client-side session ID as fallback
        setSessionId(uuidv4());
      }
    };

    initializeSession();

    // Add welcome message
    setMessages([{
      id: uuidv4(),
      role: 'assistant',
      content: 'Welcome to NFG Energy Analytics! How can I help you with energy-related calculations and analysis today?',
      timestamp: new Date().toISOString()
    }]);

    // Cleanup on unmount
    return () => {
      if (sessionId) {
        // Optional: End the session when component unmounts
        ApiService.deleteSession(sessionId).catch(console.error);
      }
    };
  }, []);

  const handleSendMessage = async (message) => {
    if (!message.trim()) return;

    // Add user message to state
    const userMessage = {
      id: uuidv4(),
      role: 'user',
      content: message,
      timestamp: new Date().toISOString()
    };

    setMessages(prevMessages => [...prevMessages, userMessage]);
    setLoading(true);

    try {
      // Send message to API
      const response = await ApiService.sendMessage(sessionId, message);
      
      // Add assistant response to state
      const assistantMessage = {
        id: uuidv4(),
        role: 'assistant',
        content: response.message.content,
        timestamp: response.message.timestamp,
        rawResult: response.message.raw_result
      };

      setMessages(prevMessages => [...prevMessages, assistantMessage]);
    } catch (error) {
      console.error('Error sending message:', error);
      
      // Add error message
      const errorMessage = {
        id: uuidv4(),
        role: 'assistant',
        content: 'Sorry, there was an error processing your request. Please try again later.',
        timestamp: new Date().toISOString(),
        error: true
      };

      setMessages(prevMessages => [...prevMessages, errorMessage]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', height: '100vh' }}>
      <Header />
      <Container maxWidth="lg" sx={{ flexGrow: 1, display: 'flex', flexDirection: 'column' }}>
        <Tabs value={tabIndex} onChange={handleTabChange} sx={{ mb: 2 }}>
          <Tab label="Chat Interface" />
          <Tab label="API Test" />
        </Tabs>
        
        {tabIndex === 0 ? (
          <ChatInterface 
            messages={messages} 
            onSendMessage={handleSendMessage} 
            loading={loading} 
          />
        ) : (
          <ApiTest />
        )}
      </Container>
    </Box>
  );
}

export default App;
