import React, { useState, useRef, useEffect } from 'react';
import { ArrowUp, FolderOpen, X } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { cn } from '../lib/utils';
import { useChatStore } from '../stores/chatStore';
import toast from 'react-hot-toast';

interface PromptInputProps {
  onSend: (content: string) => void;
  disabled?: boolean;
}

const PromptInput: React.FC<PromptInputProps> = ({ 
  onSend, 
  disabled = false 
}) => {
  const [input, setInput] = useState('');
  const { baseDirectory, setBaseDirectory, chatMode, setChatMode } = useChatStore();
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = `${textareaRef.current.scrollHeight}px`;
    }
  }, [input]);

  const handleSubmit = (e?: React.FormEvent) => {
    e?.preventDefault();
    
    if (!baseDirectory) {
      toast.error("Please select a base directory first.", {
        icon: '📁',
        style: {
          borderRadius: '10px',
          background: '#333',
          color: '#fff',
        },
      });
      return;
    }

    if (input.trim() && !disabled) {
      onSend(input.trim());
      setInput('');
      if (textareaRef.current) {
        textareaRef.current.style.height = 'auto';
      }
    }
  };

  const handleSelectDirectory = async () => {
    try {
      console.log('PromptInput: Requesting directory selection...');
      // @ts-ignore - electron is exposed via preload
      if (!window.electron || !window.electron.selectDirectory) {
          throw new Error("Electron API 'selectDirectory' is not available. Please restart the app.");
      }
      const path = await window.electron.selectDirectory();
      console.log('PromptInput: Selected path:', path);
      if (path) {
        setBaseDirectory(path);
        toast.success(`Base directory set to: ${path.split(/[\\/]/).pop()}`, {
          icon: '✅',
        });
      }
    } catch (error: any) {
      console.error('Failed to select directory:', error);
      toast.error(error.message || "Failed to open directory picker.");
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  const currentDirName = baseDirectory ? baseDirectory.split(/[\\/]/).pop() : null;

  return (
    <div className="absolute bottom-8 left-0 right-0 z-[100] px-6 pointer-events-none">
      <div className="max-w-4xl mx-auto w-full pointer-events-auto">
        <form 
          onSubmit={handleSubmit}
          className={cn(
            "relative flex flex-col w-full bg-card/90 backdrop-blur-xl border border-border/50 rounded-3xl shadow-2xl transition-all duration-300 ring-1 ring-white/10",
            disabled && "opacity-50 cursor-not-allowed"
          )}
        >
          {/* Base Directory Indicator */}
          <AnimatePresence>
            {baseDirectory && (
              <motion.div 
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: 10 }}
                className="flex items-center gap-2 px-4 py-2 border-b border-border/30"
              >
                <div className="flex items-center gap-1.5 px-2 py-0.5 bg-primary/10 text-primary rounded-full text-[10px] font-medium uppercase tracking-wider">
                  <FolderOpen size={12} />
                  <span className="max-w-[300px] truncate" title={baseDirectory}>{baseDirectory}</span>
                  <button 
                    type="button"
                    onClick={() => setBaseDirectory(null)}
                    className="hover:text-foreground transition-colors ml-1"
                  >
                    <X size={10} />
                  </button>
                </div>
              </motion.div>
            )}
          </AnimatePresence>

          <div className="flex items-end gap-2 p-2">
            <button
              type="button"
              onClick={handleSelectDirectory}
              className={cn(
                "flex-shrink-0 w-10 h-10 rounded-2xl flex items-center justify-center transition-all duration-200 hover:bg-muted group relative",
                baseDirectory ? "text-primary bg-primary/10" : "text-muted-foreground hover:text-foreground"
              )}
              title="Select Base Directory"
            >
              <FolderOpen size={20} />
              {!baseDirectory && (
                <span className="absolute -top-1 -right-1 w-2.5 h-2.5 bg-red-500 rounded-full border-2 border-card animate-pulse" />
              )}
            </button>

            <select
              value={chatMode}
              onChange={(e) => setChatMode(e.target.value as any)}
              disabled={disabled}
              className="bg-transparent border border-border/30 rounded-xl px-3 py-2 text-sm text-foreground outline-none focus:ring-1 focus:ring-primary/50 transition-colors h-10 shrink-0 cursor-pointer appearance-none text-center min-w-[110px]"
            >
              <option value="multiagent">Multiagent</option>
              <option value="chat">General Chat</option>
            </select>


            <textarea
              ref={textareaRef}
              rows={1}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder={baseDirectory ? `Message in ${currentDirName}...` : "Select a base directory to start..."}
              disabled={disabled}
              className="w-full bg-transparent border-none resize-none py-2.5 px-2 min-h-[44px] max-h-[200px] overflow-y-auto text-sm leading-relaxed placeholder:text-muted-foreground/60 scrollbar-none"
            />
            
            <motion.button
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              type="submit"
              disabled={!input.trim() || disabled}
              className={cn(
                "flex-shrink-0 w-10 h-10 rounded-2xl flex items-center justify-center transition-all duration-300",
                input.trim() && baseDirectory
                  ? "bg-primary text-primary-foreground shadow-lg shadow-primary/20" 
                  : "bg-muted text-muted-foreground opacity-50"
              )}
            >
              <ArrowUp size={20} />
            </motion.button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default PromptInput;
