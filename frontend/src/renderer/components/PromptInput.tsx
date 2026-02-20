import React, { useState, useRef, useEffect } from 'react';
import { ArrowUp } from 'lucide-react';
import { motion } from 'framer-motion';
import { cn } from '../lib/utils';

interface PromptInputProps {
  onSend: (content: string) => void;
  disabled?: boolean;
  placeholder?: string;
}

const PromptInput: React.FC<PromptInputProps> = ({ 
  onSend, 
  disabled = false, 
  placeholder = "Message AI Assistant..." 
}) => {
  const [input, setInput] = useState('');
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = `${textareaRef.current.scrollHeight}px`;
    }
  }, [input]);

  const handleSubmit = (e?: React.FormEvent) => {
    e?.preventDefault();
    if (input.trim() && !disabled) {
      onSend(input.trim());
      setInput('');
      if (textareaRef.current) {
        textareaRef.current.style.height = 'auto';
      }
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  return (
    <form 
      onSubmit={handleSubmit}
      className={cn(
        "relative flex flex-col w-full bg-card border border-border rounded-2xl shadow-sm transition-all",
        disabled && "opacity-50 cursor-not-allowed"
      )}
    >
      <textarea
        ref={textareaRef}
        rows={1}
        value={input}
        onChange={(e) => setInput(e.target.value)}
        onKeyDown={handleKeyDown}
        placeholder={placeholder}
        disabled={disabled}
        className="w-full bg-transparent border-none focus:ring-0 resize-none py-4 pl-4 pr-14 min-h-[56px] max-h-[200px] overflow-y-auto text-sm leading-relaxed placeholder:text-muted-foreground scrollbar-thin scrollbar-thumb-border scrollbar-track-transparent"
      />
      
      <motion.button
        whileHover={{ scale: 1.05 }}
        whileTap={{ scale: 0.95 }}
        type="submit"
        disabled={!input.trim() || disabled}
        className={cn(
          "absolute right-3 bottom-3 w-8 h-8 rounded-full flex items-center justify-center transition-all",
          input.trim() 
            ? "bg-primary text-primary-foreground hover:opacity-90" 
            : "bg-muted text-muted-foreground"
        )}
      >
        <ArrowUp size={18} />
      </motion.button>
    </form>
  );
};

export default PromptInput;
