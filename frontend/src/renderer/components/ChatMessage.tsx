import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Message } from '../stores/chatStore';
import { cn } from '../lib/utils';
import { User, Sparkles, Globe, Folder, Terminal, ChevronDown, ChevronRight, Search } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

interface ChatMessageProps {
  message: Message;
}

const ChatMessage: React.FC<ChatMessageProps> = ({ message }) => {
  const isUser = message.role === 'user';
  const [isExpanded, setIsExpanded] = useState(false);

  // Determine icon and color based on agentName or message type
  const getAgentIcon = () => {
    switch (message.agentName) {
      case 'BrowserAgent':
        return <Globe size={16} className="text-blue-500" />;
      case 'FileSystemAgent':
        return <Folder size={16} className="text-amber-500" />;
      case 'TerminalAgent':
        return <Terminal size={16} className="text-green-500" />;
      case 'ResearchAgent':
        return <Search size={16} className="text-purple-500" />;
      default:
        return <Sparkles size={16} className="text-primary" />;
    }
  };

  const isToolOutput = message.type === 'tool_output' || message.type === 'agent_start' || message.type === 'tasks_decomposed' || message.type === 'status';
  const isError = message.type === 'error';

  if (isToolOutput) {
    // Avoid rendering empty tool calls
    if (!message.content || (typeof message.content === 'string' && !message.content.trim()) || (typeof message.content === 'object' && Object.keys(message.content).length === 0)) {
        return null;
    }

    return (
      <motion.div
        initial={{ opacity: 0, y: 5 }}
        animate={{ opacity: 1, y: 0 }}
        className="flex w-full gap-4 flex-row"
      >
        <div className="w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0 mt-1 bg-muted">
           {getAgentIcon()}
        </div>
        
        <div className="flex flex-col max-w-[80%] w-full">
            <div 
                className="flex items-center gap-2 cursor-pointer p-2 hover:bg-muted/50 rounded-md transition-colors"
                onClick={() => setIsExpanded(!isExpanded)}
            >
                {isExpanded ? <ChevronDown size={14} /> : <ChevronRight size={14} />}
                <span className="text-xs font-medium text-muted-foreground uppercase tracking-wider">
                    {message.agentName || 'System'} {message.type?.replace('_', ' ')}
                </span>
            </div>

            <AnimatePresence>
                {isExpanded && (
                    <motion.div
                        initial={{ height: 0, opacity: 0 }}
                        animate={{ height: 'auto', opacity: 1 }}
                        exit={{ height: 0, opacity: 0 }}
                        className="overflow-hidden"
                    >
                        <div className="bg-muted/30 p-3 rounded-md text-xs font-mono whitespace-pre-wrap border border-border mt-1">
                            {typeof message.content === 'object' ? JSON.stringify(message.content, null, 2) : message.content}
                        </div>
                    </motion.div>
                )}
            </AnimatePresence>
        </div>
      </motion.div>
    )
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.2 }}
      className={cn(
        "flex w-full gap-4",
        isUser ? "flex-row-reverse" : "flex-row"
      )}
    >
      <div className={cn(
        "w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0 mt-1",
        isUser ? "bg-primary text-primary-foreground" : "bg-muted"
      )}>
        {isUser ? <User size={16} /> : <Sparkles size={16} className={isError ? "text-red-500" : "text-primary"} />}
      </div>
      
      <div className={cn(
        "flex flex-col max-w-[80%]",
        isUser ? "items-end" : "items-start"
      )}>
        <div className={cn(
          "px-4 py-2.5 rounded-2xl text-sm leading-relaxed shadow-sm",
          isUser 
            ? "bg-muted text-foreground rounded-tr-none" 
            : isError
                ? "bg-red-500/10 text-red-600 border border-red-200 rounded-tl-none"
                : "bg-transparent text-foreground rounded-tl-none border border-border"
        )}>
          {typeof message.content === 'object' ? (
            <div className="whitespace-pre-wrap font-mono text-xs">
              {JSON.stringify(message.content, null, 2)}
            </div>
          ) : (
            <div className="prose prose-sm dark:prose-invert max-w-none break-words leading-normal">
              <ReactMarkdown 
                remarkPlugins={[remarkGfm]}
                components={{
                  pre: ({node, ...props}: any) => <div className="overflow-auto my-2 p-2 bg-muted/50 rounded-md" {...props} />,
                  code: ({node, ...props}: any) => <code className="bg-muted/50 px-1 py-0.5 rounded text-xs font-mono" {...props} />
                }}
              >
                {typeof message.content === 'string' ? message.content : JSON.stringify(message.content)}
              </ReactMarkdown>
            </div>
          )}
        </div>
        <span className="text-[10px] text-muted-foreground mt-1 px-1">
          {new Date(message.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
        </span>
      </div>
    </motion.div>
  );
};

export default ChatMessage;
