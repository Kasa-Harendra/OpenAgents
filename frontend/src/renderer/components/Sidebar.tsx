import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  SquarePen, 
  Settings, 
  MessageSquare, 
  ChevronLeft,
  ChevronRight,
  User,
  Trash2
} from 'lucide-react';
import { cn } from '../lib/utils';
import { useChatStore } from '../stores/chatStore';
import ThemeToggle from '@/components/ThemeToggle';
import { useNavigate, useLocation } from 'react-router-dom';
import gsap from 'gsap';

const Sidebar: React.FC = () => {
  const [isCollapsed, setIsCollapsed] = useState(false);
  const { chats, activeChatId, setActiveChat, addChat, removeChat, loadConversations } = useChatStore();
  const navigate = useNavigate();
  const location = useLocation();

  useEffect(() => {
    loadConversations();
  }, [loadConversations]);

  return (
    <motion.aside
      initial={false}
      animate={{ 
        width: isCollapsed ? 70 : 260,
        transition: { duration: 0.2, ease: "easeInOut" }
      }}
      className={cn(
        "relative flex flex-col h-full bg-sidebar group z-40",
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
          onClick={() => {
            addChat("New Chat");
            navigate("/");
          }}
          className={cn(
            "p-2 hover:bg-hover rounded-lg transition-all active:scale-95",
            isCollapsed ? "" : "ml-auto"
          )}
          title="New Chat" aria-label="New Chat"
        >
          <SquarePen size={20} className="text-secondary-foreground" />
        </button>
      </div>

      {/* Middle Section - Chat History */}
      <div className="flex-1 overflow-y-auto px-3 py-4 space-y-1.5">
        <AnimatePresence initial={false}>
          {chats.map((chat) => {
            const isActive = activeChatId === chat.id && location.pathname === "/";
            return (
            <motion.div
              key={chat.id}
              role="button"
              tabIndex={0}
              initial={{ opacity: 0, x: -10 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: -10 }}
              onMouseEnter={(e) => {
                gsap.to(e.currentTarget, { scale: 1.02, x: 4, duration: 0.5, ease: "power3.out" });
              }}
              onMouseLeave={(e) => {
                gsap.to(e.currentTarget, { scale: 1, x: 0, duration: 0.5, ease: "power3.out" });
              }}
              whileTap={{ scale: 0.98 }}
              onClick={() => {
                setActiveChat(chat.id);
                navigate("/");
              }}
              onKeyDown={(e) => {
                if (e.key === 'Enter' || e.key === ' ') {
                  setActiveChat(chat.id);
                  navigate("/");
                }
              }}
              className={cn(
                "relative w-full flex items-center gap-3 px-3 py-2.5 rounded-xl transition-colors group/item cursor-pointer select-none",
                isActive
                  ? "text-foreground" 
                  : "text-muted-foreground hover:text-foreground",
                isCollapsed ? "justify-center" : ""
              )}
            >
              {isActive && (
                <motion.div 
                  layoutId="activeChatIndicator"
                  className="absolute inset-0 bg-secondary rounded-xl z-0"
                  initial={false}
                  transition={{ type: "spring", stiffness: 350, damping: 30 }}
                />
              )}
              <div className="relative z-10 flex items-center gap-3 w-full min-w-0">
                <MessageSquare size={18} className="flex-shrink-0" />
                {!isCollapsed && (
                  <span className="text-sm font-medium truncate text-left flex-1">{chat.title}</span>
                )}
                {!isCollapsed && (
                  <button
                    type="button"
                    onClick={(e) => {
                      e.stopPropagation();
                      removeChat(chat.id);
                    }}
                    className="opacity-0 group-hover/item:opacity-100 p-1 hover:bg-destructive/20 text-muted-foreground hover:text-destructive rounded-md transition-all flex-shrink-0"
                    title="Delete conversation"
                    aria-label={`Delete conversation ${chat.title}`}
                  >
                    <Trash2 size={14} />
                  </button>
                )}
              </div>
            </motion.div>
          )})}
        </AnimatePresence>
      </div>

      {/* Bottom Section */}
      <div className="p-2 space-y-1">
        <div className={cn("flex items-center", isCollapsed ? "justify-center" : "gap-2")}>
          <ThemeToggle isCollapsed={isCollapsed} />
        </div>
        
        <button 
          onClick={() => navigate("/settings")}
          className={cn(
            "w-full flex items-center gap-3 px-3 py-2 rounded-lg hover:bg-hover transition-all",
            location.pathname === "/settings" 
              ? "bg-secondary text-secondary-foreground" 
              : "text-muted-foreground hover:text-foreground",
            isCollapsed ? "justify-center" : ""
          )}
        >
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
          "absolute -right-3 top-1/2 -translate-y-1/2 w-6 h-12 bg-background rounded-full flex items-center justify-center shadow-sm opacity-0 group-hover:opacity-100 focus-visible:opacity-100 transition-opacity z-50",
          "hover:bg-muted"
        )}
        aria-label={isCollapsed ? "Expand Sidebar" : "Collapse Sidebar"}
      >
        {isCollapsed ? <ChevronRight size={14} /> : <ChevronLeft size={14} />}
      </button>
    </motion.aside>
  );
};

export default Sidebar;
