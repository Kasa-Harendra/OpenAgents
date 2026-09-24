import React from 'react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import '@testing-library/jest-dom/vitest';
import axios from 'axios';
import App from '../App';

// Mock child components
vi.mock('../components/AuthPopup', () => ({
  default: () => <div data-testid="auth-popup">Auth Popup</div>,
}));

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

// Mock axios
vi.mock('axios');
const mockedAxios = vi.mocked(axios);

describe('App', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('sets authenticated to false when auth status check fails', async () => {
    // Suppress console.error in test output
    const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {});

    // Mock axios to reject
    mockedAxios.get.mockRejectedValue(new Error('Network Error'));

    render(
      <MemoryRouter>
        <App />
      </MemoryRouter>
    );

    // Wait for the auth popup to appear, meaning authenticated became false
    await waitFor(() => {
      expect(screen.getByTestId('auth-popup')).toBeInTheDocument();
    });

    // Check that axios.get was called correctly
    expect(mockedAxios.get).toHaveBeenCalledWith('http://localhost:8000/auth/status');

    // Verify the error was logged
    expect(consoleSpy).toHaveBeenCalledWith('Failed to check auth status:', expect.any(Error));

    consoleSpy.mockRestore();
  });

  it('sets authenticated to true when auth status check succeeds', async () => {
    mockedAxios.get.mockResolvedValue({ data: { authenticated: true } });

    render(
      <MemoryRouter>
        <App />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByTestId('app-layout')).toBeInTheDocument();
    });

    // Auth popup should not be rendered
    expect(screen.queryByTestId('auth-popup')).not.toBeInTheDocument();
  });
});
