import React, { useState, useEffect } from 'react';
import { 
  Settings as SettingsIcon, 
  Cpu, 
  Server, 
  Save, 
  Edit2, 
  X,
  Plus,
  Info
} from 'lucide-react';
import { cn } from '../lib/utils';
import axios from 'axios';
import { toast } from 'react-hot-toast';

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

const PROVIDERS = ['NONE', 'OLLAMA', 'OPENAI', 'GEMINI', 'ANTHROPIC', 'GROQ', 'OTHERS'];

const SettingsPage: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'agents' | 'mcp'>('agents');
  const [configs, setConfigs] = useState<AgentConfig[]>([]);
  const [editingAgent, setEditingAgent] = useState<string | null>(null);
  const [editForm, setEditForm] = useState<AgentConfig | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchConfigs();
  }, []);

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
        "RAGAgent",
        "EmbeddingModel",
        "IntegratorAgent",
        "GuardianAgent"
      ];

      const sortedConfigs = response.data.sort((a: AgentConfig, b: AgentConfig) => {
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
                        className="p-2 hover:bg-muted rounded-lg transition-colors text-muted-foreground hover:text-foreground"
                        title="Edit Configuration"
                      >
                        <Edit2 size={18} />
                      </button>
                    ) : (
                      <div className="flex gap-2">
                        <button
                          onClick={handleCancel}
                          className="p-2 hover:bg-destructive/10 rounded-lg transition-colors text-muted-foreground hover:text-destructive"
                          title="Cancel"
                        >
                          <X size={18} />
                        </button>
                        <button
                          onClick={handleSave}
                          className="p-2 hover:bg-primary/10 rounded-lg transition-colors text-muted-foreground hover:text-primary"
                          title="Save Changes"
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
        ) : (
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
        )}
      </div>
    </div>
  );
};

export default SettingsPage;
