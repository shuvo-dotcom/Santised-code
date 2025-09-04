import React, { useState, useRef, useEffect } from 'react';
import { 
  Box, 
  Paper, 
  TextField, 
  Button, 
  Typography, 
  IconButton,
  CircularProgress
} from '@mui/material';
import SendIcon from '@mui/icons-material/Send';
import DeleteIcon from '@mui/icons-material/Delete';
import MessageBubble from './MessageBubble';

const ChatInterface = ({ messages, onSendMessage, loading }) => {
  const [input, setInput] = useState('');
  const messagesEndRef = useRef(null);
  const chatContainerRef = useRef(null);

  // Auto-scroll to bottom when messages change
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleSend = (e) => {
    e.preventDefault();
    if (input.trim() && !loading) {
      onSendMessage(input);
      setInput('');
    }
  };

  const handleClearInput = () => {
    setInput('');
  };

  return (
    <Paper 
      elevation={3} 
      sx={{ 
        display: 'flex', 
        flexDirection: 'column',
        height: '100%',
        maxHeight: 'calc(100vh - 100px)',
        my: 2,
        borderRadius: 2,
        overflow: 'hidden'
      }}
    >
      {/* Chat Header */}
      <Box sx={{ 
        p: 2, 
        backgroundColor: 'primary.main', 
        color: 'white' 
      }}>
        <Typography variant="h6">
          NFG Energy Analytics Assistant
        </Typography>
        <Typography variant="body2">
          Ask questions about energy metrics, calculations, and data analysis
        </Typography>
      </Box>
      
      {/* Messages Container */}
      <Box 
        ref={chatContainerRef}
        sx={{ 
          flexGrow: 1, 
          overflowY: 'auto', 
          p: 2,
          backgroundColor: 'background.default',
          display: 'flex',
          flexDirection: 'column'
        }}
      >
        {messages.map((message) => (
          <MessageBubble key={message.id} message={message} />
        ))}
        
        {loading && (
          <Box 
            className="assistant-message loading-message"
            sx={{ display: 'flex', alignItems: 'center' }}
          >
            <CircularProgress size={20} sx={{ mr: 1 }} />
            <Typography>Processing your request...</Typography>
          </Box>
        )}
        
        <div ref={messagesEndRef} />
      </Box>
      
      {/* Input Area */}
      <Box 
        component="form" 
        onSubmit={handleSend}
        sx={{ 
          p: 2, 
          backgroundColor: 'background.paper',
          borderTop: 1, 
          borderColor: 'divider',
          display: 'flex'
        }}
      >
        <TextField
          fullWidth
          variant="outlined"
          placeholder="Ask about energy metrics, calculations, or data analysis..."
          value={input}
          onChange={(e) => setInput(e.target.value)}
          sx={{ mr: 1 }}
          disabled={loading}
          InputProps={{
            endAdornment: input && (
              <IconButton size="small" onClick={handleClearInput}>
                <DeleteIcon fontSize="small" />
              </IconButton>
            )
          }}
        />
        <Button 
          variant="contained" 
          color="primary" 
          endIcon={<SendIcon />}
          type="submit"
          disabled={!input.trim() || loading}
        >
          Send
        </Button>
      </Box>
    </Paper>
  );
};

export default ChatInterface;
