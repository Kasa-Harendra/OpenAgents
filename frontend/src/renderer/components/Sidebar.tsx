import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  SquarePen, 
  Settings, 
  MessageSquare, 
  ChevronLeft,
  ChevronRight,
  User
} from 'lucide-react';
import { cn } from '../lib/utils';
import { useChatStore } from '../stores/chatStore';
import ThemeToggle from '@/components/ThemeToggle';

const Sidebar: React.FC = () => {
  const [isCollapsed, setIsCollapsed] = useState(false);
  const { chats, activeChatId, setActiveChat, addChat } = useChatStore();

  return (
    <motion.aside
      initial={false}
      animate={{ 
        width: isCollapsed ? 70 : 260,
        transition: { duration: 0.2, ease: "easeInOut" }
      }}
      className={cn(
        "relative flex flex-col h-full bg-sidebar border-r border-sidebar-border group z-40",
        isCollapsed ? "items-center" : ""
      )}
    >
      {/* Top Section */}
      <div className={cn(
        "flex items-center justify-between p-4 h-16 transition-opacity duration-200",
        isCollapsed ? "justify-center" : ""
      )}>
        {!isCollapsed && (
          <span className="font-semibold text-lg truncate pr-2">AI Assistant</span>
        )}
        <button
          onClick={() => addChat("New Chat")}
          className={cn(
            "p-2 hover:bg-hover rounded-lg transition-all active:scale-95",
            isCollapsed ? "" : "ml-auto"
          )}
          title="New Chat"
        >
          <SquarePen size={20} className="text-secondary-foreground" />
        </button>
      </div>

      {/* Middle Section - Chat History */}
      <div className="flex-1 overflow-y-auto px-2 py-2 space-y-1">
        <AnimatePresence initial={false}>
          {chats.map((chat) => (
            <motion.button
              key={chat.id}
              initial={{ opacity: 0, x: -10 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: -10 }}
              onClick={() => setActiveChat(chat.id)}
              className={cn(
                "w-full flex items-center gap-3 px-3 py-2 rounded-lg transition-all group/item",
                activeChatId === chat.id 
                  ? "bg-secondary text-secondary-foreground" 
                  : "hover:bg-hover text-muted-foreground hover:text-foreground",
                isCollapsed ? "justify-center" : ""
              )}
            >
              <MessageSquare size={18} className="flex-shrink-0" />
              {!isCollapsed && (
                <span className="text-sm truncate text-left">{chat.title}</span>
              )}
            </motion.button>
          ))}
        </AnimatePresence>
      </div>

      {/* Bottom Section */}
      <div className="p-2 border-t border-sidebar-border space-y-1">
        <div className={cn("flex items-center", isCollapsed ? "justify-center" : "gap-2")}>
          <ThemeToggle isCollapsed={isCollapsed} />
        </div>
        
        <button className={cn(
          "w-full flex items-center gap-3 px-3 py-2 rounded-lg hover:bg-hover text-muted-foreground hover:text-foreground transition-all",
          isCollapsed ? "justify-center" : ""
        )}>
          <Settings size={18} />
          {!isCollapsed && <span className="text-sm font-medium">Settings</span>}
        </button>

        <div className={cn(
          "flex items-center gap-3 px-3 py-2 mt-1",
          isCollapsed ? "justify-center" : ""
        )}>
          <div className="w-8 h-8 rounded-full bg-muted flex items-center justify-center flex-shrink-0">
            <User size={16} />
          </div>
          {!isCollapsed && (
            <div className="flex flex-col min-w-0">
              <span className="text-sm font-medium truncate">User Profile</span>
            </div>
          )}
        </div>
      </div>

      {/* Toggle Button */}
      <button
        onClick={() => setIsCollapsed(!isCollapsed)}
        className={cn(
          "absolute -right-3 top-1/2 -translate-y-1/2 w-6 h-12 bg-background border border-border rounded-full flex items-center justify-center shadow-sm opacity-0 group-hover:opacity-100 transition-opacity z-50",
          "hover:bg-muted"
        )}
      >
        {isCollapsed ? <ChevronRight size={14} /> : <ChevronLeft size={14} />}
      </button>
    </motion.aside>
  );
};

export default Sidebar;
