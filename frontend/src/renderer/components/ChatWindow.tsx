import React, { useRef, useEffect } from 'react';
import { motion } from 'framer-motion';
import { useChatStore } from '../stores/chatStore';
import ChatMessage from '@/components/ChatMessage';
import SystemMessageGroup from '@/components/SystemMessageGroup';
import PromptInput from '@/components/PromptInput';
import { Sparkles } from 'lucide-react'; // Assuming Sparkles icon is from lucide-react

const ChatWindow: React.FC = () => {
  const { chats, activeChatId, connect, disconnect, sendMessage, isConnected, updateChatTitle, addChat } = useChatStore();
  const activeChat = chats.find((c) => c.id === activeChatId);
  const scrollRef = useRef<HTMLDivElement>(null);

  const [isEditingTitle, setIsEditingTitle] = React.useState(false);
  const [titleInput, setTitleInput] = React.useState('');
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (isEditingTitle && inputRef.current) {
        inputRef.current.focus();
    }
  }, [isEditingTitle]);

  useEffect(() => {
    connect();
    return () => disconnect();
  }, [connect, disconnect]);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [activeChat?.messages.length, activeChat?.isTyping]);

  const handleSend = (content: string) => {
    if (!activeChatId) return;
    sendMessage(content);
  };

  const handleInitialSend = (content: string) => {
    addChat("New Chat");
    setTimeout(() => {
        useChatStore.getState().sendMessage(content);
    }, 100);
  };

  if (!activeChatId) {
    return (
      <div className="flex flex-col items-center justify-center min-h-full p-4 text-center space-y-6">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="space-y-2"
        >
          <h1 className="text-4xl font-semibold tracking-tight">How can I help you today?</h1>
          <p className="text-muted-foreground">Start a new conversation or select one from the sidebar.</p>
        </motion.div>
        <div className="w-full max-w-2xl pt-4">
          <PromptInput onSend={handleInitialSend} disabled={false} />
        </div>
      </div>
    );
  }

  const handleTitleClick = () => {
    if (activeChat) {
        setTitleInput(activeChat.title);
        setIsEditingTitle(true);
    }
  };

  const handleTitleSave = () => {
    if (activeChat && titleInput.trim()) {
        updateChatTitle(activeChat.id, titleInput.trim());
    }
    setIsEditingTitle(false);
  };

  const handleTitleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
        handleTitleSave();
    } else if (e.key === 'Escape') {
        setIsEditingTitle(false);
    }
  };

  return (
    <div className="flex flex-col h-full relative">
      <div className="px-6 py-4 border-b border-border flex justify-between items-center bg-card/30 backdrop-blur-sm shrink-0">
        <div className="flex-1 mr-4">
            {isEditingTitle ? (
                <input
                    ref={inputRef}
                    type="text"
                    value={titleInput}
                    onChange={(e) => setTitleInput(e.target.value)}
                    onBlur={handleTitleSave}
                    onKeyDown={handleTitleKeyDown}
                    className="font-semibold text-lg bg-transparent border-b border-primary focus:outline-none w-full"
                />
            ) : (
                <h2 
                    className="font-semibold text-lg cursor-pointer hover:underline decoration-dashed underline-offset-4 decoration-muted-foreground/50"
                    onClick={handleTitleClick}
                    title="Click to rename"
                >
                    {activeChat?.title || 'New Chat'}
                </h2>
            )}
        </div>
        <div className="flex items-center gap-2 shrink-0">
            <div className={`w-2.5 h-2.5 rounded-full ${isConnected ? 'bg-green-500 shadow-[0_0_8px_rgba(34,197,94,0.5)]' : 'bg-red-500 shadow-[0_0_8px_rgba(239,68,68,0.5)]'}`} />
            <span className="text-xs font-medium text-muted-foreground">{isConnected ? 'Online' : 'Offline'}</span>
        </div>
      </div>

      <div className="flex-1 overflow-y-auto px-6 py-4 space-y-6 scroll-smooth pb-32" ref={scrollRef}>
        <div className="max-w-5xl mx-auto space-y-6">
          {activeChat?.messages.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-20 text-center space-y-4">
              <h2 className="text-2xl font-medium">New Conversation</h2>
              <p className="text-sm text-muted-foreground">Ask anything to get started.</p>
            </div>
          ) : (
            (() => {
              type GroupItem = 
                | { type: 'system_group'; messages: typeof messages; id: string }
                | { type: 'single'; message: typeof messages[0]; id: string };

              const messages = activeChat?.messages || [];
              const groupedMessages: GroupItem[] = [];
              let currentSystemGroup: typeof messages = [];

              messages.forEach((msg) => {
                const isSystemMessage = ['tool_output', 'agent_start', 'tasks_decomposed', 'status'].includes(msg.type || '');
                
                if (isSystemMessage) {
                  currentSystemGroup.push(msg);
                } else {
                  if (currentSystemGroup.length > 0) {
                    groupedMessages.push({ type: 'system_group', messages: [...currentSystemGroup], id: `group-${currentSystemGroup[0].id}` });
                    currentSystemGroup = [];
                  }
                  groupedMessages.push({ type: 'single', message: msg, id: msg.id });
                }
              });

              // Push remaining system messages
              if (currentSystemGroup.length > 0) {
                groupedMessages.push({ type: 'system_group', messages: [...currentSystemGroup], id: `group-${currentSystemGroup[0].id}` });
              }

              return groupedMessages.map((group) => {
                if (group.type === 'system_group') {
                  return <SystemMessageGroup key={group.id} messages={group.messages} />;
                }
                return <ChatMessage key={group.id} message={group.message} />;
              });
            })()
          )}
        </div>
      </div>

      <PromptInput onSend={handleSend} disabled={activeChat?.isTyping} />
    </div>
  );
};

export default ChatWindow;
