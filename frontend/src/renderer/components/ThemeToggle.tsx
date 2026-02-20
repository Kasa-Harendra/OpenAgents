import React from 'react';
import { Sun, Moon } from 'lucide-react';
import { useThemeStore } from '../stores/themeStore';
import { cn } from '../lib/utils';

interface ThemeToggleProps {
  isCollapsed?: boolean;
}

const ThemeToggle: React.FC<ThemeToggleProps> = ({ isCollapsed }) => {
  const { theme, toggleTheme } = useThemeStore();

  return (
    <button
      onClick={toggleTheme}
      className={cn(
        "w-full flex items-center gap-3 px-3 py-2 rounded-lg hover:bg-hover text-muted-foreground hover:text-foreground transition-all",
        isCollapsed ? "justify-center" : ""
      )}
      title={theme === 'light' ? 'Switch to Dark Mode' : 'Switch to Light Mode'}
    >
      {theme === 'light' ? (
        <Moon size={18} />
      ) : (
        <Sun size={18} />
      )}
      {!isCollapsed && (
        <span className="text-sm font-medium">
          {theme === 'light' ? 'Dark Mode' : 'Light Mode'}
        </span>
      )}
    </button>
  );
};

export default ThemeToggle;
