import React, { useState, useEffect } from 'react';
import { 
  Settings as SettingsIcon, 
  Cpu, 
  Server, 
  Save, 
  Edit2, 
  X,
  Plus,
  Info,
  User,
  LogOut,
  FileText,
  HardDrive,
  Shield,
  CheckCircle2
} from 'lucide-react';
import { cn } from '../lib/utils';
import axios from 'axios';
import toast from '../utils/toast';

const BASE_URL = 'http://localhost:8000';

interface AgentConfig {
  agent_name: string;
  llm_provider: string;
  agent_type: string;
  llm_config: {
    model: string;
    base_url: string;
    api_key: string | null;
  };
  description?: string;
}

interface AgentPrompt {
  agent_name: string;
  system_prompt: string;
  updated_at?: string;
}

interface StorageOverview {
  home: string;
  database: string;
  database_exists: boolean;
  credentials_dir: string;
  credentials_secured: boolean;
  skills_dir: string;
  skills_count: number;
  mods_dir: string;
  mods_count: number;
  history_dir: string;
  history_sessions_count: number;
  audit_dir: string;
}

const PROVIDERS = ['NONE', 'OLLAMA', 'OPENAI', 'GEMINI', 'ANTHROPIC', 'GROQ', 'OTHERS'];

const SettingsPage: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'agents' | 'mcp' | 'prompts' | 'system' | 'account'>('agents');
  const [configs, setConfigs] = useState<AgentConfig[]>([]);
  const [prompts, setPrompts] = useState<AgentPrompt[]>([]);
  const [editingAgent, setEditingAgent] = useState<string | null>(null);
  const [editForm, setEditForm] = useState<AgentConfig | null>(null);
  
  const [editingPrompt, setEditingPrompt] = useState<string | null>(null);
  const [promptEditForm, setPromptEditForm] = useState<AgentPrompt | null>(null);
  
  // System & Storage state (~/.openagents)
  const [storageData, setStorageData] = useState<StorageOverview | null>(null);
  const [systemConfig, setSystemConfig] = useState<any>({
    version: '1.0.0',
    theme: 'dark',
    telemetry: false,
    default_model_provider: 'gemini',
    default_chat_mode: 'multiagent',
    server: { host: '127.0.0.1', port: 8000 },
    features: {
      claude_mods: true,
      self_healing: true,
      context_compaction: true,
      human_in_the_loop: true
    }
  });
  const [savingSystem, setSavingSystem] = useState(false);

  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchConfigs();
    fetchPrompts();
    fetchSystemInfo();
  }, []);

  const fetchSystemInfo = async () => {
    try {
      const [storageRes, configRes] = await Promise.all([
        axios.get(`${BASE_URL}/system/storage`),
        axios.get(`${BASE_URL}/system/config`)
      ]);
      setStorageData(storageRes.data);
      if (configRes.data?.config) {
        setSystemConfig(configRes.data.config);
      }
    } catch (err) {
      console.error('Failed to fetch system info:', err);
    }
  };

  const handleSaveSystemConfig = async () => {
    try {
      setSavingSystem(true);
      await axios.post(`${BASE_URL}/system/config`, { settings: systemConfig });
      toast.success('System configuration saved to ~/.openagents/config.json');
      fetchSystemInfo();
    } catch (err) {
      toast.error('Failed to save system configuration');
    } finally {
      setSavingSystem(false);
    }
  };

  const fetchConfigs = async () => {
    try {
      setLoading(true);
      const response = await axios.get(`${BASE_URL}/config`);
      
      const order = [
        "Coordinator",
        "FileSystemAgent",
        "ResearchAgent",
        "TerminalAgent",
        "BrowserAgent",
        "IntegratorAgent",
        "GuardianAgent"
      ];

      const hiddenAgents = ["RAGAgent", "YTAgent", "EmbeddingModel", "CodeExplainerAgent", "CodeExplainer", "YT", "RAG"];

      const filteredConfigs = response.data.filter((a: AgentConfig) => !hiddenAgents.includes(a.agent_name));

      const sortedConfigs = filteredConfigs.sort((a: AgentConfig, b: AgentConfig) => {
        const indexA = order.indexOf(a.agent_name);
        const indexB = order.indexOf(b.agent_name);
        
        if (indexA === -1 && indexB === -1) return a.agent_name.localeCompare(b.agent_name);
        if (indexA === -1) return 1;
        if (indexB === -1) return -1;
        
        return indexA - indexB;
      });

      setConfigs(sortedConfigs);
    } catch (error) {
      console.error('Failed to fetch configs:', error);
      toast.error('Failed to load configurations');
    } finally {
      setLoading(false);
    }
  };

  const fetchPrompts = async () => {
    try {
      const response = await axios.get(`${BASE_URL}/prompts`);
      const hiddenAgents = ["RAGAgent", "YTAgent", "EmbeddingModel", "CodeExplainerAgent", "CodeExplainer", "YT", "RAG"];
      const filteredPrompts = response.data.filter((p: AgentPrompt) => !hiddenAgents.includes(p.agent_name));
      setPrompts(filteredPrompts);
    } catch (error) {
      console.error('Failed to fetch prompts:', error);
    }
  };

  const handleEdit = (config: AgentConfig) => {
    setEditingAgent(config.agent_name);
    setEditForm({ ...config });
  };

  const handleCancel = () => {
    setEditingAgent(null);
    setEditForm(null);
  };

  const handleSave = async () => {
    if (!editForm) return;

    if (editForm.llm_provider.toLowerCase() !== 'none' && !editForm.llm_config.model) {
      toast.error('Model name is mandatory');
      return;
    }

    try {
      const payload = {
        agent_name: editForm.agent_name,
        llm_provider: editForm.llm_provider.toLowerCase(),
        agent_type: editForm.agent_type,
        llm_config: editForm.llm_config
      };
      await axios.put(`${BASE_URL}/config/${editForm.agent_name}`, payload);
      toast.success('Configuration saved successfully');
      setEditingAgent(null);
      setEditForm(null);
      fetchConfigs();
    } catch (error) {
      console.error('Failed to save config:', error);
      toast.error('Failed to save configuration');
    }
  };

  const updateFormField = (field: string, value: any) => {
    if (!editForm) return;
    if (field === 'llm_provider') {
      const isNone = value.toUpperCase() === 'NONE';
      setEditForm({
        ...editForm,
        llm_provider: value,
        llm_config: isNone ? {
          model: '',
          api_key: '',
          base_url: ''
        } : editForm.llm_config
      });
    } else if (field.startsWith('llm_config.')) {
      const configField = field.split('.')[1];
      setEditForm({
        ...editForm,
        llm_config: {
          ...editForm.llm_config,
          [configField]: value
        }
      });
    } else {
      setEditForm({ ...editForm, [field]: value });
    }
  };

  const handleEditPrompt = (prompt: AgentPrompt) => {
    setEditingPrompt(prompt.agent_name);
    setPromptEditForm({ ...prompt });
  };

  const handleCancelPrompt = () => {
    setEditingPrompt(null);
    setPromptEditForm(null);
  };

  const handleSavePrompt = async () => {
    if (!promptEditForm) return;

    try {
      await axios.put(`${BASE_URL}/prompts/${promptEditForm.agent_name}`, {
        agent_name: promptEditForm.agent_name,
        system_prompt: promptEditForm.system_prompt
      });
      toast.success('System prompt saved successfully');
      setEditingPrompt(null);
      setPromptEditForm(null);
      fetchPrompts();
    } catch (error) {
      console.error('Failed to save prompt:', error);
      toast.error('Failed to save system prompt');
    }
  };

  return (
    <div className="flex flex-col h-full bg-background overflow-hidden animate-fade-in">
      {/* Header */}
      <div className="px-8 py-6 border-b border-border flex items-center justify-between shrink-0">
        <div>
          <h1 className="text-2xl font-semibold flex items-center gap-2">
            <SettingsIcon className="text-primary" size={24} />
            Settings
          </h1>
          <p className="text-sm text-muted-foreground mt-1">Configure your AI agents and MCP servers</p>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex px-8 border-b border-border bg-muted/30 shrink-0">
        <button
          onClick={() => setActiveTab('agents')}
          className={cn(
            "px-6 py-3 text-sm font-medium border-b-2 transition-all flex items-center gap-2",
            activeTab === 'agents' 
              ? "border-primary text-primary" 
              : "border-transparent text-muted-foreground hover:text-foreground"
          )}
        >
          <Cpu size={16} />
          Agent Configurations
        </button>
        <button
          onClick={() => setActiveTab('mcp')}
          className={cn(
            "px-6 py-3 text-sm font-medium border-b-2 transition-all flex items-center gap-2",
            activeTab === 'mcp' 
              ? "border-primary text-primary" 
              : "border-transparent text-muted-foreground hover:text-foreground"
          )}
        >
          <Server size={16} />
          MCP Servers
        </button>
        <button
          onClick={() => setActiveTab('prompts')}
          className={cn(
            "px-6 py-3 text-sm font-medium border-b-2 transition-all flex items-center gap-2",
            activeTab === 'prompts' 
              ? "border-primary text-primary" 
              : "border-transparent text-muted-foreground hover:text-foreground"
          )}
        >
          <FileText size={16} />
          System Prompts
        </button>
        <button
          onClick={() => setActiveTab('system')}
          className={cn(
            "px-6 py-3 text-sm font-medium border-b-2 transition-all flex items-center gap-2",
            activeTab === 'system' 
              ? "border-primary text-primary" 
              : "border-transparent text-muted-foreground hover:text-foreground"
          )}
        >
          <HardDrive size={16} />
          System & Storage
        </button>
        <button
          onClick={() => setActiveTab('account')}
          className={cn(
            "px-6 py-3 text-sm font-medium border-b-2 transition-all flex items-center gap-2",
            activeTab === 'account' 
              ? "border-primary text-primary" 
              : "border-transparent text-muted-foreground hover:text-foreground"
          )}
        >
          <User size={16} />
          Account
        </button>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto p-8 custom-scrollbar">
        {activeTab === 'agents' ? (
          <div className="max-w-4xl mx-auto space-y-6">
            {loading ? (
              <div className="flex justify-center py-12">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
              </div>
            ) : configs.length === 0 ? (
              <div className="text-center py-12 bg-muted/20 rounded-xl border border-dashed border-border">
                <p className="text-muted-foreground">No agent configurations found</p>
              </div>
            ) : (
              configs.map((config) => (
                <div 
                  key={config.agent_name}
                  className={cn(
                    "group relative bg-card border border-border rounded-xl p-6 transition-all",
                    editingAgent === config.agent_name ? "ring-2 ring-primary border-transparent" : "hover:border-primary/50"
                  )}
                >
                  <div className="flex items-start justify-between mb-4">
                    <div>
                      <h3 className="text-lg font-semibold">{config.agent_name}</h3>
                      <p className="text-xs text-muted-foreground mt-0.5 max-w-md italic">
                        {config.description || 'No description available'}
                      </p>
                      <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-primary/10 text-primary uppercase mt-2">
                        {config.agent_type}
                      </span>
                    </div>
                    {editingAgent !== config.agent_name ? (
                      <button
                        onClick={() => handleEdit(config)}
                        className="p-2 hover:bg-muted rounded-lg transition-colors text-muted-foreground hover:text-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary/50"
                        title="Edit Configuration"
                        aria-label="Edit Configuration"
                      >
                        <Edit2 size={18} />
                      </button>
                    ) : (
                      <div className="flex gap-2">
                        <button
                          onClick={handleCancel}
                          className="p-2 hover:bg-destructive/10 rounded-lg transition-colors text-muted-foreground hover:text-destructive focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary/50"
                          title="Cancel"
                          aria-label="Cancel editing"
                        >
                          <X size={18} />
                        </button>
                        <button
                          onClick={handleSave}
                          className="p-2 hover:bg-primary/10 rounded-lg transition-colors text-muted-foreground hover:text-primary focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary/50"
                          title="Save Changes"
                          aria-label="Save Configuration"
                        >
                          <Save size={18} />
                        </button>
                      </div>
                    )}
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    {/* Provider */}
                    <div className="space-y-2">
                      <label className="text-sm font-medium text-muted-foreground">LLM Provider</label>
                      {editingAgent === config.agent_name ? (
                        <select
                          value={editForm?.llm_provider.toUpperCase()}
                          onChange={(e) => updateFormField('llm_provider', e.target.value)}
                          className="w-full bg-background border border-input rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-primary outline-none transition-all"
                        >
                          {PROVIDERS.map(p => <option key={p} value={p}>{p}</option>)}
                        </select>
                      ) : (
                        <div className="px-3 py-2 bg-muted/30 rounded-lg text-sm border border-transparent uppercase">
                          {config.llm_provider}
                        </div>
                      )}
                    </div>

                    {/* Model Name */}
                    <div className="space-y-2">
                      <label className="text-sm font-medium text-muted-foreground flex items-center gap-1">
                        Model Name
                        {editForm?.llm_provider.toLowerCase() !== 'none' && (
                          <span className="text-destructive text-xs">*</span>
                        )}
                      </label>
                      {editingAgent === config.agent_name ? (
                        <input
                          type="text"
                          value={editForm?.llm_config.model || ''}
                          onChange={(e) => updateFormField('llm_config.model', e.target.value)}
                          className="w-full bg-background border border-input rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-primary outline-none transition-all"
                          placeholder="e.g. gpt-4, llama3"
                        />
                      ) : (
                        <div className="px-3 py-2 bg-muted/30 rounded-lg text-sm border border-transparent">
                          {config.llm_config.model || <span className="text-muted-foreground italic">Not set</span>}
                        </div>
                      )}
                    </div>

                    {/* Base URL */}
                    <div className="space-y-2">
                      <label className="text-sm font-medium text-muted-foreground flex items-center gap-1">
                        Base URL
                      </label>
                      {editingAgent === config.agent_name ? (
                        <input
                          type="text"
                          value={editForm?.llm_config.base_url || ''}
                          onChange={(e) => updateFormField('llm_config.base_url', e.target.value)}
                          className="w-full bg-background border border-input rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-primary outline-none transition-all"
                          placeholder="e.g. http://localhost:11434/v1"
                        />
                      ) : (
                        <div className="px-3 py-2 bg-muted/30 rounded-lg text-sm border border-transparent truncate">
                          {config.llm_config.base_url || <span className="text-muted-foreground italic">Not set</span>}
                        </div>
                      )}
                    </div>

                    {/* API Key */}
                    <div className="space-y-2">
                      <label className="text-sm font-medium text-muted-foreground flex items-center gap-1">
                        API Key
                        {config.llm_provider !== 'ollama' && <span className="text-destructive text-xs">*</span>}
                      </label>
                      {editingAgent === config.agent_name ? (
                        <input
                          type="password"
                          value={editForm?.llm_config.api_key || ''}
                          onChange={(e) => updateFormField('llm_config.api_key', e.target.value)}
                          className="w-full bg-background border border-input rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-primary outline-none transition-all"
                          placeholder="Secret Key"
                        />
                      ) : (
                        <div className="px-3 py-2 bg-muted/30 rounded-lg text-sm border border-transparent">
                          {config.llm_config.api_key ? '••••••••••••••••' : <span className="text-muted-foreground italic">None</span>}
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              ))
            )}
          </div>
        ) : activeTab === 'mcp' ? (
          <div className="max-w-4xl mx-auto">
            <div className="flex items-center justify-between mb-8">
              <h2 className="text-xl font-semibold flex items-center gap-2">
                <Server size={20} className="text-primary" />
                Configured MCP Servers
              </h2>
              <button 
                className="flex items-center gap-2 px-4 py-2 bg-primary text-primary-foreground rounded-lg hover:bg-primary/90 transition-all active:scale-95 text-sm font-medium shadow-sm"
                onClick={() => toast('MCP server adding functionality coming soon!', { icon: 'ℹ️' })}
              >
                <Plus size={16} />
                Add Server
              </button>
            </div>

            <div className="grid gap-4">
              <div className="bg-card border border-border rounded-xl p-8 text-center space-y-4">
                  <div className="w-16 h-16 bg-primary/10 rounded-full flex items-center justify-center mx-auto">
                    <Info className="text-primary" size={32} />
                  </div>
                  <div>
                    <h3 className="text-lg font-medium">Model Context Protocol Integration</h3>
                    <p className="text-sm text-muted-foreground max-w-md mx-auto mt-2">
                      Connect your agents to external tools and data sources via MCP.
                      Support for both stdio and SSE servers is built-in.
                    </p>
                  </div>
                  <div className="pt-4">
                    <div className="inline-flex items-center gap-2 px-3 py-1 bg-muted rounded-full text-xs font-medium text-muted-foreground">
                      <div className="w-2 h-2 rounded-full bg-amber-500 animate-pulse" />
                      Configuration UI in development
                    </div>
                  </div>
              </div>
            </div>
          </div>
        ) : activeTab === 'prompts' ? (
          <div className="max-w-4xl mx-auto space-y-6">
            <div className="flex items-center justify-between mb-8">
              <h2 className="text-xl font-semibold flex items-center gap-2">
                <FileText size={20} className="text-primary" />
                System Prompts
              </h2>
            </div>
            
            {prompts.map((prompt) => (
              <div 
                key={prompt.agent_name}
                className={cn(
                  "group relative bg-card border border-border rounded-xl p-6 transition-all",
                  editingPrompt === prompt.agent_name ? "ring-2 ring-primary border-transparent" : "hover:border-primary/50"
                )}
              >
                <div className="flex items-start justify-between mb-4">
                  <div>
                    <h3 className="text-lg font-semibold">{prompt.agent_name}</h3>
                  </div>
                  {editingPrompt !== prompt.agent_name ? (
                    <button
                      onClick={() => handleEditPrompt(prompt)}
                      className="p-2 hover:bg-muted rounded-lg transition-colors text-muted-foreground hover:text-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary/50"
                      title="Edit Prompt"
                      aria-label="Edit Prompt"
                    >
                      <Edit2 size={18} />
                    </button>
                  ) : (
                    <div className="flex gap-2">
                      <button
                        onClick={handleCancelPrompt}
                        className="p-2 hover:bg-destructive/10 rounded-lg transition-colors text-muted-foreground hover:text-destructive focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary/50"
                        title="Cancel"
                        aria-label="Cancel editing prompt"
                      >
                        <X size={18} />
                      </button>
                      <button
                        onClick={handleSavePrompt}
                        className="p-2 hover:bg-primary/10 rounded-lg transition-colors text-muted-foreground hover:text-primary focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary/50"
                        title="Save Changes"
                        aria-label="Save Prompt"
                      >
                        <Save size={18} />
                      </button>
                    </div>
                  )}
                </div>

                <div className="mt-4">
                  {editingPrompt === prompt.agent_name ? (
                    <textarea
                      value={promptEditForm?.system_prompt || ''}
                      onChange={(e) => setPromptEditForm({ ...promptEditForm!, system_prompt: e.target.value })}
                      className="w-full bg-background border border-input rounded-lg px-4 py-3 text-sm focus:ring-2 focus:ring-primary outline-none transition-all h-64 font-mono leading-relaxed"
                      placeholder="Enter system prompt..."
                    />
                  ) : (
                    <div className="bg-muted/30 rounded-lg p-4 text-sm font-mono whitespace-pre-wrap leading-relaxed max-h-64 overflow-y-auto custom-scrollbar border border-transparent">
                      {prompt.system_prompt}
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>
        ) : activeTab === 'system' ? (
          <div className="max-w-4xl mx-auto space-y-8 animate-in fade-in duration-200">
            {/* Storage Card */}
            <div className="bg-card border border-border rounded-2xl p-6 shadow-sm">
              <div className="flex items-center justify-between pb-4 border-b border-border">
                <div className="flex items-center gap-3">
                  <div className="p-2.5 rounded-xl bg-primary/10 text-primary">
                    <HardDrive size={22} />
                  </div>
                  <div>
                    <h2 className="text-lg font-bold">Standardized Storage Directory</h2>
                    <p className="text-xs text-muted-foreground font-mono">
                      {storageData?.home || '~/.openagents'}
                    </p>
                  </div>
                </div>
                <span className="flex items-center gap-1.5 px-3 py-1 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 text-xs font-semibold">
                  <CheckCircle2 size={13} /> Active & Standardized
                </span>
              </div>

              {/* Grid of paths */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-6">
                <div className="p-4 rounded-xl bg-secondary/40 border border-border/60">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-medium text-muted-foreground">Database Engine</span>
                    <span className="text-[11px] font-mono px-2 py-0.5 rounded bg-blue-500/10 text-blue-400">SQLite</span>
                  </div>
                  <div className="font-mono text-xs text-foreground font-semibold mt-1 truncate">
                    {storageData?.database || '~/.openagents/openagents.db'}
                  </div>
                  <span className="text-[11px] text-muted-foreground mt-1 block">
                    Houses agent configurations, system prompts, and MCP registries.
                  </span>
                </div>

                <div className="p-4 rounded-xl bg-secondary/40 border border-border/60">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-medium text-muted-foreground">Credentials Vault</span>
                    <span className="text-[11px] font-mono px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-400 flex items-center gap-1">
                      <Shield size={10} /> 0o700 Secure
                    </span>
                  </div>
                  <div className="font-mono text-xs text-foreground font-semibold mt-1 truncate">
                    {storageData?.credentials_dir || '~/.openagents/credentials'}
                  </div>
                  <span className="text-[11px] text-muted-foreground mt-1 block">
                    Isolated Google OAuth credentials, refresh tokens, and user secrets.
                  </span>
                </div>

                <div className="p-4 rounded-xl bg-secondary/40 border border-border/60">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-medium text-muted-foreground">Autonomous Skills</span>
                    <span className="text-[11px] font-mono px-2 py-0.5 rounded bg-purple-500/10 text-purple-400">
                      {storageData?.skills_count ?? 6} Skills
                    </span>
                  </div>
                  <div className="font-mono text-xs text-foreground font-semibold mt-1 truncate">
                    {storageData?.skills_dir || '~/.openagents/skills'}
                  </div>
                  <span className="text-[11px] text-muted-foreground mt-1 block">
                    Standardized SKILL.md playbooks discovered dynamically by Orchestrator.
                  </span>
                </div>

                <div className="p-4 rounded-xl bg-secondary/40 border border-border/60">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-medium text-muted-foreground">Conversation History</span>
                    <span className="text-[11px] font-mono px-2 py-0.5 rounded bg-cyan-500/10 text-cyan-400">
                      {storageData?.history_sessions_count ?? 0} Sessions
                    </span>
                  </div>
                  <div className="font-mono text-xs text-foreground font-semibold mt-1 truncate">
                    {storageData?.history_dir || '~/.openagents/history'}
                  </div>
                  <span className="text-[11px] text-muted-foreground mt-1 block">
                    Persistent conversation transcripts, sessions index, and task checklists.
                  </span>
                </div>
              </div>
            </div>

            {/* Config Form Card */}
            <div className="bg-card border border-border rounded-2xl p-6 shadow-sm">
              <h2 className="text-lg font-bold mb-1">Global Configuration (~/.openagents/config.json)</h2>
              <p className="text-xs text-muted-foreground mb-6">
                System preferences and core execution engines.
              </p>

              <div className="space-y-6">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div>
                    <label className="block text-xs font-medium text-muted-foreground mb-1.5">
                      Default LLM Provider
                    </label>
                    <select
                      value={systemConfig.default_model_provider || 'gemini'}
                      onChange={(e) => setSystemConfig({ ...systemConfig, default_model_provider: e.target.value })}
                      className="w-full bg-background border border-input rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-primary outline-none"
                    >
                      <option value="gemini">Google Gemini</option>
                      <option value="openai">OpenAI</option>
                      <option value="anthropic">Anthropic Claude</option>
                      <option value="ollama">Ollama (Local)</option>
                      <option value="groq">Groq</option>
                    </select>
                  </div>

                  <div>
                    <label className="block text-xs font-medium text-muted-foreground mb-1.5">
                      Default Chat Mode
                    </label>
                    <select
                      value={systemConfig.default_chat_mode || 'multiagent'}
                      onChange={(e) => setSystemConfig({ ...systemConfig, default_chat_mode: e.target.value })}
                      className="w-full bg-background border border-input rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-primary outline-none"
                    >
                      <option value="multiagent">Multi-Agent Orchestration</option>
                      <option value="chat">Direct Conversational Chat</option>
                    </select>
                  </div>
                </div>

                {/* Feature Toggles */}
                <div className="pt-4 border-t border-border/60">
                  <h3 className="text-sm font-semibold mb-3">Core Engines & Guardrails</h3>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                    {[
                      { key: 'claude_mods', label: 'Claude Mods In-Process Engine', desc: 'Allows prompt-to-mod extensions and live HUD status.' },
                      { key: 'self_healing', label: 'Self-Healing Replanning Loop', desc: 'Recovers automatically on agent tool step failures.' },
                      { key: 'context_compaction', label: 'Dynamic Context Compactor', desc: 'Truncates middle logs while preserving diagnostic heads and tails.' },
                      { key: 'human_in_the_loop', label: 'Human-In-The-Loop Risk Gateway', desc: 'Requires manual confirmation for destructive shell commands.' },
                    ].map((feature) => (
                      <label
                        key={feature.key}
                        className="flex items-start gap-3 p-3.5 rounded-xl border border-border/60 bg-muted/20 hover:bg-muted/40 cursor-pointer transition-colors"
                      >
                        <input
                          type="checkbox"
                          checked={systemConfig.features?.[feature.key] ?? true}
                          onChange={(e) =>
                            setSystemConfig({
                              ...systemConfig,
                              features: {
                                ...systemConfig.features,
                                [feature.key]: e.target.checked
                              }
                            })
                          }
                          className="mt-1 rounded border-border text-primary focus:ring-primary"
                        />
                        <div>
                          <div className="text-sm font-medium">{feature.label}</div>
                          <div className="text-xs text-muted-foreground mt-0.5">{feature.desc}</div>
                        </div>
                      </label>
                    ))}
                  </div>
                </div>

                <div className="pt-4 border-t border-border/60 flex items-center justify-between">
                  <span className="text-xs text-muted-foreground font-mono">
                    Target: ~/.openagents/config.json
                  </span>
                  <button
                    onClick={handleSaveSystemConfig}
                    disabled={savingSystem}
                    className="flex items-center gap-2 bg-primary text-primary-foreground px-5 py-2.5 rounded-xl font-medium hover:bg-primary/90 transition-all shadow-sm active:scale-95 text-sm"
                  >
                    <Save size={16} />
                    {savingSystem ? 'Saving...' : 'Save System Configuration'}
                  </button>
                </div>
              </div>
            </div>
          </div>
        ) : (
          <div className="max-w-2xl mx-auto">
            <div className="bg-card border border-border rounded-2xl overflow-hidden shadow-sm">
              <div className="h-32 bg-gradient-to-r from-primary/10 to-primary/5 p-8 flex items-end">
                <div className="flex items-center gap-4">
                  <div className="w-20 h-20 bg-background rounded-2xl border-4 border-card shadow-xl flex items-center justify-center overflow-hidden">
                    <User className="text-primary/40" size={40} />
                  </div>
                  <div className="mb-2">
                    <h2 className="text-xl font-bold">User Profile</h2>
                    <p className="text-sm text-muted-foreground">Manage your account and preferences</p>
                  </div>
                </div>
              </div>

              <div className="p-8 space-y-8">
                <div className="grid gap-6">
                  <div className="space-y-1">
                    <label className="text-sm font-medium text-muted-foreground">Username</label>
                    <div className="flex items-center justify-between p-3 bg-muted/30 rounded-lg border border-border/50">
                      <span className="font-medium text-foreground">Google User</span>
                      <span className="text-xs bg-primary/10 text-primary px-2 py-0.5 rounded uppercase">Verified</span>
                    </div>
                  </div>

                  <div className="space-y-1">
                    <label className="text-sm font-medium text-muted-foreground">Account Status</label>
                    <p className="text-sm">Currently signed in with Google OAuth. Your tokens are securely stored locally.</p>
                  </div>
                </div>

                <div className="pt-6 border-t border-border/50">
                  <button
                    onClick={async () => {
                      try {
                        await axios.post(`${BASE_URL}/auth/logout`);
                        toast.success('Logged out successfully');
                        window.location.reload(); // Force reload to trigger AuthPopup
                      } catch (error) {
                        toast.error('Failed to sign out');
                      }
                    }}
                    className="flex items-center gap-2 px-6 py-3 bg-destructive/10 text-destructive rounded-xl hover:bg-destructive hover:text-destructive-foreground transition-all font-medium"
                  >
                    <LogOut size={18} />
                    Sign Out and Clear Session
                  </button>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default SettingsPage;
