import React, { useState } from 'react';
import { Message } from '../stores/chatStore';
import ChatMessage from './ChatMessage';
import { ChevronDown, ChevronRight, Activity } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

interface SystemMessageGroupProps {
  messages: Message[];
}

export const SystemMessageGroup: React.FC<SystemMessageGroupProps> = ({ messages }) => {
  const [isOpen, setIsOpen] = useState(false);

  // If there are no messages, don't render anything
  if (!messages.length) return null;

  return (
    <div className="border border-border/40 rounded-lg bg-card/50 overflow-hidden my-2">
        <button
            type="button"
            className="w-full flex items-center gap-2 p-3 cursor-pointer hover:bg-muted/40 transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary focus-visible:ring-offset-2"
            onClick={() => setIsOpen(!isOpen)}
            aria-expanded={isOpen}
            aria-label={`Toggle System Activity (${messages.length} steps)`}
        >
            <div className="p-1.5 rounded-md bg-muted text-muted-foreground">
                <Activity size={14} />
            </div>
            {isOpen ? <ChevronDown size={14} className="text-muted-foreground" /> : <ChevronRight size={14} className="text-muted-foreground" />}
            
            <span className="text-xs font-medium text-muted-foreground">
                System Activity ({messages.length} steps)
            </span>
        </button>
        
        <AnimatePresence>
            {isOpen && (
                <motion.div
                    initial={{ height: 0, opacity: 0 }}
                    animate={{ height: 'auto', opacity: 1 }}
                    exit={{ height: 0, opacity: 0 }}
                    className="overflow-hidden"
                >
                    <div className="p-3 pt-0 flex flex-col gap-3 border-t border-border/30 bg-muted/5">
                        {messages.map(m => (
                            <ChatMessage key={m.id} message={m} />
                        ))}
                    </div>
                </motion.div>
            )}
        </AnimatePresence>
    </div>
  );
};

export default SystemMessageGroup;
