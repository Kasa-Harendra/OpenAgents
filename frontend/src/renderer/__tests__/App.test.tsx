import React from 'react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import '@testing-library/jest-dom/vitest';
import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import App from '../App';

// Mock child components
vi.mock('../components/AppLayout', () => ({
  default: ({ children }: { children: React.ReactNode }) => <div data-testid="app-layout">{children}</div>,
}));

vi.mock('../components/ChatWindow', () => ({
  default: () => <div data-testid="chat-window">Chat Window</div>,
}));

vi.mock('../components/SettingsPage', () => ({
  default: () => <div data-testid="settings-page">Settings Page</div>,
}));

// Mock stores
vi.mock('../stores/taskStore', () => ({
  useTaskStore: () => ({
    openLauncher: vi.fn(),
  }),
}));

vi.mock('../stores/themeStore', () => ({
  useThemeStore: () => ({
    theme: 'light',
  }),
}));

// Mock framer-motion to simplify rendering
vi.mock('framer-motion', () => ({
  AnimatePresence: ({ children }: { children: React.ReactNode }) => <>{children}</>,
}));

describe('App', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders AppLayout directly at startup without authentication popup', () => {
    render(
      <MemoryRouter>
        <App />
      </MemoryRouter>
    );

    expect(screen.getByTestId('app-layout')).toBeInTheDocument();
    expect(screen.getByTestId('chat-window')).toBeInTheDocument();
  });
});

