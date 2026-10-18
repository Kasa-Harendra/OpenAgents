import React, { useEffect } from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import { AnimatePresence } from 'framer-motion';
import { useTaskStore } from './stores/taskStore';
import { useThemeStore } from './stores/themeStore';
import AppLayout from './components/AppLayout';
import ChatWindow from './components/ChatWindow';

import SettingsPage from './components/SettingsPage';
import AuthPopup from './components/AuthPopup';
import axios from 'axios';

const BASE_URL = 'http://localhost:8000';

export default function App() {
  const { openLauncher } = useTaskStore();
  const { theme } = useThemeStore();
  const [authenticated, setAuthenticated] = React.useState<boolean | null>(null);

  // Check auth status on mount
  useEffect(() => {
    checkAuthStatus();
  }, []);

  const checkAuthStatus = async () => {
    try {
      const response = await axios.get(`${BASE_URL}/auth/status`);
      setAuthenticated(response.data.authenticated);
    } catch (error) {
      console.error('Failed to check auth status:', error);
      // If server is down, we might want to retry or show error
      // For now, let's assume not authenticated if check fails
      setAuthenticated(false);
    }
  };

  // Apply theme class to document
  useEffect(() => {
    if (theme === 'dark') {
      document.documentElement.classList.add('dark');
    } else {
      document.documentElement.classList.remove('dark');
    }
  }, [theme]);

  // Cmd+K keyboard shortcut
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
        e.preventDefault();
        openLauncher();
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [openLauncher]);



  if (authenticated === null) {
    return (
      <div className="h-screen w-screen flex items-center justify-center bg-background">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
      </div>
    );
  }

  return (
    <>
      {!authenticated && <AuthPopup onAuthenticated={() => setAuthenticated(true)} />}
      <AppLayout>
      <div className="drag-region fixed top-0 left-0 right-0 h-10 z-50 pointer-events-none" />
      <main className="flex-1 overflow-hidden">
        <AnimatePresence mode="wait">
          <Routes>
            <Route path="/" element={<ChatWindow />} />
            <Route path="/settings" element={<SettingsPage />} />
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </AnimatePresence>
      </main>
      </AppLayout>
    </>
  );
}
