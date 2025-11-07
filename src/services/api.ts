import axios from 'axios';

// Centralized API configuration
// Change baseURL for production deployment
const api = axios.create({
  baseURL: 'http://localhost:8000',
  timeout: 60000,
});

export default api;
