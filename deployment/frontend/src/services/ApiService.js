import axios from 'axios';

// API base URL from environment or default to local development
const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:9000';
console.log('Using API URL:', API_URL);

/**
 * Service for interacting with the NFG Analytics API
 */
class ApiService {
  /**
   * Create a new chat session
   * @returns {Promise<Object>} Session info
   */
  static async createSession() {
    try {
      const response = await axios.post(`${API_URL}/chat/session`);
      return response.data;
    } catch (error) {
      console.error('Error creating session:', error);
      throw error;
    }
  }

  /**
   * Send a message in a chat session
   * @param {string} sessionId - Chat session ID
   * @param {string} message - Message to send
   * @returns {Promise<Object>} Response with assistant message
   */
  static async sendMessage(sessionId, message) {
    try {
      console.log(`Sending message to ${API_URL}/chat/${sessionId}`, message);
      const response = await axios.post(`${API_URL}/chat/${sessionId}`, {
        query: message
      });
      console.log('API response:', response.data);
      return response.data;
    } catch (error) {
      console.error('Error sending message:', error);
      console.error('Error details:', error.response ? error.response.data : 'No response data');
      console.error('Error status:', error.response ? error.response.status : 'No status');
      throw error;
    }
  }

  /**
   * Get chat history for a session
   * @param {string} sessionId - Chat session ID
   * @returns {Promise<Object>} Chat history
   */
  static async getChatHistory(sessionId) {
    try {
      const response = await axios.get(`${API_URL}/chat/${sessionId}`);
      return response.data;
    } catch (error) {
      console.error('Error getting chat history:', error);
      throw error;
    }
  }

  /**
   * Delete a chat session
   * @param {string} sessionId - Chat session ID
   * @returns {Promise<Object>} Confirmation message
   */
  static async deleteSession(sessionId) {
    try {
      const response = await axios.delete(`${API_URL}/chat/${sessionId}`);
      return response.data;
    } catch (error) {
      console.error('Error deleting session:', error);
      throw error;
    }
  }

  /**
   * Process a single query (without chat context)
   * @param {string} query - Query to process
   * @returns {Promise<Object>} Query result
   */
  static async processQuery(query) {
    try {
      const response = await axios.post(`${API_URL}/query`, { query });
      return response.data;
    } catch (error) {
      console.error('Error processing query:', error);
      throw error;
    }
  }

  /**
   * Check API health status
   * @returns {Promise<Object>} Health status
   */
  static async healthCheck() {
    try {
      const response = await axios.get(`${API_URL}/health`);
      return response.data;
    } catch (error) {
      console.error('API health check failed:', error);
      throw error;
    }
  }
}

export default ApiService;
