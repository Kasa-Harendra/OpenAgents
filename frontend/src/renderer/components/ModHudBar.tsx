import React, { useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  ShieldCheck, 
  Terminal, 
  Zap, 
  Activity, 
  Puzzle, 
  Sparkles,
  Command,
  ChevronRight
} from 'lucide-react';
import { Link } from 'react-router-dom';
import axios from 'axios';
import { useChatStore } from '../stores/chatStore';
import { cn } from '../lib/utils';

const BASE_URL = 'http://localhost:8000';

const ICON_MAP: Record<string, React.ReactNode> = {
  shield: <ShieldCheck size={13} className="text-emerald-400" />,
  terminal: <Terminal size={13} className="text-blue-400" />,
  zap: <Zap size={13} className="text-purple-400" />,
  activity: <Activity size={13} className="text-amber-400" />,
  sparkles: <Sparkles size={13} className="text-pink-400" />,
};

const COLOR_CLASSES: Record<string, string> = {
  emerald: "border-emerald-500/30 bg-emerald-500/10 text-emerald-400",
  blue: "border-blue-500/30 bg-blue-500/10 text-blue-400",
  amber: "border-amber-500/30 bg-amber-500/10 text-amber-400",
  purple: "border-purple-500/30 bg-purple-500/10 text-purple-400",
  default: "border-border bg-card/60 text-foreground"
};

const ModHudBar: React.FC = () => {
  const { hudWidgets, setHudWidgets } = useChatStore();

  useEffect(() => {
    // Fetch initial HUD status on mount
    const fetchHud = async () => {
      try {
        const res = await axios.get(`${BASE_URL}/mods/hud`);
        if (Array.isArray(res.data) && res.data.length > 0) {
          setHudWidgets(res.data);
        }
      } catch (e) {
        // Silent catch if backend is still starting
      }
    };
    fetchHud();
  }, [setHudWidgets]);

  return (
    <div className="w-full px-4 mb-2">
      <div className="flex items-center justify-between gap-2 px-3 py-1.5 rounded-lg bg-card/40 backdrop-blur-md border border-border/60 text-xs">
        {/* Left Side: Widgets List or Default Hint */}
        <div className="flex items-center gap-2 overflow-x-auto scrollbar-none py-0.5">
          <div className="flex items-center gap-1.5 text-muted-foreground font-medium shrink-0">
            <span className="relative flex h-2 w-2">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
              <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500"></span>
            </span>
            <span className="hidden sm:inline font-mono">MODS HUD:</span>
          </div>

          <AnimatePresence>
            {hudWidgets.length > 0 ? (
              hudWidgets.map((w) => (
                <motion.div
                  key={w.id}
                  initial={{ opacity: 0, scale: 0.9 }}
                  animate={{ opacity: 1, scale: 1 }}
                  exit={{ opacity: 0, scale: 0.9 }}
                  className={cn(
                    "flex items-center gap-1.5 px-2 py-0.5 rounded-md border shrink-0 font-medium",
                    COLOR_CLASSES[w.color || "default"] || COLOR_CLASSES.default
                  )}
                >
                  {ICON_MAP[w.icon || ""] || <Puzzle size={12} />}
                  <span className="text-muted-foreground">{w.label}:</span>
                  <span className="font-semibold text-foreground">{w.value}</span>
                </motion.div>
              ))
            ) : (
              <div className="flex items-center gap-2 text-muted-foreground">
                <span className="bg-secondary/60 px-1.5 py-0.5 rounded text-[11px] font-mono">/mods</span>
                <span className="hidden md:inline">Type <code className="text-foreground">/create-mod &lt;prompt&gt;</code> to generate custom mods</span>
              </div>
            )}
          </AnimatePresence>
        </div>

        {/* Right Side: Quick Action Link */}
        <Link
          to="/mods"
          className="flex items-center gap-1 text-[11px] font-medium text-muted-foreground hover:text-foreground shrink-0 transition-colors ml-2"
          title="Open Claude Mods Manager"
        >
          <Command size={11} />
          <span className="hidden sm:inline">Manage</span>
          <ChevronRight size={12} />
        </Link>
      </div>
    </div>
  );
};

export default ModHudBar;
