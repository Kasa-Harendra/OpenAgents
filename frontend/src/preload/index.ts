import { contextBridge, ipcRenderer } from 'electron';

// Expose protected methods that allow the renderer process to use
// the ipcRenderer without exposing the entire object
contextBridge.exposeInMainWorld('electron', {
  // Add IPC methods here as needed
  platform: process.platform,
});

// Expose API for communicating with FastAPI backend
contextBridge.exposeInMainWorld('api', {
  // Backend URL - can be configured via environment variable
  baseURL: process.env.VITE_API_URL || 'http://localhost:8000',
});
