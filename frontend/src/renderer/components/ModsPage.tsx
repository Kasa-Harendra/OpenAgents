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
  Code,
  Sparkles,
  Command,
  ArrowRight
} from 'lucide-react';
import axios from 'axios';
import { cn } from '../lib/utils';
import toast from '../utils/toast';

const BASE_URL = 'http://localhost:8000';

interface ModMetadata {
  id: string;
  name: string;
  version: string;
  description: string;
  author: string;
  enabled: boolean;
  hooks: string[];
  entry: string;
}

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
  
  // Prompt-to-Mod Generator state
  const [generatePrompt, setGeneratePrompt] = useState('');
  const [isGenerating, setIsGenerating] = useState(false);

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

  const handleGenerateMod = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!generatePrompt.trim()) return;

    try {
      setIsGenerating(true);
      const res = await axios.post<{ status: string; mod: ModMetadata }>(`${BASE_URL}/mods/generate`, {
        prompt: generatePrompt.trim()
      });

      if (res.data.status === 'success' && res.data.mod) {
        setMods(prev => [res.data.mod, ...prev.filter(m => m.id !== res.data.mod.id)]);
        setGeneratePrompt('');
        toast.success(`🎉 Created and loaded mod: "${res.data.mod.name}"`);
      }
    } catch (err: any) {
      console.error('Failed to generate mod:', err);
      toast.error(err.response?.data?.detail || 'Failed to generate mod.');
    } finally {
      setIsGenerating(false);
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
                In-process plugins for prompt rewriting, live HUD widgets, tool guardrails, and slash commands.
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

      {/* Prompt-to-Mod Generator Card */}
      <div className="p-5 rounded-2xl border border-primary/30 bg-gradient-to-r from-primary/10 via-card/50 to-background shadow-sm space-y-3">
        <div className="flex items-center gap-2">
          <Sparkles size={18} className="text-primary animate-pulse" />
          <h3 className="font-semibold text-base text-foreground">Create Mod with Prompt (Meta-Modding)</h3>
        </div>
        <p className="text-xs text-muted-foreground leading-relaxed">
          Describe the feature or hook you want. OpenAgents writes the code, registers the lifecycle hooks, and hot-loads it live.
        </p>

        <form onSubmit={handleGenerateMod} className="flex flex-col sm:flex-row gap-2 pt-1">
          <input
            type="text"
            value={generatePrompt}
            onChange={(e) => setGeneratePrompt(e.target.value)}
            placeholder="e.g. Track execution count, inject HUD widget, and alert on shell errors"
            disabled={isGenerating}
            className="flex-1 px-3.5 py-2.5 rounded-xl border border-border bg-background/80 text-sm focus:outline-none focus:ring-2 focus:ring-primary/50"
          />
          <button
            type="submit"
            disabled={isGenerating || !generatePrompt.trim()}
            className="flex items-center justify-center gap-2 px-5 py-2.5 rounded-xl bg-primary hover:bg-primary/90 text-primary-foreground text-sm font-medium transition-all active:scale-95 disabled:opacity-50 shrink-0"
          >
            {isGenerating ? (
              <>
                <RotateCw size={15} className="animate-spin" />
                Generating...
              </>
            ) : (
              <>
                <span>Build Mod</span>
                <ArrowRight size={15} />
              </>
            )}
          </button>
        </form>

        <div className="flex items-center gap-2 pt-1 text-[11px] text-muted-foreground">
          <Command size={12} />
          <span>You can also run <code className="bg-muted px-1.5 py-0.5 rounded text-foreground font-mono">/create-mod &lt;description&gt;</code> directly in any chat!</span>
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
            <p className="text-sm mt-1">Use the generator above or create a directory in <code className="bg-muted px-1.5 py-0.5 rounded">backend/mods/</code>.</p>
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
            Mods execute directly inside the Python agent runtime. They can inspect and alter prompts prior to model reasoning (<code className="text-foreground">on_before_prompt</code>), block or audit dangerous terminal/filesystem commands (<code className="text-foreground">on_before_tool_execution</code>), inject live HUD widgets into the desktop chat (<code className="text-foreground">ctx.set_hud_widget</code>), and respond to instant slash commands (<code className="text-foreground">/mods</code>, <code className="text-foreground">/audit</code>).
          </p>
        </div>
      </div>
    </div>
  );
};

export default ModsPage;
