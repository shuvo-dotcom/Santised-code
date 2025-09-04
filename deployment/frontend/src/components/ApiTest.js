import React, { useState, useEffect } from 'react';
import { Box, Button, Typography, Paper, TextField } from '@mui/material';
import ApiService from '../services/ApiService';

const ApiTest = () => {
  const [healthStatus, setHealthStatus] = useState('');
  const [sessionId, setSessionId] = useState('');
  const [chatResponse, setChatResponse] = useState('');
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState('What is the capacity of system 1?');
  const [error, setError] = useState('');

  const checkHealth = async () => {
    try {
      setLoading(true);
      const result = await ApiService.healthCheck();
      setHealthStatus(JSON.stringify(result, null, 2));
      setError('');
    } catch (err) {
      setError(`Health check failed: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  const createSession = async () => {
    try {
      setLoading(true);
      const result = await ApiService.createSession();
      setSessionId(result.session_id);
      setError('');
    } catch (err) {
      setError(`Session creation failed: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  const sendChatMessage = async () => {
    if (!sessionId) {
      setError('Please create a session first');
      return;
    }
    
    try {
      setLoading(true);
      const result = await ApiService.sendMessage(sessionId, message);
      setChatResponse(JSON.stringify(result, null, 2));
      setError('');
    } catch (err) {
      setError(`Message sending failed: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  return (
    <Paper elevation={3} sx={{ p: 3, mt: 2 }}>
      <Typography variant="h5" gutterBottom>API Test Panel</Typography>
      
      <Box sx={{ mb: 3 }}>
        <Button 
          variant="contained" 
          onClick={checkHealth}
          disabled={loading}
          sx={{ mr: 1 }}
        >
          Check Health
        </Button>
        
        <Typography variant="subtitle1" sx={{ mt: 1 }}>
          Health Status:
        </Typography>
        <Paper variant="outlined" sx={{ p: 1, bgcolor: '#f5f5f5', maxHeight: '100px', overflow: 'auto' }}>
          <pre>{healthStatus || 'Not checked yet'}</pre>
        </Paper>
      </Box>
      
      <Box sx={{ mb: 3 }}>
        <Button 
          variant="contained" 
          onClick={createSession}
          disabled={loading}
          sx={{ mr: 1 }}
        >
          Create Session
        </Button>
        
        <Typography variant="subtitle1" sx={{ mt: 1 }}>
          Session ID:
        </Typography>
        <Paper variant="outlined" sx={{ p: 1, bgcolor: '#f5f5f5' }}>
          {sessionId || 'No session created'}
        </Paper>
      </Box>
      
      <Box sx={{ mb: 3 }}>
        <TextField
          fullWidth
          label="Chat Message"
          value={message}
          onChange={(e) => setMessage(e.target.value)}
          margin="normal"
        />
        
        <Button 
          variant="contained" 
          onClick={sendChatMessage}
          disabled={loading || !sessionId}
          sx={{ my: 1 }}
        >
          Send Message
        </Button>
        
        <Typography variant="subtitle1" sx={{ mt: 1 }}>
          Response:
        </Typography>
        <Paper variant="outlined" sx={{ p: 1, bgcolor: '#f5f5f5', maxHeight: '200px', overflow: 'auto' }}>
          <pre>{chatResponse || 'No response yet'}</pre>
        </Paper>
      </Box>
      
      {error && (
        <Paper variant="outlined" sx={{ p: 1, bgcolor: '#ffebee', mt: 2 }}>
          <Typography color="error">{error}</Typography>
        </Paper>
      )}
      
      {loading && (
        <Typography variant="body2" sx={{ mt: 1, fontStyle: 'italic' }}>
          Loading...
        </Typography>
      )}
    </Paper>
  );
};

export default ApiTest;
