import React, { useState, useEffect } from 'react';
import { 
  Puzzle, 
  RotateCw, 
  ShieldCheck, 
  CheckCircle2, 
  XCircle, 
  Terminal, 
  MessageSquare, 
  Info,
  Code
} from 'lucide-react';
import axios from 'axios';
import { cn } from '../lib/utils';
import toast from '../utils/toast';

const BASE_URL = 'http://localhost:8000';

interface ModMetadata {
  id: str;
  name: str;
  version: str;
  description: str;
  author: str;
  enabled: boolean;
  hooks: string[];
  entry: string;
}

type str = string;

const HOOK_ICONS: Record<string, React.ReactNode> = {
  on_before_prompt: <MessageSquare size={14} className="text-blue-400" />,
  on_after_prompt: <MessageSquare size={14} className="text-cyan-400" />,
  on_before_tool_execution: <ShieldCheck size={14} className="text-amber-400" />,
  on_after_tool_execution: <Terminal size={14} className="text-emerald-400" />,
  on_custom_command: <Code size={14} className="text-purple-400" />,
};

const ModsPage: React.FC = () => {
  const [mods, setMods] = useState<ModMetadata[]>([]);
  const [loading, setLoading] = useState(true);
  const [togglingId, setTogglingId] = useState<string | null>(null);

  useEffect(() => {
    fetchMods();
  }, []);

  const fetchMods = async () => {
    try {
      setLoading(true);
      const res = await axios.get<ModMetadata[]>(`${BASE_URL}/mods`);
      setMods(res.data);
    } catch (err) {
      console.error('Failed to load mods:', err);
      toast.error('Failed to load mods from backend.');
    } finally {
      setLoading(false);
    }
  };

  const handleToggle = async (modId: string) => {
    try {
      setTogglingId(modId);
      const res = await axios.post<{ mod_id: string; enabled: boolean }>(`${BASE_URL}/mods/${modId}/toggle`);
      setMods(prev =>
        prev.map(m => m.id === modId ? { ...m, enabled: res.data.enabled } : m)
      );
      toast.success(`Mod ${res.data.enabled ? 'enabled' : 'disabled'} successfully.`);
    } catch (err) {
      console.error('Failed to toggle mod:', err);
      toast.error('Failed to toggle mod state.');
    } finally {
      setTogglingId(null);
    }
  };

  const handleReload = async () => {
    try {
      setLoading(true);
      const res = await axios.post<{ status: string; loaded_mods: ModMetadata[] }>(`${BASE_URL}/mods/reload`);
      setMods(res.data.loaded_mods);
      toast.success('Mods reloaded from disk.');
    } catch (err) {
      console.error('Failed to reload mods:', err);
      toast.error('Failed to reload mods.');
    } finally {
      setLoading(false);
    }
  };

  const activeCount = mods.filter(m => m.enabled).length;

  return (
    <div className="flex-1 flex flex-col h-full overflow-y-auto bg-background text-foreground p-6 md:p-8 space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-border pb-6">
        <div>
          <div className="flex items-center gap-3">
            <div className="p-2.5 rounded-xl bg-primary/10 text-primary">
              <Puzzle size={24} />
            </div>
            <div>
              <h1 className="text-2xl font-bold tracking-tight">Claude Mods</h1>
              <p className="text-sm text-muted-foreground">
                In-process lifecycle plugins for prompt rewriting, tool execution guardrails, and runtime telemetry.
              </p>
            </div>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={handleReload}
            disabled={loading}
            className="flex items-center gap-2 px-4 py-2 rounded-lg bg-secondary hover:bg-secondary/80 text-secondary-foreground text-sm font-medium transition-all active:scale-95 disabled:opacity-50"
          >
            <RotateCw size={16} className={cn(loading && "animate-spin")} />
            Reload from Disk
          </button>
        </div>
      </div>

      {/* Stats Summary */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <div className="p-4 rounded-xl border border-border bg-card/50 flex items-center justify-between">
          <div>
            <p className="text-xs text-muted-foreground uppercase tracking-wider font-semibold">Total Installed</p>
            <p className="text-2xl font-bold mt-1">{mods.length}</p>
          </div>
          <Puzzle size={24} className="text-muted-foreground" />
        </div>

        <div className="p-4 rounded-xl border border-border bg-card/50 flex items-center justify-between">
          <div>
            <p className="text-xs text-muted-foreground uppercase tracking-wider font-semibold">Active & Hooked</p>
            <p className="text-2xl font-bold mt-1 text-emerald-500">{activeCount}</p>
          </div>
          <CheckCircle2 size={24} className="text-emerald-500" />
        </div>

        <div className="p-4 rounded-xl border border-border bg-card/50 flex items-center justify-between">
          <div>
            <p className="text-xs text-muted-foreground uppercase tracking-wider font-semibold">Disabled</p>
            <p className="text-2xl font-bold mt-1 text-muted-foreground">{mods.length - activeCount}</p>
          </div>
          <XCircle size={24} className="text-muted-foreground" />
        </div>
      </div>

      {/* Mods List */}
      <div className="space-y-4">
        <h2 className="text-lg font-semibold flex items-center gap-2">
          <span>Installed Mods</span>
          <span className="text-xs px-2 py-0.5 rounded-full bg-secondary text-secondary-foreground">
            {mods.length}
          </span>
        </h2>

        {loading && mods.length === 0 ? (
          <div className="p-12 text-center text-muted-foreground border border-dashed border-border rounded-xl">
            <RotateCw size={24} className="animate-spin mx-auto mb-2 text-primary" />
            Loading installed mods...
          </div>
        ) : mods.length === 0 ? (
          <div className="p-12 text-center text-muted-foreground border border-dashed border-border rounded-xl">
            <Puzzle size={32} className="mx-auto mb-3 text-muted-foreground/60" />
            <p className="font-medium text-foreground">No mods installed yet</p>
            <p className="text-sm mt-1">Create a directory in <code className="bg-muted px-1.5 py-0.5 rounded">backend/mods/</code> with a <code className="bg-muted px-1.5 py-0.5 rounded">mod.json</code>.</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 gap-4">
            {mods.map(mod => (
              <div
                key={mod.id}
                className={cn(
                  "p-5 rounded-xl border transition-all bg-card/40 flex flex-col sm:flex-row sm:items-start justify-between gap-4",
                  mod.enabled ? "border-primary/30 shadow-sm" : "border-border opacity-70"
                )}
              >
                <div className="space-y-2 flex-1">
                  <div className="flex items-center gap-2.5 flex-wrap">
                    <span className="font-semibold text-base text-foreground">{mod.name}</span>
                    <span className="text-xs font-mono px-2 py-0.5 rounded bg-muted text-muted-foreground">
                      v{mod.version}
                    </span>
                    <span className="text-xs text-muted-foreground">by {mod.author}</span>
                  </div>

                  <p className="text-sm text-muted-foreground leading-relaxed">
                    {mod.description || 'No description provided.'}
                  </p>

                  {/* Registered Hooks */}
                  <div className="pt-2 flex items-center gap-2 flex-wrap">
                    <span className="text-xs font-medium text-muted-foreground">Hooks:</span>
                    {mod.hooks.map(hook => (
                      <span
                        key={hook}
                        className="inline-flex items-center gap-1.5 text-xs px-2.5 py-1 rounded-md bg-secondary/80 text-foreground border border-border"
                      >
                        {HOOK_ICONS[hook] || <Code size={12} />}
                        <span className="font-mono">{hook}</span>
                      </span>
                    ))}
                  </div>
                </div>

                {/* Toggle Switch */}
                <div className="flex sm:flex-col items-center sm:items-end justify-between gap-2 pt-2 sm:pt-0">
                  <button
                    onClick={() => handleToggle(mod.id)}
                    disabled={togglingId === mod.id}
                    className={cn(
                      "relative inline-flex h-6 w-11 shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out focus:outline-none focus:ring-2 focus:ring-primary focus:ring-offset-2",
                      mod.enabled ? "bg-emerald-500" : "bg-muted"
                    )}
                    role="switch"
                    aria-checked={mod.enabled}
                    title={mod.enabled ? "Disable Mod" : "Enable Mod"}
                  >
                    <span
                      className={cn(
                        "pointer-events-none inline-block h-5 w-5 transform rounded-full bg-white shadow-lg ring-0 transition duration-200 ease-in-out",
                        mod.enabled ? "translate-x-5" : "translate-x-0"
                      )}
                    />
                  </button>
                  <span className="text-xs font-medium text-muted-foreground">
                    {mod.enabled ? 'Active' : 'Disabled'}
                  </span>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Guide Info Box */}
      <div className="p-4 rounded-xl border border-primary/20 bg-primary/5 flex items-start gap-3 mt-6">
        <Info size={20} className="text-primary shrink-0 mt-0.5" />
        <div className="text-xs text-muted-foreground leading-relaxed space-y-1">
          <p className="font-medium text-foreground">How Claude Mods work in OpenAgents</p>
          <p>
            Mods execute directly inside the Python agent runtime. They can inspect and alter prompts prior to model reasoning (<code className="text-foreground">on_before_prompt</code>), block or audit dangerous terminal/filesystem commands (<code className="text-foreground">on_before_tool_execution</code>), and scrub sensitive credentials from output logs (<code className="text-foreground">on_after_tool_execution</code>).
          </p>
        </div>
      </div>
    </div>
  );
};

export default ModsPage;
