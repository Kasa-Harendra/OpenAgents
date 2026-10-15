import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  CheckCircle2, 
  Circle, 
  AlertCircle, 
  Loader2, 
  ListTodo, 
  ChevronDown, 
  ChevronRight,
  Bot
} from 'lucide-react';
import { useChatStore } from '../stores/chatStore';
import { cn } from '../lib/utils';

export interface TaskItem {
  id?: string;
  agent: string;
  subtask: string;
  status?: 'pending' | 'in_progress' | 'completed' | 'failed';
}

const AGENT_COLORS: Record<string, string> = {
  FileSystemAgent: "text-amber-400 bg-amber-400/10 border-amber-400/20",
  TerminalAgent: "text-blue-400 bg-blue-400/10 border-blue-400/20",
  BrowserAgent: "text-purple-400 bg-purple-400/10 border-purple-400/20",
  ResearchAgent: "text-cyan-400 bg-cyan-400/10 border-cyan-400/20",
  IntegratorAgent: "text-emerald-400 bg-emerald-400/10 border-emerald-400/20",
  Coordinator: "text-pink-400 bg-pink-400/10 border-pink-400/20",
};

const TaskChecklist: React.FC = () => {
  const activeTasks = useChatStore((state) => state.activeTasks as TaskItem[]);
  const [isCollapsed, setIsCollapsed] = useState(false);

  if (!activeTasks || activeTasks.length === 0) {
    return null;
  }

  const completedCount = activeTasks.filter(t => t.status === 'completed').length;
  const inProgressTask = activeTasks.find(t => t.status === 'in_progress');
  const progressPercent = Math.round((completedCount / activeTasks.length) * 100);

  return (
    <div className="w-full max-w-4xl mx-auto my-3 px-4">
      <div className="rounded-2xl border border-border/80 bg-card/60 backdrop-blur-md shadow-sm overflow-hidden">
        {/* Header Bar */}
        <div 
          onClick={() => setIsCollapsed(!isCollapsed)}
          className="flex items-center justify-between px-4 py-2.5 bg-muted/40 cursor-pointer select-none hover:bg-muted/60 transition-colors"
        >
          <div className="flex items-center gap-2.5">
            <div className="p-1 rounded-md bg-primary/10 text-primary">
              <ListTodo size={15} />
            </div>
            <span className="text-xs font-semibold tracking-tight text-foreground">
              Execution Plan ({completedCount}/{activeTasks.length} Completed)
            </span>
            {inProgressTask && (
              <span className="hidden sm:inline-flex items-center gap-1 text-[11px] font-mono text-muted-foreground animate-pulse">
                • Current: {inProgressTask.agent}
              </span>
            )}
          </div>

          <div className="flex items-center gap-3">
            {/* Progress bar */}
            <div className="hidden sm:flex items-center gap-2 w-28">
              <div className="flex-1 h-1.5 rounded-full bg-muted overflow-hidden">
                <div 
                  className="h-full bg-emerald-500 rounded-full transition-all duration-300"
                  style={{ width: `${progressPercent}%` }}
                />
              </div>
              <span className="text-[10px] font-mono text-muted-foreground font-semibold">{progressPercent}%</span>
            </div>

            <button 
              className="text-muted-foreground hover:text-foreground"
              aria-label={isCollapsed ? "Expand tasks" : "Collapse tasks"}
            >
              {isCollapsed ? <ChevronRight size={14} /> : <ChevronDown size={14} />}
            </button>
          </div>
        </div>

        {/* Task Items List */}
        <AnimatePresence initial={false}>
          {!isCollapsed && (
            <motion.div
              initial={{ height: 0, opacity: 0 }}
              animate={{ height: 'auto', opacity: 1 }}
              exit={{ height: 0, opacity: 0 }}
              className="divide-y divide-border/40 p-2 space-y-1"
            >
              {activeTasks.map((task, idx) => {
                const status = task.status || 'pending';
                return (
                  <div
                    key={task.id || `task_${idx}`}
                    className={cn(
                      "flex items-start gap-3 p-2 rounded-xl text-xs transition-colors",
                      status === 'in_progress' ? "bg-primary/5 border border-primary/20 shadow-xs" : "hover:bg-muted/30"
                    )}
                  >
                    {/* Status Icon */}
                    <div className="mt-0.5 shrink-0">
                      {status === 'completed' && (
                        <CheckCircle2 size={15} className="text-emerald-500" />
                      )}
                      {status === 'in_progress' && (
                        <Loader2 size={15} className="text-primary animate-spin" />
                      )}
                      {status === 'failed' && (
                        <AlertCircle size={15} className="text-red-500" />
                      )}
                      {status === 'pending' && (
                        <Circle size={15} className="text-muted-foreground/40" />
                      )}
                    </div>

                    {/* Agent Pill & Subtask Description */}
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 mb-1 flex-wrap">
                        <span className={cn(
                          "px-2 py-0.5 rounded-md text-[10px] font-mono border font-medium inline-flex items-center gap-1",
                          AGENT_COLORS[task.agent] || "text-foreground bg-muted border-border"
                        )}>
                          <Bot size={10} />
                          {task.agent}
                        </span>
                        <span className="text-[10px] text-muted-foreground font-mono">Step {idx + 1}</span>
                      </div>
                      <p className={cn(
                        "leading-relaxed break-words",
                        status === 'completed' ? "text-muted-foreground line-through opacity-80" : "text-foreground",
                        status === 'in_progress' ? "font-medium" : ""
                      )}>
                        {task.subtask}
                      </p>
                    </div>
                  </div>
                );
              })}
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </div>
  );
};

export default TaskChecklist;
