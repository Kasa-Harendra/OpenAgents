import { useEffect } from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import { AnimatePresence } from 'framer-motion';
import { useTaskStore } from './stores/taskStore';
import { useThemeStore } from './stores/themeStore';
import AppLayout from './components/AppLayout';
import ChatWindow from './components/ChatWindow';

export default function App() {
  const { openLauncher } = useTaskStore();
  const { theme } = useThemeStore();

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

  return (
    <AppLayout>
      <div className="drag-region fixed top-0 left-0 right-0 h-10 z-50 pointer-events-none" />
      <main className="flex-1 overflow-hidden">
        <AnimatePresence mode="wait">
          <Routes>
            <Route path="/" element={<ChatWindow />} />
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </AnimatePresence>
      </main>
    </AppLayout>
  );
}
