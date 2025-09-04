import React from 'react';
import { Box, Typography, Paper } from '@mui/material';
import ReactMarkdown from 'react-markdown';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { tomorrow } from 'react-syntax-highlighter/dist/esm/styles/prism';

const MessageBubble = ({ message }) => {
  const isUser = message.role === 'user';
  
  // Format timestamp if available
  const formattedTime = message.timestamp ? 
    new Date(message.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) : '';
  
  return (
    <Box 
      sx={{ 
        display: 'flex',
        flexDirection: 'column',
        alignItems: isUser ? 'flex-end' : 'flex-start',
        mb: 2
      }}
    >
      <Box 
        className={isUser ? 'user-message' : 'assistant-message'}
        sx={{
          maxWidth: '85%',
          position: 'relative',
          ...(message.error && { 
            backgroundColor: 'error.light', 
            color: 'error.contrastText' 
          })
        }}
      >
        <ReactMarkdown
          components={{
            code({node, inline, className, children, ...props}) {
              const match = /language-(\w+)/.exec(className || '')
              return !inline && match ? (
                <SyntaxHighlighter
                  style={tomorrow}
                  language={match[1]}
                  PreTag="div"
                  {...props}
                >
                  {String(children).replace(/\n$/, '')}
                </SyntaxHighlighter>
              ) : (
                <code className={className} {...props}>
                  {children}
                </code>
              )
            }
          }}
        >
          {message.content}
        </ReactMarkdown>

        {/* Display data visualization if available */}
        {message.rawResult && message.rawResult.chart_data && (
          <Paper elevation={1} sx={{ mt: 2, p: 2 }}>
            <Typography variant="subtitle2" sx={{ mb: 1 }}>
              {message.rawResult.chart_title || 'Energy Data Visualization'}
            </Typography>
            {/* Visualization placeholder - in a real app, this would render a chart */}
            <Box 
              sx={{ 
                height: 200, 
                backgroundColor: 'action.hover',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center'
              }}
            >
              <Typography variant="body2" color="text.secondary">
                [Chart visualization would render here]
              </Typography>
            </Box>
          </Paper>
        )}

        {/* Timestamp */}
        <Typography 
          variant="caption" 
          sx={{ 
            display: 'block',
            color: 'text.secondary',
            mt: 0.5,
            textAlign: isUser ? 'right' : 'left'
          }}
        >
          {formattedTime}
        </Typography>
      </Box>
    </Box>
  );
};

export default MessageBubble;
