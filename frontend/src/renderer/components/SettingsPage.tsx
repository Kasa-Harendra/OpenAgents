import React, { useState, useEffect } from 'react';
import { 
  Settings as SettingsIcon, 
  Cpu, 
  Save, 
  Edit2, 
  X, 
  FileText,
  Bot,
  Plus,
  Trash2,
  Server,
  Wrench,
  Sparkles,
  Check,
  AlertCircle,
  Terminal,
  Globe,
  Key,
  Database,
  ShieldCheck,
  ExternalLink,
  Copy,
  RefreshCw,
  CheckCircle2,
  Lock,
  Code,
  Zap,
  Layers,
  FileJson
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

export interface CustomAgent {
  id: string;
  name: string;
  description: string;
  system_prompt: string;
  llm_provider: string;
  model_name: string;
  mcp_servers: string[];
  skills: string[];
  is_active: boolean;
  created_at?: string;
  updated_at?: string;
}

export interface RegisteredMCPServer {
  id: string;
  name: string;
  type: string; // 'stdio' | 'sse'
  command?: string | null;
  args?: string[] | null;
  env?: Record<string, string> | null;
  url?: string | null;
  updated_at?: string;
}

interface MCPPreset {
  id: string;
  name: string;
  type: string;
  command?: string;
  args?: string[];
  env?: Record<string, string>;
  url?: string;
  description: string;
  oauth_provider?: string;
  oauth_connected?: boolean;
  oauth_user?: string | null;
}

export interface OAuthProvider {
  id: string;
  name: string;
  description: string;
  icon: string;
  type: string;
  category: string;
  connected: boolean;
  user?: string | null;
  avatar_url?: string | null;
  scopes?: string | null;
  expires_at?: number | null;
  updated_at?: number | null;
}

interface AvailableOptions {
  skills: { id: string; name: string; description: string; path?: string }[];
  mcp_servers: { name: string; type: string; description?: string; id?: string }[];
}

const PROVIDERS = ['NONE', 'OLLAMA', 'OPENAI', 'GEMINI', 'ANTHROPIC', 'GROQ', 'OTHERS'];
const COMMON_MODELS = ['llama3.1', 'llama3.2', 'gpt-4o', 'gpt-4o-mini', 'claude-3-5-sonnet', 'gemini-1.5-pro', 'deepseek-r1'];

const SettingsPage: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'agents' | 'custom_agents' | 'mcp_servers' | 'prompts'>('agents');
  
  // Built-in agents
  const [configs, setConfigs] = useState<AgentConfig[]>([]);
  const [prompts, setPrompts] = useState<AgentPrompt[]>([]);
  const [editingAgent, setEditingAgent] = useState<string | null>(null);
  const [editForm, setEditForm] = useState<AgentConfig | null>(null);
  const [editingPrompt, setEditingPrompt] = useState<string | null>(null);
  const [promptEditForm, setPromptEditForm] = useState<AgentPrompt | null>(null);
  const [loading, setLoading] = useState(true);

  // User-created Custom Agents
  const [customAgents, setCustomAgents] = useState<CustomAgent[]>([]);
  const [loadingCustomAgents, setLoadingCustomAgents] = useState<boolean>(false);
  const [availableOptions, setAvailableOptions] = useState<AvailableOptions>({ skills: [], mcp_servers: [] });
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingCustomAgentId, setEditingCustomAgentId] = useState<string | null>(null);

  const [agentForm, setAgentForm] = useState({
    name: '',
    description: '',
    system_prompt: '',
    llm_provider: 'OLLAMA',
    model_name: 'llama3.1',
    mcp_servers: [] as string[],
    skills: [] as string[],
    is_active: true
  });
  const [customMcpInput, setCustomMcpInput] = useState('');
  const [customSkillInput, setCustomSkillInput] = useState('');

  // MCP Servers Registry State
  const [mcpServers, setMcpServers] = useState<RegisteredMCPServer[]>([]);
  const [mcpPresets, setMcpPresets] = useState<MCPPreset[]>([]);
  const [loadingMcpServers, setLoadingMcpServers] = useState<boolean>(false);
  const [isMcpModalOpen, setIsMcpModalOpen] = useState(false);
  const [editingMcpId, setEditingMcpId] = useState<string | null>(null);

  const [mcpForm, setMcpForm] = useState<{
    name: string;
    type: 'stdio' | 'sse';
    command: string;
    args: string;
    url: string;
    env: { key: string; value: string }[];
  }>({
    name: '',
    type: 'stdio',
    command: 'npx',
    args: '',
    url: '',
    env: []
  });

  // OAuth Management State (Zero-Config Claude-Style)
  const [oauthProviders, setOauthProviders] = useState<OAuthProvider[]>([]);
  const [loadingOAuth, setLoadingOAuth] = useState<boolean>(false);
  const [oauthModal, setOauthModal] = useState<{
    isOpen: boolean;
    provider: string;
    flowId?: string;
    userCode?: string;
    verificationUri?: string;
    status: 'pending' | 'success' | 'error';
    message?: string;
    error?: string;
  } | null>(null);
  const [copiedCode, setCopiedCode] = useState(false);

  // Raw JSON & Direct OAuth Panel State inside MCP Registration Modal
  const [mcpModalTab, setMcpModalTab] = useState<'form' | 'json'>('form');
  const [rawJsonInput, setRawJsonInput] = useState<string>('');
  const [rawJsonError, setRawJsonError] = useState<string | null>(null);
  const [jsonOAuthProvider, setJsonOAuthProvider] = useState<'github' | 'google' | 'slack' | 'custom'>('github');
  const [customOAuthParams, setCustomOAuthParams] = useState({
    client_id: '',
    auth_url: '',
    token_url: '',
    scopes: 'read write',
    redirect_port: 8765
  });

  useEffect(() => {
    fetchConfigs();
    fetchPrompts();
    fetchCustomAgents();
    fetchAvailableOptions();
    fetchMcpServers();
    fetchMcpPresets();
    fetchOAuthProviders();
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

  const fetchCustomAgents = async () => {
    try {
      setLoadingCustomAgents(true);
      const res = await axios.get(`${BASE_URL}/custom-agents`);
      setCustomAgents(res.data);
    } catch (error) {
      console.error('Failed to fetch custom agents:', error);
    } finally {
      setLoadingCustomAgents(false);
    }
  };

  const fetchAvailableOptions = async () => {
    try {
      const res = await axios.get(`${BASE_URL}/custom-agents/available-options`);
      setAvailableOptions(res.data);
    } catch (error) {
      console.error('Failed to fetch available options:', error);
    }
  };

  const fetchMcpServers = async () => {
    try {
      setLoadingMcpServers(true);
      const res = await axios.get(`${BASE_URL}/mcp-servers`);
      setMcpServers(res.data);
    } catch (error) {
      console.error('Failed to fetch MCP servers:', error);
    } finally {
      setLoadingMcpServers(false);
    }
  };

  const fetchMcpPresets = async () => {
    try {
      const res = await axios.get(`${BASE_URL}/mcp-servers/presets`);
      setMcpPresets(res.data);
    } catch (error) {
      console.error('Failed to fetch MCP presets:', error);
    }
  };

  const fetchOAuthProviders = async () => {
    try {
      setLoadingOAuth(true);
      const res = await axios.get(`${BASE_URL}/oauth/providers`);
      setOauthProviders(res.data);
    } catch (error) {
      console.error('Failed to fetch OAuth providers:', error);
    } finally {
      setLoadingOAuth(false);
    }
  };

  const handleConnectOAuth = async (providerId: string) => {
    try {
      setCopiedCode(false);
      setOauthModal({
        isOpen: true,
        provider: providerId,
        status: 'pending',
        message: 'Initiating secure authorization...'
      });

      const res = await axios.post(`${BASE_URL}/oauth/authorize/${providerId}`);
      const data = res.data;

      setOauthModal({
        isOpen: true,
        provider: providerId,
        flowId: data.flow_id,
        userCode: data.user_code,
        verificationUri: data.verification_uri,
        status: 'pending',
        message: data.message || 'Waiting for browser approval...'
      });

      // Poll background flow status
      if (data.flow_id) {
        const flowId = data.flow_id;
        const intervalId = setInterval(async () => {
          try {
            const check = await axios.get(`${BASE_URL}/oauth/flows/${flowId}`);
            if (check.data.status === 'success') {
              clearInterval(intervalId);
              setOauthModal(prev => prev ? { ...prev, status: 'success', message: 'Authentication Successful!' } : null);
              toast.success(`Connected to ${providerId.toUpperCase()} successfully!`);
              setTimeout(() => {
                setOauthModal(null);
              }, 1600);
              fetchOAuthProviders();
              fetchMcpPresets();
            } else if (check.data.status === 'error' || check.data.status === 'expired') {
              clearInterval(intervalId);
              setOauthModal(prev => prev ? { ...prev, status: 'error', error: check.data.error || 'Authorization failed or timed out' } : null);
            }
          } catch (e) {
            // Keep polling
          }
        }, 2200);
      }
    } catch (err: any) {
      const msg = err.response?.data?.detail || err.message || 'Failed to start authorization';
      setOauthModal(prev => prev ? { ...prev, status: 'error', error: msg } : null);
      toast.error(`Authorization error: ${msg}`);
    }
  };

  const handleDisconnectOAuth = async (providerId: string) => {
    if (!window.confirm(`Disconnect ${providerId.toUpperCase()}? MCP servers using this connection will lose access.`)) {
      return;
    }
    try {
      await axios.delete(`${BASE_URL}/oauth/providers/${providerId}`);
      toast.success(`Disconnected ${providerId}`);
      fetchOAuthProviders();
      fetchMcpPresets();
    } catch (err: any) {
      toast.error(`Failed to disconnect: ${err.message}`);
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

  // Custom Agent Management Handlers
  const handleOpenCreateModal = () => {
    setEditingCustomAgentId(null);
    setAgentForm({
      name: '',
      description: '',
      system_prompt: '',
      llm_provider: 'OLLAMA',
      model_name: 'llama3.1',
      mcp_servers: [],
      skills: [],
      is_active: true
    });
    setCustomMcpInput('');
    setCustomSkillInput('');
    setIsModalOpen(true);
  };

  const handleOpenEditModal = (agent: CustomAgent) => {
    setEditingCustomAgentId(agent.id);
    setAgentForm({
      name: agent.name,
      description: agent.description || '',
      system_prompt: agent.system_prompt || '',
      llm_provider: (agent.llm_provider || 'ollama').toUpperCase(),
      model_name: agent.model_name || 'llama3.1',
      mcp_servers: [...(agent.mcp_servers || [])],
      skills: [...(agent.skills || [])],
      is_active: agent.is_active
    });
    setCustomMcpInput('');
    setCustomSkillInput('');
    setIsModalOpen(true);
  };

  const handleToggleMcp = (mcpName: string) => {
    setAgentForm(prev => {
      const exists = prev.mcp_servers.includes(mcpName);
      return {
        ...prev,
        mcp_servers: exists 
          ? prev.mcp_servers.filter(m => m !== mcpName)
          : [...prev.mcp_servers, mcpName]
      };
    });
  };

  const handleAddCustomMcp = () => {
    const val = customMcpInput.trim();
    if (!val) return;
    if (!agentForm.mcp_servers.includes(val)) {
      setAgentForm(prev => ({ ...prev, mcp_servers: [...prev.mcp_servers, val] }));
    }
    setCustomMcpInput('');
  };

  const handleToggleSkill = (skillName: string) => {
    setAgentForm(prev => {
      const exists = prev.skills.includes(skillName);
      return {
        ...prev,
        skills: exists 
          ? prev.skills.filter(s => s !== skillName)
          : [...prev.skills, skillName]
      };
    });
  };

  const handleAddCustomSkill = () => {
    const val = customSkillInput.trim();
    if (!val) return;
    if (!agentForm.skills.includes(val)) {
      setAgentForm(prev => ({ ...prev, skills: [...prev.skills, val] }));
    }
    setCustomSkillInput('');
  };

  const handleSaveCustomAgent = async () => {
    const nameClean = agentForm.name.trim();
    if (!nameClean) {
      toast.error('Agent name is required');
      return;
    }

    const hasMcp = agentForm.mcp_servers.length > 0;
    const hasSkill = agentForm.skills.length > 0;
    if (!hasMcp && !hasSkill) {
      toast.error('An agent must have at least one MCP server or Skill (or both)');
      return;
    }

    try {
      const payload = {
        name: nameClean,
        description: agentForm.description.trim(),
        system_prompt: agentForm.system_prompt.trim(),
        llm_provider: agentForm.llm_provider.toLowerCase(),
        model_name: agentForm.model_name.trim() || 'llama3.1',
        mcp_servers: agentForm.mcp_servers,
        skills: agentForm.skills,
        is_active: agentForm.is_active
      };

      if (editingCustomAgentId) {
        await axios.put(`${BASE_URL}/custom-agents/${editingCustomAgentId}`, payload);
        toast.success(`Agent '${payload.name}' updated successfully`);
      } else {
        await axios.post(`${BASE_URL}/custom-agents`, payload);
        toast.success(`Agent '${payload.name}' created successfully`);
      }

      setIsModalOpen(false);
      fetchCustomAgents();
    } catch (error: any) {
      console.error('Failed to save agent:', error);
      const detail = error.response?.data?.detail || 'Failed to save agent';
      toast.error(detail);
    }
  };

  const handleDeleteCustomAgent = async (agent: CustomAgent) => {
    if (!window.confirm(`Are you sure you want to delete '${agent.name}'?`)) {
      return;
    }
    try {
      await axios.delete(`${BASE_URL}/custom-agents/${agent.id}`);
      toast.success(`Agent '${agent.name}' deleted`);
      fetchCustomAgents();
    } catch (error) {
      console.error('Failed to delete agent:', error);
      toast.error('Failed to delete agent');
    }
  };

  const handleToggleAgentActive = async (agent: CustomAgent) => {
    try {
      const res = await axios.patch(`${BASE_URL}/custom-agents/${agent.id}/toggle`);
      setCustomAgents(prev => prev.map(a => a.id === agent.id ? { ...a, is_active: res.data.is_active } : a));
      toast.success(`${agent.name} is now ${res.data.is_active ? 'Active' : 'Inactive'}`);
    } catch (error) {
      console.error('Failed to toggle agent active state:', error);
      toast.error('Failed to update agent status');
    }
  };

  // MCP Server Registry Handlers
  const generateJsonFromForm = (formState: typeof mcpForm) => {
    const envObj: Record<string, string> = {};
    for (const item of formState.env) {
      if (item.key.trim()) {
        envObj[item.key.trim()] = item.value;
      }
    }
    const parsedArgs = formState.args.trim() ? formState.args.trim().split(/\s+/) : [];
    const config: any = {
      name: formState.name || 'my-mcp-server',
      type: formState.type,
    };
    if (formState.type === 'stdio') {
      config.command = formState.command || 'npx';
      config.args = parsedArgs;
    } else {
      config.url = formState.url || 'http://localhost:3000/sse';
    }
    config.env = envObj;
    return JSON.stringify(config, null, 2);
  };

  const syncRawJsonToForm = (jsonText: string): boolean => {
    try {
      setRawJsonError(null);
      if (!jsonText.trim()) {
        setRawJsonError('JSON configuration cannot be empty');
        return false;
      }
      const parsed = JSON.parse(jsonText);
      const keys = Object.keys(parsed);

      let targetName = parsed.name || '';
      let targetType: 'stdio' | 'sse' = (parsed.type?.toLowerCase() === 'sse') ? 'sse' : 'stdio';
      let targetCommand = parsed.command || 'npx';
      let targetArgs: string[] = parsed.args || [];
      let targetUrl = parsed.url || '';
      let targetEnv: Record<string, string> = parsed.env || {};

      // Detect Claude Desktop config format: { "serverName": { "command": "...", "args": [...], "env": {...} } }
      if (!parsed.name && keys.length === 1 && typeof parsed[keys[0]] === 'object' && parsed[keys[0]] !== null) {
        targetName = keys[0];
        const inner = parsed[keys[0]];
        targetType = inner.url ? 'sse' : 'stdio';
        targetCommand = inner.command || 'npx';
        targetArgs = inner.args || [];
        targetUrl = inner.url || '';
        targetEnv = inner.env || {};
      }

      setMcpForm({
        name: targetName,
        type: targetType,
        command: targetCommand,
        args: Array.isArray(targetArgs) ? targetArgs.join(' ') : String(targetArgs || ''),
        url: targetUrl,
        env: Object.entries(targetEnv).map(([key, value]) => ({ key, value: String(value) }))
      });

      // Auto-detect OAuth provider
      const candidate = parsed.oauth_provider || parsed.oauth?.provider;
      if (candidate && ['github', 'google', 'slack', 'custom'].includes(candidate.toLowerCase())) {
        setJsonOAuthProvider(candidate.toLowerCase() as any);
      } else if (targetName.toLowerCase().includes('github')) {
        setJsonOAuthProvider('github');
      } else if (targetName.toLowerCase().includes('google') || targetName.toLowerCase().includes('drive') || targetName.toLowerCase().includes('gmail')) {
        setJsonOAuthProvider('google');
      } else if (targetName.toLowerCase().includes('slack')) {
        setJsonOAuthProvider('slack');
      }

      return true;
    } catch (err: any) {
      setRawJsonError(err.message || 'Invalid JSON syntax');
      return false;
    }
  };

  const handleSwitchToTab = (tab: 'form' | 'json') => {
    if (tab === 'json') {
      setRawJsonInput(generateJsonFromForm(mcpForm));
      setRawJsonError(null);
    } else {
      syncRawJsonToForm(rawJsonInput);
    }
    setMcpModalTab(tab);
  };

  const handleLoadRawJsonTemplate = (templateKey: 'github' | 'googledrive' | 'slack' | 'custom_sse' | 'claude_desktop') => {
    let tpl = {};
    if (templateKey === 'github') {
      tpl = {
        name: 'GitHub',
        type: 'stdio',
        command: 'npx',
        args: ['-y', '@modelcontextprotocol/server-github'],
        env: {
          GITHUB_PERSONAL_ACCESS_TOKEN: ''
        },
        oauth_provider: 'github'
      };
      setJsonOAuthProvider('github');
    } else if (templateKey === 'googledrive') {
      tpl = {
        name: 'Google Drive',
        type: 'stdio',
        command: 'npx',
        args: ['-y', '@piotr-agier/google-drive-mcp'],
        env: {},
        oauth_provider: 'google'
      };
      setJsonOAuthProvider('google');
    } else if (templateKey === 'slack') {
      tpl = {
        name: 'Slack',
        type: 'stdio',
        command: 'npx',
        args: ['-y', '@modelcontextprotocol/server-slack'],
        env: {
          SLACK_BOT_TOKEN: '',
          SLACK_TEAM_ID: ''
        },
        oauth_provider: 'slack'
      };
      setJsonOAuthProvider('slack');
    } else if (templateKey === 'custom_sse') {
      tpl = {
        name: 'Remote Custom MCP',
        type: 'sse',
        url: 'https://mcp.mycompany.com/sse',
        env: {
          AUTHORIZATION_TOKEN: ''
        },
        oauth: {
          provider: 'custom',
          client_id: 'client_123',
          auth_url: 'https://auth.mycompany.com/authorize',
          token_url: 'https://auth.mycompany.com/token',
          scopes: 'read write'
        }
      };
      setJsonOAuthProvider('custom');
      setCustomOAuthParams({
        client_id: 'client_123',
        auth_url: 'https://auth.mycompany.com/authorize',
        token_url: 'https://auth.mycompany.com/token',
        scopes: 'read write',
        redirect_port: 8765
      });
    } else if (templateKey === 'claude_desktop') {
      tpl = {
        filesystem: {
          command: 'npx',
          args: ['-y', '@modelcontextprotocol/server-filesystem', './workspace'],
          env: {}
        }
      };
    }
    const formatted = JSON.stringify(tpl, null, 2);
    setRawJsonInput(formatted);
    setRawJsonError(null);
    syncRawJsonToForm(formatted);
  };

  const handleFormatRawJson = () => {
    try {
      const parsed = JSON.parse(rawJsonInput);
      setRawJsonInput(JSON.stringify(parsed, null, 2));
      setRawJsonError(null);
      toast.success('JSON formatted');
    } catch (e: any) {
      setRawJsonError(e.message);
      toast.error('Cannot format invalid JSON');
    }
  };

  const handleTriggerAuthFromRawJson = async () => {
    let providerToUse = jsonOAuthProvider;
    let customParams = { ...customOAuthParams };

    try {
      if (rawJsonInput.trim()) {
        const parsed = JSON.parse(rawJsonInput);
        const candidate = parsed.oauth_provider || parsed.oauth?.provider;
        if (candidate && ['github', 'google', 'slack', 'custom'].includes(candidate.toLowerCase())) {
          providerToUse = candidate.toLowerCase() as any;
          setJsonOAuthProvider(providerToUse);
        }
        if (parsed.oauth?.client_id && parsed.oauth?.auth_url && parsed.oauth?.token_url) {
          providerToUse = 'custom';
          setJsonOAuthProvider('custom');
          customParams = {
            client_id: parsed.oauth.client_id,
            auth_url: parsed.oauth.auth_url,
            token_url: parsed.oauth.token_url,
            scopes: parsed.oauth.scopes || 'read write',
            redirect_port: parsed.oauth.redirect_port || 8765
          };
          setCustomOAuthParams(customParams);
        }
      }
    } catch (_) {}

    try {
      setCopiedCode(false);
      setOauthModal({
        isOpen: true,
        provider: providerToUse,
        status: 'pending',
        message: `Initiating ${providerToUse.toUpperCase()} authorization...`
      });

      let res;
      if (providerToUse === 'custom') {
        if (!customParams.client_id || !customParams.auth_url || !customParams.token_url) {
          toast.error('Client ID, Auth URL, and Token URL are required for custom OAuth');
          setOauthModal(null);
          return;
        }
        res = await axios.post(`${BASE_URL}/oauth/authorize/custom`, customParams);
      } else {
        res = await axios.post(`${BASE_URL}/oauth/authorize/${providerToUse}`);
      }

      const data = res.data;
      setOauthModal({
        isOpen: true,
        provider: providerToUse,
        flowId: data.flow_id,
        userCode: data.user_code,
        verificationUri: data.verification_uri,
        status: 'pending',
        message: data.message || 'Waiting for browser approval...'
      });

      if (data.flow_id) {
        const flowId = data.flow_id;
        const intervalId = setInterval(async () => {
          try {
            const check = await axios.get(`${BASE_URL}/oauth/flows/${flowId}`);
            if (check.data.status === 'success') {
              clearInterval(intervalId);
              setOauthModal(prev => prev ? { ...prev, status: 'success', message: 'Authentication Successful!' } : null);
              toast.success(`Authorized ${providerToUse.toUpperCase()} successfully!`);

              // Auto-inject tokens into rawJsonInput and form
              try {
                const envRes = await axios.get(`${BASE_URL}/oauth/env/${providerToUse}`);
                const injectedEnv = envRes.data || {};

                try {
                  const currentObj = JSON.parse(rawJsonInput || '{}');
                  currentObj.env = { ...(currentObj.env || {}), ...injectedEnv };
                  const updatedStr = JSON.stringify(currentObj, null, 2);
                  setRawJsonInput(updatedStr);
                  syncRawJsonToForm(updatedStr);
                } catch (_) {}
              } catch (_) {}

              setTimeout(() => {
                setOauthModal(null);
              }, 1600);
              fetchOAuthProviders();
              fetchMcpPresets();
            } else if (check.data.status === 'error' || check.data.status === 'expired') {
              clearInterval(intervalId);
              setOauthModal(prev => prev ? { ...prev, status: 'error', error: check.data.error || 'Authorization failed' } : null);
            }
          } catch (e) {
            // Keep polling
          }
        }, 2200);
      }
    } catch (err: any) {
      const msg = err.response?.data?.detail || err.message || 'Authorization failed';
      setOauthModal(prev => prev ? { ...prev, status: 'error', error: msg } : null);
      toast.error(`Authorization error: ${msg}`);
    }
  };

  const handleOpenCreateMcpModal = (preset?: MCPPreset) => {
    setEditingMcpId(null);
    setMcpModalTab('form');
    setRawJsonError(null);
    let initialForm = {
      name: '',
      type: 'stdio' as 'stdio' | 'sse',
      command: 'npx',
      args: '',
      url: '',
      env: [] as { key: string; value: string }[]
    };
    if (preset) {
      initialForm = {
        name: preset.name,
        type: (preset.type as 'stdio' | 'sse') || 'stdio',
        command: preset.command || 'npx',
        args: (preset.args || []).join(' '),
        url: preset.url || '',
        env: Object.entries(preset.env || {}).map(([key, value]) => ({ key, value }))
      };
      if (preset.oauth_provider) {
        setJsonOAuthProvider((preset.oauth_provider as any) || 'github');
      }
    }
    setMcpForm(initialForm);
    setRawJsonInput(generateJsonFromForm(initialForm));
    setIsMcpModalOpen(true);
  };

  const handleOpenEditMcpModal = (server: RegisteredMCPServer) => {
    setEditingMcpId(server.id);
    setMcpModalTab('form');
    setRawJsonError(null);
    const initialForm = {
      name: server.name,
      type: (server.type as 'stdio' | 'sse') || 'stdio',
      command: server.command || '',
      args: (server.args || []).join(' '),
      url: server.url || '',
      env: Object.entries(server.env || {}).map(([key, value]) => ({ key, value }))
    };
    setMcpForm(initialForm);
    setRawJsonInput(generateJsonFromForm(initialForm));
    setIsMcpModalOpen(true);
  };

  const handleSaveMcpServer = async () => {
    // If user is currently editing on JSON tab, validate & sync first
    if (mcpModalTab === 'json') {
      const ok = syncRawJsonToForm(rawJsonInput);
      if (!ok) {
        toast.error('Cannot save: Invalid JSON in Raw JSON panel');
        return;
      }
    }

    const nameClean = mcpForm.name.trim();
    if (!nameClean) {
      toast.error('Server name is required');
      return;
    }

    if (mcpForm.type === 'stdio' && !mcpForm.command.trim()) {
      toast.error('Command is required for stdio server');
      return;
    }

    if (mcpForm.type === 'sse' && !mcpForm.url.trim()) {
      toast.error('URL is required for SSE server');
      return;
    }

    // Build args array
    const parsedArgs = mcpForm.args.trim() ? mcpForm.args.trim().split(/\s+/) : [];
    
    // Build env dictionary
    const envObj: Record<string, string> = {};
    for (const item of mcpForm.env) {
      if (item.key.trim()) {
        envObj[item.key.trim()] = item.value;
      }
    }

    const payload = {
      name: nameClean,
      type: mcpForm.type,
      command: mcpForm.type === 'stdio' ? mcpForm.command.trim() : null,
      args: mcpForm.type === 'stdio' ? parsedArgs : [],
      env: envObj,
      url: mcpForm.type === 'sse' ? mcpForm.url.trim() : null
    };

    try {
      if (editingMcpId) {
        await axios.put(`${BASE_URL}/mcp-servers/${editingMcpId}`, payload);
        toast.success(`MCP Server '${nameClean}' updated successfully`);
      } else {
        await axios.post(`${BASE_URL}/mcp-servers`, payload);
        toast.success(`MCP Server '${nameClean}' registered successfully`);
      }
      setIsMcpModalOpen(false);
      fetchMcpServers();
      fetchAvailableOptions();
    } catch (error: any) {
      console.error('Failed to save MCP server:', error);
      const detail = error.response?.data?.detail || 'Failed to save MCP server';
      toast.error(detail);
    }
  };

  const handleDeleteMcpServer = async (server: RegisteredMCPServer) => {
    if (!window.confirm(`Are you sure you want to remove '${server.name}' from MCP registry?`)) {
      return;
    }
    try {
      await axios.delete(`${BASE_URL}/mcp-servers/${server.id}`);
      toast.success(`MCP Server '${server.name}' removed`);
      fetchMcpServers();
      fetchAvailableOptions();
    } catch (error) {
      console.error('Failed to delete MCP server:', error);
      toast.error('Failed to delete MCP server');
    }
  };

  const handleAddEnvRow = () => {
    setMcpForm(prev => ({ ...prev, env: [...prev.env, { key: '', value: '' }] }));
  };

  const handleUpdateEnvRow = (idx: number, field: 'key' | 'value', val: string) => {
    setMcpForm(prev => {
      const next = [...prev.env];
      next[idx] = { ...next[idx], [field]: val };
      return { ...prev, env: next };
    });
  };

  const handleRemoveEnvRow = (idx: number) => {
    setMcpForm(prev => ({ ...prev, env: prev.env.filter((_, i) => i !== idx) }));
  };

  const hasSelectedMcp = agentForm.mcp_servers.length > 0;
  const hasSelectedSkill = agentForm.skills.length > 0;
  const isCapabilitiesValid = hasSelectedMcp || hasSelectedSkill;

  return (
    <div className="flex flex-col h-full bg-background overflow-hidden animate-fade-in">
      {/* Header */}
      <div className="px-8 py-6 border-b border-border flex items-center justify-between shrink-0">
        <div>
          <h1 className="text-2xl font-semibold flex items-center gap-2">
            <SettingsIcon className="text-primary" size={24} />
            Settings
          </h1>
          <p className="text-sm text-muted-foreground mt-1">Configure your built-in agents, custom agents, MCP registry, and prompts</p>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex px-8 border-b border-border bg-muted/30 shrink-0 overflow-x-auto">
        <button
          onClick={() => setActiveTab('agents')}
          className={cn(
            "px-6 py-3 text-sm font-medium border-b-2 transition-all flex items-center gap-2 shrink-0",
            activeTab === 'agents' 
              ? "border-primary text-primary" 
              : "border-transparent text-muted-foreground hover:text-foreground"
          )}
        >
          <Cpu size={16} />
          Agent Configurations
        </button>
        <button
          onClick={() => setActiveTab('custom_agents')}
          className={cn(
            "px-6 py-3 text-sm font-medium border-b-2 transition-all flex items-center gap-2 shrink-0",
            activeTab === 'custom_agents' 
              ? "border-primary text-primary" 
              : "border-transparent text-muted-foreground hover:text-foreground"
          )}
        >
          <Bot size={16} />
          My Agents
          {customAgents.length > 0 && (
            <span className="ml-1.5 px-1.5 py-0.2 bg-primary/20 text-primary rounded-full text-xs font-semibold">
              {customAgents.length}
            </span>
          )}
        </button>
        <button
          onClick={() => setActiveTab('mcp_servers')}
          className={cn(
            "px-6 py-3 text-sm font-medium border-b-2 transition-all flex items-center gap-2 shrink-0",
            activeTab === 'mcp_servers' 
              ? "border-primary text-primary" 
              : "border-transparent text-muted-foreground hover:text-foreground"
          )}
        >
          <Server size={16} />
          MCP Servers
          {mcpServers.length > 0 && (
            <span className="ml-1.5 px-1.5 py-0.2 bg-blue-500/20 text-blue-600 dark:text-blue-400 rounded-full text-xs font-semibold">
              {mcpServers.length}
            </span>
          )}
        </button>
        <button
          onClick={() => setActiveTab('prompts')}
          className={cn(
            "px-6 py-3 text-sm font-medium border-b-2 transition-all flex items-center gap-2 shrink-0",
            activeTab === 'prompts' 
              ? "border-primary text-primary" 
              : "border-transparent text-muted-foreground hover:text-foreground"
          )}
        >
          <FileText size={16} />
          System Prompts
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
                          {config.llm_config.model || <span className="text-muted-foreground italic">None</span>}
                        </div>
                      )}
                    </div>

                    {/* Base URL */}
                    <div className="space-y-2">
                      <label className="text-sm font-medium text-muted-foreground">Base URL</label>
                      {editingAgent === config.agent_name ? (
                        <input
                          type="text"
                          value={editForm?.llm_config.base_url || ''}
                          onChange={(e) => updateFormField('llm_config.base_url', e.target.value)}
                          className="w-full bg-background border border-input rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-primary outline-none transition-all"
                          placeholder="Optional"
                        />
                      ) : (
                        <div className="px-3 py-2 bg-muted/30 rounded-lg text-sm border border-transparent truncate">
                          {config.llm_config.base_url || <span className="text-muted-foreground italic">Default</span>}
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
        ) : activeTab === 'custom_agents' ? (
          <div className="max-w-4xl mx-auto space-y-6">
            {/* Header banner */}
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-2 border-b border-border/50">
              <div>
                <h2 className="text-xl font-semibold flex items-center gap-2">
                  <Bot size={22} className="text-primary" />
                  User-Created Custom Agents
                </h2>
                <p className="text-xs text-muted-foreground mt-0.5">
                  Design and manage your own custom agents with specialized LLMs, MCP servers, and Skills.
                </p>
              </div>
              <button
                type="button"
                onClick={handleOpenCreateModal}
                className="inline-flex items-center gap-2 px-4 py-2 bg-primary text-primary-foreground text-sm font-medium rounded-lg hover:bg-primary/90 transition-all shadow-sm active:scale-95 shrink-0"
              >
                <Plus size={16} />
                Create Agent
              </button>
            </div>

            {/* Custom Agents List */}
            {loadingCustomAgents ? (
              <div className="flex justify-center py-12">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
              </div>
            ) : customAgents.length === 0 ? (
              <div className="text-center py-16 px-6 bg-muted/20 rounded-2xl border border-dashed border-border flex flex-col items-center">
                <div className="w-14 h-14 rounded-2xl bg-primary/10 text-primary flex items-center justify-center mb-4">
                  <Bot size={28} />
                </div>
                <h3 className="text-base font-semibold text-foreground">No Custom Agents Created Yet</h3>
                <p className="text-xs text-muted-foreground max-w-md mt-1 mb-6">
                  Build custom agents tailored to your workflow by assigning them a dedicated LLM and connecting MCP tools, Skills, or both.
                </p>
                <button
                  type="button"
                  onClick={handleOpenCreateModal}
                  className="inline-flex items-center gap-2 px-4 py-2 bg-primary text-primary-foreground text-sm font-medium rounded-lg hover:bg-primary/90 transition-all shadow-sm"
                >
                  <Plus size={16} />
                  Create First Agent
                </button>
              </div>
            ) : (
              <div className="grid gap-4">
                {customAgents.map(agent => {
                  const hasMcp = agent.mcp_servers && agent.mcp_servers.length > 0;
                  const hasSkill = agent.skills && agent.skills.length > 0;

                  return (
                    <div
                      key={agent.id}
                      className={cn(
                        "bg-card border rounded-xl p-5 transition-all shadow-sm flex flex-col gap-4",
                        agent.is_active ? "border-border hover:border-primary/50" : "border-border/60 opacity-80 bg-muted/10"
                      )}
                    >
                      {/* Top row */}
                      <div className="flex items-start justify-between gap-4">
                        <div className="space-y-1">
                          <div className="flex items-center gap-2.5 flex-wrap">
                            <span className="text-base font-semibold text-foreground">{agent.name}</span>
                            <span className={cn(
                              "px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wider rounded-full",
                              agent.is_active 
                                ? "bg-emerald-500/15 text-emerald-600 dark:text-emerald-400 border border-emerald-500/20" 
                                : "bg-muted text-muted-foreground border border-border"
                            )}>
                              {agent.is_active ? 'Active' : 'Inactive'}
                            </span>
                            
                            {hasMcp && hasSkill ? (
                              <span className="px-2 py-0.5 text-[10px] font-semibold rounded-full bg-indigo-500/10 text-indigo-500 border border-indigo-500/20">
                                Dual: MCP + Skill
                              </span>
                            ) : hasMcp ? (
                              <span className="px-2 py-0.5 text-[10px] font-semibold rounded-full bg-blue-500/10 text-blue-500 border border-blue-500/20">
                                MCP Enabled
                              </span>
                            ) : (
                              <span className="px-2 py-0.5 text-[10px] font-semibold rounded-full bg-purple-500/10 text-purple-500 border border-purple-500/20">
                                Skill Enabled
                              </span>
                            )}
                          </div>

                          {agent.description ? (
                            <p className="text-xs text-muted-foreground leading-relaxed">
                              {agent.description}
                            </p>
                          ) : (
                            <p className="text-xs text-muted-foreground italic">No description provided</p>
                          )}
                        </div>

                        {/* Actions */}
                        <div className="flex items-center gap-1 shrink-0">
                          <button
                            type="button"
                            onClick={() => handleToggleAgentActive(agent)}
                            className={cn(
                              "px-2.5 py-1 rounded-md text-xs font-medium transition-colors border flex items-center gap-1.5 mr-1",
                              agent.is_active 
                                ? "bg-emerald-500/10 border-emerald-500/30 text-emerald-600 hover:bg-emerald-500/20" 
                                : "bg-muted border-border text-muted-foreground hover:text-foreground"
                            )}
                            title={agent.is_active ? "Click to deactivate" : "Click to activate"}
                          >
                            <span className={cn("w-1.5 h-1.5 rounded-full", agent.is_active ? "bg-emerald-500 animate-pulse" : "bg-zinc-400")} />
                            <span>{agent.is_active ? 'Enabled' : 'Disabled'}</span>
                          </button>

                          <button
                            type="button"
                            onClick={() => handleOpenEditModal(agent)}
                            className="p-1.5 hover:bg-muted text-muted-foreground hover:text-foreground rounded-lg transition-colors"
                            title="Edit Agent"
                            aria-label={`Edit ${agent.name}`}
                          >
                            <Edit2 size={16} />
                          </button>
                          <button
                            type="button"
                            onClick={() => handleDeleteCustomAgent(agent)}
                            className="p-1.5 hover:bg-destructive/10 text-muted-foreground hover:text-destructive rounded-lg transition-colors"
                            title="Delete Agent"
                            aria-label={`Delete ${agent.name}`}
                          >
                            <Trash2 size={16} />
                          </button>
                        </div>
                      </div>

                      {/* Capabilities and Specs Row */}
                      <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 pt-3 border-t border-border/50 text-xs">
                        {/* LLM Spec */}
                        <div className="flex items-center gap-2 p-2 bg-muted/30 rounded-lg">
                          <Cpu size={15} className="text-primary shrink-0" />
                          <div className="min-w-0">
                            <span className="text-[10px] text-muted-foreground block uppercase font-mono">LLM</span>
                            <span className="font-medium text-foreground truncate block">
                              {agent.llm_provider.toUpperCase()} • {agent.model_name}
                            </span>
                          </div>
                        </div>

                        {/* MCP Servers */}
                        <div className="flex items-start gap-2 p-2 bg-muted/30 rounded-lg sm:col-span-1">
                          <Server size={15} className="text-blue-500 shrink-0 mt-0.5" />
                          <div className="min-w-0 flex-1">
                            <span className="text-[10px] text-muted-foreground block uppercase font-mono">
                              MCP Servers ({agent.mcp_servers?.length || 0})
                            </span>
                            {hasMcp ? (
                              <div className="flex flex-wrap gap-1 mt-1">
                                {agent.mcp_servers.map((mcp, idx) => (
                                  <span key={idx} className="px-1.5 py-0.5 bg-blue-500/10 text-blue-600 dark:text-blue-400 rounded text-[11px] font-mono">
                                    {mcp}
                                  </span>
                                ))}
                              </div>
                            ) : (
                              <span className="text-muted-foreground italic text-[11px]">None assigned</span>
                            )}
                          </div>
                        </div>

                        {/* Skills */}
                        <div className="flex items-start gap-2 p-2 bg-muted/30 rounded-lg sm:col-span-1">
                          <Wrench size={15} className="text-purple-500 shrink-0 mt-0.5" />
                          <div className="min-w-0 flex-1">
                            <span className="text-[10px] text-muted-foreground block uppercase font-mono">
                              Skills ({agent.skills?.length || 0})
                            </span>
                            {hasSkill ? (
                              <div className="flex flex-wrap gap-1 mt-1">
                                {agent.skills.map((s, idx) => (
                                  <span key={idx} className="px-1.5 py-0.5 bg-purple-500/10 text-purple-600 dark:text-purple-400 rounded text-[11px] font-mono">
                                    {s}
                                  </span>
                                ))}
                              </div>
                            ) : (
                              <span className="text-muted-foreground italic text-[11px]">None assigned</span>
                            )}
                          </div>
                        </div>
                      </div>

                      {/* System Prompt preview if available */}
                      {agent.system_prompt && (
                        <div className="bg-muted/20 rounded-lg p-2.5 border border-border/30 text-[11px] font-mono text-muted-foreground truncate">
                          <span className="font-semibold text-foreground/70 mr-1.5 uppercase tracking-wider text-[10px]">Prompt:</span>
                          {agent.system_prompt}
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
            )}
          </div>
        ) : activeTab === 'mcp_servers' ? (
          <div className="max-w-4xl mx-auto space-y-8">
            {/* Header banner */}
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-2 border-b border-border/50">
              <div>
                <h2 className="text-xl font-semibold flex items-center gap-2">
                  <Server size={22} className="text-primary" />
                  Model Context Protocol (MCP) Server Registry
                </h2>
                <p className="text-xs text-muted-foreground mt-0.5">
                  Configure and manage shared MCP servers. Any agent can be connected to these servers without running separate instances.
                </p>
              </div>
              <button
                type="button"
                onClick={() => handleOpenCreateMcpModal()}
                className="inline-flex items-center gap-2 px-4 py-2 bg-primary text-primary-foreground text-sm font-medium rounded-lg hover:bg-primary/90 transition-all shadow-sm active:scale-95 shrink-0"
              >
                <Plus size={16} />
                Register MCP Server
              </button>
            </div>

            {/* Zero-Config 1-Click OAuth MCP Hub (Claude Style) */}
            <div className="space-y-3.5 p-4 rounded-2xl bg-card border border-border shadow-sm">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                <div>
                  <h3 className="text-xs font-semibold uppercase tracking-wider text-muted-foreground flex items-center gap-1.5">
                    <ShieldCheck size={15} className="text-emerald-500" />
                    Zero-Config OAuth Integrations (Claude-Style)
                  </h3>
                  <p className="text-[11px] text-muted-foreground mt-0.5">
                    Connect accounts via browser OAuth without client IDs or API keys. Tokens are stored in <code className="font-mono text-[10px] bg-muted px-1.5 py-0.5 rounded text-foreground/80">~/.openagents/credentials/oauth_tokens.json</code> and auto-injected.
                  </p>
                </div>
                <button
                  type="button"
                  onClick={fetchOAuthProviders}
                  disabled={loadingOAuth}
                  className="px-2.5 py-1 text-xs border border-border/80 bg-muted/40 hover:bg-muted text-muted-foreground hover:text-foreground rounded-lg transition-colors flex items-center gap-1.5 self-start sm:self-auto shrink-0"
                >
                  <RefreshCw size={12} className={loadingOAuth ? "animate-spin" : ""} />
                  <span>Refresh Status</span>
                </button>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 pt-1">
                {oauthProviders.map((provider) => {
                  return (
                    <div
                      key={provider.id}
                      className={cn(
                        "p-3.5 rounded-xl border transition-all flex flex-col justify-between gap-3 text-left",
                        provider.connected 
                          ? "bg-emerald-500/[0.04] border-emerald-500/30" 
                          : "bg-muted/20 border-border hover:border-primary/40"
                      )}
                    >
                      <div className="space-y-1.5">
                        <div className="flex items-center justify-between gap-2">
                          <span className="font-semibold text-xs text-foreground flex items-center gap-1.5">
                            {provider.id === 'github' ? (
                              <Terminal size={14} className="text-muted-foreground" />
                            ) : provider.id === 'google' ? (
                              <Globe size={14} className="text-blue-500" />
                            ) : (
                              <Key size={14} className="text-purple-500" />
                            )}
                            {provider.name}
                          </span>
                          <span className={cn(
                            "text-[10px] px-1.5 py-0.2 rounded-full font-semibold uppercase tracking-wider",
                            provider.connected 
                              ? "bg-emerald-500/15 text-emerald-600 dark:text-emerald-400 border border-emerald-500/30" 
                              : "bg-muted text-muted-foreground"
                          )}>
                            {provider.connected ? "Connected" : "Not Linked"}
                          </span>
                        </div>
                        <p className="text-[11px] text-muted-foreground line-clamp-2 leading-relaxed">
                          {provider.description}
                        </p>
                      </div>

                      <div className="pt-2 border-t border-border/40 flex items-center justify-between gap-2">
                        {provider.connected ? (
                          <>
                            <div className="min-w-0 flex-1 flex items-center gap-1.5 text-xs text-emerald-600 dark:text-emerald-400 font-medium truncate">
                              <CheckCircle2 size={13} className="shrink-0" />
                              <span className="truncate">{provider.user || "Active"}</span>
                            </div>
                            <button
                              type="button"
                              onClick={() => handleDisconnectOAuth(provider.id)}
                              className="px-2 py-1 text-[11px] text-destructive hover:bg-destructive/10 rounded transition-colors shrink-0"
                              title="Disconnect account"
                            >
                              Disconnect
                            </button>
                          </>
                        ) : (
                          <>
                            <span className="text-[10px] text-muted-foreground flex items-center gap-1">
                              <Lock size={11} className="text-muted-foreground/70" />
                              Zero-token setup
                            </span>
                            <button
                              type="button"
                              onClick={() => handleConnectOAuth(provider.id)}
                              className="px-2.5 py-1 text-xs font-medium rounded-lg bg-primary text-primary-foreground hover:bg-primary/90 transition-all shadow-sm active:scale-95 flex items-center gap-1 shrink-0"
                            >
                              <span>Connect</span>
                              <ExternalLink size={11} />
                            </button>
                          </>
                        )}
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>

            {/* Popular Presets Quick-Add Section */}
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <h3 className="text-xs font-semibold uppercase tracking-wider text-muted-foreground flex items-center gap-1.5">
                  <Sparkles size={14} className="text-primary" />
                  Quick-Add Popular Presets
                </h3>
                <span className="text-[11px] text-muted-foreground">Click any preset to prefill and configure</span>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-3">
                {mcpPresets.map((preset) => {
                  const alreadyRegistered = mcpServers.some(s => s.name.toLowerCase() === preset.name.toLowerCase());

                  return (
                    <div
                      key={preset.id}
                      className={cn(
                        "p-3.5 rounded-xl border bg-card/60 transition-all flex flex-col justify-between gap-3 text-left group",
                        alreadyRegistered ? "border-border/60 opacity-80" : "border-border hover:border-primary/50 hover:shadow-sm"
                      )}
                    >
                      <div>
                        <div className="flex items-center justify-between gap-2 mb-1">
                          <span className="font-semibold text-xs text-foreground">{preset.name}</span>
                          <span className="text-[10px] font-mono px-1.5 py-0.2 rounded bg-muted text-muted-foreground uppercase">
                            {preset.type}
                          </span>
                        </div>
                        <p className="text-[11px] text-muted-foreground line-clamp-2 leading-relaxed">
                          {preset.description}
                        </p>
                      </div>

                      <div className="pt-2 border-t border-border/40 flex items-center justify-between">
                        {preset.oauth_connected ? (
                          <span className="text-[10px] text-emerald-600 dark:text-emerald-400 font-medium flex items-center gap-1" title="OAuth token auto-injected">
                            <ShieldCheck size={12} />
                            OAuth Active
                          </span>
                        ) : alreadyRegistered ? (
                          <span className="text-[10px] text-emerald-600 dark:text-emerald-400 font-medium flex items-center gap-1">
                            <Check size={12} />
                            Registered
                          </span>
                        ) : (
                          <span className="text-[10px] text-muted-foreground font-mono">
                            {preset.command || 'sse'}
                          </span>
                        )}

                        <button
                          type="button"
                          onClick={() => handleOpenCreateMcpModal(preset)}
                          className={cn(
                            "px-2.5 py-1 text-xs font-medium rounded-md transition-all flex items-center gap-1",
                            alreadyRegistered 
                              ? "bg-muted text-muted-foreground hover:text-foreground" 
                              : "bg-primary/10 text-primary hover:bg-primary hover:text-primary-foreground"
                          )}
                        >
                          <Plus size={12} />
                          {alreadyRegistered ? 'Configure' : 'Add'}
                        </button>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>

            {/* Registered Servers List */}
            <div className="space-y-3 pt-2">
              <div className="flex items-center justify-between">
                <h3 className="text-xs font-semibold uppercase tracking-wider text-muted-foreground flex items-center gap-1.5">
                  <Database size={14} className="text-primary" />
                  Active Registered MCP Servers ({mcpServers.length})
                </h3>
              </div>

              {loadingMcpServers ? (
                <div className="flex justify-center py-12">
                  <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
                </div>
              ) : mcpServers.length === 0 ? (
                <div className="text-center py-14 px-6 bg-muted/20 rounded-2xl border border-dashed border-border flex flex-col items-center">
                  <div className="w-12 h-12 rounded-2xl bg-blue-500/10 text-blue-500 flex items-center justify-center mb-3">
                    <Server size={24} />
                  </div>
                  <h4 className="text-sm font-semibold text-foreground">No MCP Servers Registered Yet</h4>
                  <p className="text-xs text-muted-foreground max-w-sm mt-1 mb-5">
                    Register an MCP server above (or choose a quick preset) to make its tools available to all your custom agents.
                  </p>
                  <button
                    type="button"
                    onClick={() => handleOpenCreateMcpModal()}
                    className="inline-flex items-center gap-2 px-4 py-2 bg-primary text-primary-foreground text-xs font-medium rounded-lg hover:bg-primary/90 transition-all shadow-sm"
                  >
                    <Plus size={14} />
                    Register Custom Server
                  </button>
                </div>
              ) : (
                <div className="grid gap-3.5">
                  {mcpServers.map((server) => {
                    const isStdio = server.type === 'stdio';
                    const envKeys = Object.keys(server.env || {});

                    return (
                      <div
                        key={server.id}
                        className="bg-card border border-border rounded-xl p-4 transition-all shadow-sm hover:border-primary/40 space-y-3"
                      >
                        <div className="flex items-start justify-between gap-4">
                          <div className="space-y-1">
                            <div className="flex items-center gap-2">
                              <span className="font-semibold text-sm text-foreground">{server.name}</span>
                              <span className={cn(
                                "px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wider rounded-full",
                                isStdio 
                                  ? "bg-blue-500/10 text-blue-600 dark:text-blue-400 border border-blue-500/20" 
                                  : "bg-purple-500/10 text-purple-600 dark:text-purple-400 border border-purple-500/20"
                              )}>
                                {server.type}
                              </span>
                            </div>
                          </div>

                          <div className="flex items-center gap-1 shrink-0">
                            <button
                              type="button"
                              onClick={() => handleOpenEditMcpModal(server)}
                              className="p-1.5 hover:bg-muted text-muted-foreground hover:text-foreground rounded-lg transition-colors"
                              title="Edit Server"
                              aria-label={`Edit ${server.name}`}
                            >
                              <Edit2 size={16} />
                            </button>
                            <button
                              type="button"
                              onClick={() => handleDeleteMcpServer(server)}
                              className="p-1.5 hover:bg-destructive/10 text-muted-foreground hover:text-destructive rounded-lg transition-colors"
                              title="Delete Server"
                              aria-label={`Delete ${server.name}`}
                            >
                              <Trash2 size={16} />
                            </button>
                          </div>
                        </div>

                        {/* Connection Details */}
                        <div className="bg-muted/30 p-2.5 rounded-lg border border-border/40 space-y-1.5 text-xs font-mono">
                          {isStdio ? (
                            <div className="flex items-start gap-2">
                              <Terminal size={14} className="text-muted-foreground shrink-0 mt-0.5" />
                              <div className="break-all text-muted-foreground leading-normal">
                                <span className="text-foreground font-semibold mr-1.5">{server.command}</span>
                                {(server.args || []).join(' ')}
                              </div>
                            </div>
                          ) : (
                            <div className="flex items-center gap-2">
                              <Globe size={14} className="text-purple-500 shrink-0" />
                              <span className="text-foreground break-all">{server.url}</span>
                            </div>
                          )}

                          {envKeys.length > 0 && (
                            <div className="flex items-center gap-2 pt-1 border-t border-border/30 text-[11px] text-muted-foreground">
                              <Key size={12} className="text-amber-500 shrink-0" />
                              <span>Environment Variables:</span>
                              <div className="flex flex-wrap gap-1">
                                {envKeys.map(k => (
                                  <span key={k} className="px-1.5 py-0.2 bg-muted rounded font-mono text-[10px]">
                                    {k}=••••
                                  </span>
                                ))}
                              </div>
                            </div>
                          )}
                        </div>
                      </div>
                    );
                  })}
                </div>
              )}
            </div>
          </div>
        ) : (
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
        )}
      </div>

      {/* Create / Edit Custom Agent Modal */}
      {isModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-background/80 backdrop-blur-md animate-fade-in">
          <div className="bg-card border border-border w-full max-w-2xl rounded-2xl shadow-2xl overflow-hidden flex flex-col max-h-[90vh] animate-scale-in">
            {/* Modal Header */}
            <div className="px-6 py-4 border-b border-border flex items-center justify-between shrink-0 bg-muted/20">
              <div className="flex items-center gap-2.5">
                <div className="w-8 h-8 rounded-lg bg-primary/10 text-primary flex items-center justify-center">
                  <Bot size={18} />
                </div>
                <div>
                  <h3 className="font-semibold text-base">
                    {editingCustomAgentId ? `Edit Agent: ${agentForm.name}` : 'Create Custom Agent'}
                  </h3>
                  <p className="text-xs text-muted-foreground">
                    Define name, routing LLM, and assign MCP servers or Skills.
                  </p>
                </div>
              </div>
              <button
                type="button"
                onClick={() => setIsModalOpen(false)}
                className="p-1.5 rounded-lg hover:bg-muted text-muted-foreground hover:text-foreground transition-colors"
                aria-label="Close modal"
              >
                <X size={18} />
              </button>
            </div>

            {/* Modal Body */}
            <div className="p-6 space-y-5 overflow-y-auto custom-scrollbar flex-1">
              {/* Name & Active toggle */}
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                <div className="sm:col-span-2 space-y-1.5">
                  <label className="text-xs font-semibold text-foreground flex items-center gap-1">
                    Agent Name <span className="text-destructive">*</span>
                  </label>
                  <input
                    type="text"
                    value={agentForm.name}
                    onChange={(e) => setAgentForm({ ...agentForm, name: e.target.value })}
                    className="w-full bg-background border border-input rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-primary outline-none transition-all"
                    placeholder="e.g. DocumentationWriter, SqlOptimizer"
                  />
                </div>

                <div className="space-y-1.5">
                  <label className="text-xs font-semibold text-foreground block">
                    Status
                  </label>
                  <button
                    type="button"
                    onClick={() => setAgentForm({ ...agentForm, is_active: !agentForm.is_active })}
                    className={cn(
                      "w-full flex items-center justify-between px-3 py-2 rounded-lg border text-xs font-medium transition-all",
                      agentForm.is_active 
                        ? "bg-emerald-500/10 border-emerald-500/30 text-emerald-600 dark:text-emerald-400" 
                        : "bg-muted border-border text-muted-foreground"
                    )}
                  >
                    <span>{agentForm.is_active ? 'Active' : 'Inactive'}</span>
                    <span className={cn(
                      "w-2 h-2 rounded-full",
                      agentForm.is_active ? "bg-emerald-500" : "bg-zinc-400"
                    )} />
                  </button>
                </div>
              </div>

              {/* Description */}
              <div className="space-y-1.5">
                <label className="text-xs font-semibold text-foreground">
                  Description / Role
                </label>
                <input
                  type="text"
                  value={agentForm.description}
                  onChange={(e) => setAgentForm({ ...agentForm, description: e.target.value })}
                  className="w-full bg-background border border-input rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-primary outline-none transition-all"
                  placeholder="Explain what this agent does and its area of expertise..."
                />
              </div>

              {/* LLM Configuration */}
              <div className="space-y-2 pt-2 border-t border-border/50">
                <h4 className="text-xs font-semibold uppercase tracking-wider text-muted-foreground flex items-center gap-1.5">
                  <Cpu size={14} className="text-primary" />
                  LLM Model Configuration
                </h4>
                
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  <div className="space-y-1.5">
                    <label className="text-xs font-medium text-muted-foreground">Provider</label>
                    <select
                      value={agentForm.llm_provider.toUpperCase()}
                      onChange={(e) => setAgentForm({ ...agentForm, llm_provider: e.target.value })}
                      className="w-full bg-background border border-input rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-primary outline-none transition-all"
                    >
                      {PROVIDERS.filter(p => p !== 'NONE').map(p => (
                        <option key={p} value={p}>{p}</option>
                      ))}
                    </select>
                  </div>

                  <div className="space-y-1.5">
                    <label className="text-xs font-medium text-muted-foreground">Model Name</label>
                    <input
                      type="text"
                      value={agentForm.model_name}
                      onChange={(e) => setAgentForm({ ...agentForm, model_name: e.target.value })}
                      className="w-full bg-background border border-input rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-primary outline-none transition-all font-mono"
                      placeholder="e.g. llama3.1, gpt-4o"
                    />
                  </div>
                </div>

                {/* Quick Model presets */}
                <div className="flex items-center gap-1.5 flex-wrap pt-1">
                  <span className="text-[11px] text-muted-foreground">Quick select:</span>
                  {COMMON_MODELS.map(m => (
                    <button
                      key={m}
                      type="button"
                      onClick={() => setAgentForm({ ...agentForm, model_name: m })}
                      className={cn(
                        "px-2 py-0.5 rounded text-[11px] font-mono transition-colors",
                        agentForm.model_name === m 
                          ? "bg-primary text-primary-foreground font-semibold" 
                          : "bg-muted/60 text-muted-foreground hover:bg-muted hover:text-foreground"
                      )}
                    >
                      {m}
                    </button>
                  ))}
                </div>
              </div>

              {/* Capabilities Requirement Box */}
              <div className="space-y-4 pt-2 border-t border-border/50">
                <div className="flex items-center justify-between">
                  <h4 className="text-xs font-semibold uppercase tracking-wider text-muted-foreground flex items-center gap-1.5">
                    <Sparkles size={14} className="text-primary" />
                    Agent Capabilities (MCP or Skill or Both)
                  </h4>

                  {isCapabilitiesValid ? (
                    <span className="inline-flex items-center gap-1 text-[11px] font-medium text-emerald-600 dark:text-emerald-400 bg-emerald-500/10 px-2 py-0.5 rounded-full">
                      <Check size={12} />
                      {hasSelectedMcp && hasSelectedSkill 
                        ? 'MCP + Skill Selected' 
                        : hasSelectedMcp 
                          ? 'MCP Selected' 
                          : 'Skill Selected'}
                    </span>
                  ) : (
                    <span className="inline-flex items-center gap-1 text-[11px] font-medium text-amber-600 dark:text-amber-400 bg-amber-500/10 px-2 py-0.5 rounded-full animate-pulse">
                      <AlertCircle size={12} />
                      At least one required
                    </span>
                  )}
                </div>

                {/* MCP Servers Selection */}
                <div className="p-3.5 bg-muted/20 border border-border/60 rounded-xl space-y-2.5">
                  <div className="flex items-center justify-between">
                    <label className="text-xs font-semibold text-foreground flex items-center gap-1.5">
                      <Server size={14} className="text-blue-500" />
                      Assign MCP Servers
                    </label>
                    <span className="text-[11px] text-muted-foreground font-mono">
                      Selected: {agentForm.mcp_servers.length}
                    </span>
                  </div>

                  {/* Available MCP Chips */}
                  <div className="flex flex-wrap gap-1.5">
                    {availableOptions.mcp_servers.map((mcp) => {
                      const isSelected = agentForm.mcp_servers.includes(mcp.name);
                      return (
                        <button
                          key={mcp.name}
                          type="button"
                          onClick={() => handleToggleMcp(mcp.name)}
                          className={cn(
                            "px-2.5 py-1 rounded-md text-xs font-medium transition-all flex items-center gap-1.5 border",
                            isSelected
                              ? "bg-blue-500/20 text-blue-700 dark:text-blue-300 border-blue-500/40 font-semibold"
                              : "bg-background text-muted-foreground border-border hover:border-border/80 hover:text-foreground"
                          )}
                          title={mcp.description || mcp.name}
                        >
                          {isSelected && <Check size={12} />}
                          <span>{mcp.name}</span>
                        </button>
                      );
                    })}
                  </div>

                  {/* Custom MCP input */}
                  <div className="flex items-center gap-2 pt-1">
                    <input
                      type="text"
                      value={customMcpInput}
                      onChange={(e) => setCustomMcpInput(e.target.value)}
                      onKeyDown={(e) => {
                        if (e.key === 'Enter') {
                          e.preventDefault();
                          handleAddCustomMcp();
                        }
                      }}
                      placeholder="Add custom MCP server name..."
                      className="flex-1 bg-background border border-input rounded-lg px-2.5 py-1 text-xs outline-none focus:ring-1 focus:ring-primary"
                    />
                    <button
                      type="button"
                      onClick={handleAddCustomMcp}
                      disabled={!customMcpInput.trim()}
                      className="px-2.5 py-1 bg-muted hover:bg-muted/80 text-foreground text-xs rounded-lg border border-border disabled:opacity-50"
                    >
                      + Add
                    </button>
                  </div>
                </div>

                {/* Skills Selection */}
                <div className="p-3.5 bg-muted/20 border border-border/60 rounded-xl space-y-2.5">
                  <div className="flex items-center justify-between">
                    <label className="text-xs font-semibold text-foreground flex items-center gap-1.5">
                      <Wrench size={14} className="text-purple-500" />
                      Assign Skills
                    </label>
                    <span className="text-[11px] text-muted-foreground font-mono">
                      Selected: {agentForm.skills.length}
                    </span>
                  </div>

                  {/* Available Skills Chips */}
                  <div className="flex flex-wrap gap-1.5">
                    {availableOptions.skills.map((skill) => {
                      const isSelected = agentForm.skills.includes(skill.name);
                      return (
                        <button
                          key={skill.id}
                          type="button"
                          onClick={() => handleToggleSkill(skill.name)}
                          className={cn(
                            "px-2.5 py-1 rounded-md text-xs font-medium transition-all flex items-center gap-1.5 border",
                            isSelected
                              ? "bg-purple-500/20 text-purple-700 dark:text-purple-300 border-purple-500/40 font-semibold"
                              : "bg-background text-muted-foreground border-border hover:border-border/80 hover:text-foreground"
                          )}
                          title={skill.description || skill.name}
                        >
                          {isSelected && <Check size={12} />}
                          <span>{skill.name}</span>
                        </button>
                      );
                    })}
                  </div>

                  {/* Custom Skill input */}
                  <div className="flex items-center gap-2 pt-1">
                    <input
                      type="text"
                      value={customSkillInput}
                      onChange={(e) => setCustomSkillInput(e.target.value)}
                      onKeyDown={(e) => {
                        if (e.key === 'Enter') {
                          e.preventDefault();
                          handleAddCustomSkill();
                        }
                      }}
                      placeholder="Add custom skill name..."
                      className="flex-1 bg-background border border-input rounded-lg px-2.5 py-1 text-xs outline-none focus:ring-1 focus:ring-primary"
                    />
                    <button
                      type="button"
                      onClick={handleAddCustomSkill}
                      disabled={!customSkillInput.trim()}
                      className="px-2.5 py-1 bg-muted hover:bg-muted/80 text-foreground text-xs rounded-lg border border-border disabled:opacity-50"
                    >
                      + Add
                    </button>
                  </div>
                </div>
              </div>

              {/* System Prompt */}
              <div className="space-y-1.5 pt-2 border-t border-border/50">
                <label className="text-xs font-semibold text-foreground flex items-center justify-between">
                  <span>Custom System Prompt / Instructions</span>
                  <span className="text-[10px] text-muted-foreground font-normal">Optional</span>
                </label>
                <textarea
                  value={agentForm.system_prompt}
                  onChange={(e) => setAgentForm({ ...agentForm, system_prompt: e.target.value })}
                  rows={4}
                  className="w-full bg-background border border-input rounded-lg px-3 py-2 text-xs font-mono leading-relaxed focus:ring-2 focus:ring-primary outline-none transition-all custom-scrollbar"
                  placeholder="Define base instructions, constraints, and behavior for this agent..."
                />
              </div>
            </div>

            {/* Modal Footer */}
            <div className="px-6 py-3.5 border-t border-border bg-muted/20 flex items-center justify-between shrink-0">
              <div className="text-xs">
                {!isCapabilitiesValid && (
                  <span className="text-amber-500 flex items-center gap-1 font-medium">
                    <AlertCircle size={13} />
                    Select at least 1 MCP or Skill to save.
                  </span>
                )}
              </div>

              <div className="flex items-center gap-2">
                <button
                  type="button"
                  onClick={() => setIsModalOpen(false)}
                  className="px-4 py-2 rounded-lg text-xs font-medium hover:bg-muted text-muted-foreground hover:text-foreground transition-colors"
                >
                  Cancel
                </button>
                <button
                  type="button"
                  onClick={handleSaveCustomAgent}
                  disabled={!agentForm.name.trim() || !isCapabilitiesValid}
                  className="px-4 py-2 bg-primary text-primary-foreground text-xs font-medium rounded-lg hover:bg-primary/90 transition-all shadow-sm active:scale-95 disabled:opacity-50 disabled:pointer-events-none flex items-center gap-1.5"
                >
                  <Save size={14} />
                  <span>{editingCustomAgentId ? 'Update Agent' : 'Create Agent'}</span>
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Register / Edit MCP Server Modal */}
      {isMcpModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-background/80 backdrop-blur-md animate-fade-in">
          <div className="bg-card border border-border w-full max-w-2xl rounded-2xl shadow-2xl overflow-hidden flex flex-col max-h-[92vh] animate-scale-in">
            {/* Modal Header */}
            <div className="px-6 py-4 border-b border-border flex items-center justify-between shrink-0 bg-muted/20">
              <div className="flex items-center gap-2.5">
                <div className="w-8 h-8 rounded-lg bg-blue-500/10 text-blue-500 flex items-center justify-center">
                  <Server size={18} />
                </div>
                <div>
                  <h3 className="font-semibold text-base">
                    {editingMcpId ? `Edit MCP Server: ${mcpForm.name}` : 'Register MCP Server'}
                  </h3>
                  <p className="text-xs text-muted-foreground">
                    Connect an external tool via Model Context Protocol (stdio subprocess or SSE).
                  </p>
                </div>
              </div>
              <button
                type="button"
                onClick={() => setIsMcpModalOpen(false)}
                className="p-1.5 rounded-lg hover:bg-muted text-muted-foreground hover:text-foreground transition-colors"
                aria-label="Close modal"
              >
                <X size={18} />
              </button>
            </div>

            {/* Modal Sub-Tabs: Visual Form vs Raw JSON */}
            <div className="flex border-b border-border bg-muted/30 px-6 shrink-0">
              <button
                type="button"
                onClick={() => handleSwitchToTab('form')}
                className={cn(
                  "py-2.5 px-4 text-xs font-semibold border-b-2 transition-all flex items-center gap-1.5",
                  mcpModalTab === 'form'
                    ? "border-primary text-primary"
                    : "border-transparent text-muted-foreground hover:text-foreground"
                )}
              >
                <Layers size={13} />
                Visual Form Builder
              </button>
              <button
                type="button"
                onClick={() => handleSwitchToTab('json')}
                className={cn(
                  "py-2.5 px-4 text-xs font-semibold border-b-2 transition-all flex items-center gap-1.5",
                  mcpModalTab === 'json'
                    ? "border-primary text-primary"
                    : "border-transparent text-muted-foreground hover:text-foreground"
                )}
              >
                <Code size={13} />
                Raw JSON & Direct OAuth Hub
              </button>
            </div>

            {/* Modal Body */}
            {mcpModalTab === 'form' ? (
              <div className="p-6 space-y-4 overflow-y-auto custom-scrollbar flex-1">
                {/* Name & Type */}
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  <div className="space-y-1.5">
                    <label className="text-xs font-semibold text-foreground flex items-center gap-1">
                      Server Name <span className="text-destructive">*</span>
                    </label>
                    <input
                      type="text"
                      value={mcpForm.name}
                      onChange={(e) => setMcpForm({ ...mcpForm, name: e.target.value })}
                      className="w-full bg-background border border-input rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-primary outline-none transition-all"
                      placeholder="e.g. GitHub, Filesystem, Postgres"
                    />
                  </div>

                  <div className="space-y-1.5">
                    <label className="text-xs font-semibold text-foreground">
                      Protocol Transport
                    </label>
                    <div className="grid grid-cols-2 gap-2">
                      <button
                        type="button"
                        onClick={() => setMcpForm({ ...mcpForm, type: 'stdio' })}
                        className={cn(
                          "py-2 px-3 text-xs font-medium rounded-lg border transition-all text-center flex items-center justify-center gap-1.5",
                          mcpForm.type === 'stdio'
                            ? "bg-blue-500/10 border-blue-500/40 text-blue-600 dark:text-blue-400 font-semibold"
                            : "bg-muted/40 border-border text-muted-foreground hover:text-foreground"
                        )}
                      >
                        <Terminal size={13} />
                        stdio
                      </button>
                      <button
                        type="button"
                        onClick={() => setMcpForm({ ...mcpForm, type: 'sse' })}
                        className={cn(
                          "py-2 px-3 text-xs font-medium rounded-lg border transition-all text-center flex items-center justify-center gap-1.5",
                          mcpForm.type === 'sse'
                            ? "bg-purple-500/10 border-purple-500/40 text-purple-600 dark:text-purple-400 font-semibold"
                            : "bg-muted/40 border-border text-muted-foreground hover:text-foreground"
                        )}
                      >
                        <Globe size={13} />
                        SSE / HTTP
                      </button>
                    </div>
                  </div>
                </div>

                {/* stdio options: command & arguments */}
                {mcpForm.type === 'stdio' ? (
                  <div className="space-y-3 p-3.5 bg-muted/20 border border-border/50 rounded-xl">
                    <div className="space-y-1.5">
                      <label className="text-xs font-medium text-foreground flex items-center gap-1">
                        Command <span className="text-destructive">*</span>
                      </label>
                      <input
                        type="text"
                        value={mcpForm.command}
                        onChange={(e) => setMcpForm({ ...mcpForm, command: e.target.value })}
                        className="w-full bg-background border border-input rounded-lg px-3 py-2 text-xs font-mono focus:ring-1 focus:ring-primary outline-none"
                        placeholder="e.g. npx, uvx, python, node, docker"
                      />
                    </div>

                    <div className="space-y-1.5">
                      <label className="text-xs font-medium text-foreground">
                        Command Arguments (space-separated)
                      </label>
                      <input
                        type="text"
                        value={mcpForm.args}
                        onChange={(e) => setMcpForm({ ...mcpForm, args: e.target.value })}
                        className="w-full bg-background border border-input rounded-lg px-3 py-2 text-xs font-mono focus:ring-1 focus:ring-primary outline-none"
                        placeholder="e.g. -y @modelcontextprotocol/server-github"
                      />
                    </div>
                  </div>
                ) : (
                  <div className="space-y-1.5 p-3.5 bg-muted/20 border border-border/50 rounded-xl">
                    <label className="text-xs font-medium text-foreground flex items-center gap-1">
                      Server SSE URL <span className="text-destructive">*</span>
                    </label>
                    <input
                      type="text"
                      value={mcpForm.url}
                      onChange={(e) => setMcpForm({ ...mcpForm, url: e.target.value })}
                      className="w-full bg-background border border-input rounded-lg px-3 py-2 text-xs font-mono focus:ring-1 focus:ring-primary outline-none"
                      placeholder="e.g. http://localhost:3000/sse"
                    />
                  </div>
                )}

                {/* Environment Variables */}
                <div className="space-y-2 pt-2 border-t border-border/50">
                  <div className="flex items-center justify-between">
                    <label className="text-xs font-semibold text-foreground flex items-center gap-1.5">
                      <Key size={13} className="text-amber-500" />
                      Environment Variables (API Keys & Tokens)
                    </label>
                    <button
                      type="button"
                      onClick={handleAddEnvRow}
                      className="text-xs text-primary hover:underline font-medium flex items-center gap-1"
                    >
                      <Plus size={12} />
                      Add Variable
                    </button>
                  </div>

                  {mcpForm.env.length === 0 ? (
                    <p className="text-xs text-muted-foreground italic bg-muted/20 p-2.5 rounded-lg border border-border/30">
                      No environment variables configured.
                    </p>
                  ) : (
                    <div className="space-y-2 max-h-40 overflow-y-auto custom-scrollbar">
                      {mcpForm.env.map((row, idx) => (
                        <div key={idx} className="flex items-center gap-2">
                          <input
                            type="text"
                            value={row.key}
                            onChange={(e) => handleUpdateEnvRow(idx, 'key', e.target.value)}
                            placeholder="VARIABLE_NAME"
                            className="w-1/2 bg-background border border-input rounded-lg px-2.5 py-1.5 text-xs font-mono outline-none focus:ring-1 focus:ring-primary uppercase"
                          />
                          <input
                            type="password"
                            value={row.value}
                            onChange={(e) => handleUpdateEnvRow(idx, 'value', e.target.value)}
                            placeholder="value / secret token"
                            className="w-1/2 bg-background border border-input rounded-lg px-2.5 py-1.5 text-xs font-mono outline-none focus:ring-1 focus:ring-primary"
                          />
                          <button
                            type="button"
                            onClick={() => handleRemoveEnvRow(idx)}
                            className="p-1.5 hover:bg-destructive/10 text-muted-foreground hover:text-destructive rounded transition-colors"
                            title="Remove variable"
                          >
                            <Trash2 size={13} />
                          </button>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            ) : (
              /* Raw JSON & Direct OAuth Hub Panel */
              <div className="p-6 space-y-4 overflow-y-auto custom-scrollbar flex-1">
                {/* Templates toolbar */}
                <div className="space-y-2">
                  <div className="flex items-center justify-between">
                    <label className="text-xs font-semibold text-foreground flex items-center gap-1.5">
                      <FileJson size={14} className="text-primary" />
                      Paste / Dump Raw MCP Configuration JSON
                    </label>
                    <div className="flex items-center gap-1 text-[11px]">
                      {rawJsonError ? (
                        <span className="text-destructive font-medium flex items-center gap-1">
                          <AlertCircle size={12} />
                          Invalid JSON
                        </span>
                      ) : (
                        <span className="text-emerald-500 font-medium flex items-center gap-1">
                          <CheckCircle2 size={12} />
                          Valid JSON
                        </span>
                      )}
                    </div>
                  </div>

                  <div className="flex flex-wrap items-center gap-1.5 pt-0.5">
                    <span className="text-[10px] text-muted-foreground font-medium uppercase tracking-wider mr-1">
                      Quick Templates:
                    </span>
                    <button
                      type="button"
                      onClick={() => handleLoadRawJsonTemplate('github')}
                      className="px-2 py-0.5 rounded bg-muted/60 hover:bg-muted text-[11px] font-mono border border-border/60 transition-colors"
                    >
                      + GitHub
                    </button>
                    <button
                      type="button"
                      onClick={() => handleLoadRawJsonTemplate('googledrive')}
                      className="px-2 py-0.5 rounded bg-muted/60 hover:bg-muted text-[11px] font-mono border border-border/60 transition-colors"
                    >
                      + Google Drive
                    </button>
                    <button
                      type="button"
                      onClick={() => handleLoadRawJsonTemplate('slack')}
                      className="px-2 py-0.5 rounded bg-muted/60 hover:bg-muted text-[11px] font-mono border border-border/60 transition-colors"
                    >
                      + Slack
                    </button>
                    <button
                      type="button"
                      onClick={() => handleLoadRawJsonTemplate('custom_sse')}
                      className="px-2 py-0.5 rounded bg-purple-500/10 text-purple-600 dark:text-purple-400 hover:bg-purple-500/20 text-[11px] font-mono border border-purple-500/20 transition-colors"
                    >
                      + Remote SSE w/ OAuth
                    </button>
                    <button
                      type="button"
                      onClick={() => handleLoadRawJsonTemplate('claude_desktop')}
                      className="px-2 py-0.5 rounded bg-muted/60 hover:bg-muted text-[11px] font-mono border border-border/60 transition-colors"
                    >
                      + Claude Desktop Format
                    </button>
                  </div>
                </div>

                {/* Monospaced Editor */}
                <div className="space-y-1.5">
                  <textarea
                    value={rawJsonInput}
                    onChange={(e) => {
                      setRawJsonInput(e.target.value);
                      syncRawJsonToForm(e.target.value);
                    }}
                    rows={10}
                    className="w-full bg-background border border-input rounded-xl p-3.5 text-xs font-mono outline-none focus:ring-2 focus:ring-primary leading-relaxed resize-y custom-scrollbar"
                    placeholder={`{\n  "name": "My-MCP-Server",\n  "type": "stdio",\n  "command": "npx",\n  "args": ["-y", "@modelcontextprotocol/server-xyz"],\n  "env": {}\n}`}
                  />
                  {rawJsonError && (
                    <p className="text-[11px] text-destructive bg-destructive/10 p-2 rounded-lg border border-destructive/20 font-mono">
                      {rawJsonError}
                    </p>
                  )}
                </div>

                {/* Editor action buttons */}
                <div className="flex items-center justify-between gap-2 pt-1 border-t border-border/40">
                  <div className="flex items-center gap-2">
                    <button
                      type="button"
                      onClick={handleFormatRawJson}
                      className="px-2.5 py-1 text-xs bg-muted/60 hover:bg-muted border border-border rounded-lg text-muted-foreground hover:text-foreground transition-all flex items-center gap-1"
                    >
                      Format JSON
                    </button>
                    <button
                      type="button"
                      onClick={() => {
                        const ok = syncRawJsonToForm(rawJsonInput);
                        if (ok) {
                          toast.success('Synced to visual form builder');
                          setMcpModalTab('form');
                        }
                      }}
                      className="px-2.5 py-1 text-xs bg-muted/60 hover:bg-muted border border-border rounded-lg text-muted-foreground hover:text-foreground transition-all flex items-center gap-1"
                    >
                      Sync to Form View
                    </button>
                  </div>
                </div>

                {/* Dedicated Manual OAuth Trigger Hub */}
                <div className="p-4 rounded-xl bg-gradient-to-br from-card to-muted/20 border border-primary/25 space-y-3 shadow-sm">
                  <div className="flex items-start justify-between gap-3">
                    <div className="space-y-0.5">
                      <div className="flex items-center gap-1.5 text-xs font-semibold text-foreground">
                        <Zap size={14} className="text-amber-500 fill-amber-500" />
                        <span>Manually Trigger OAuth Authorization</span>
                      </div>
                      <p className="text-[11px] text-muted-foreground leading-relaxed">
                        Trigger the authentication flow directly. Captured tokens will automatically be injected into the JSON <code className="font-mono text-[10px] bg-muted px-1.5 py-0.5 rounded text-foreground/80">env</code> block.
                      </p>
                    </div>
                  </div>

                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 pt-1">
                    <div className="space-y-1">
                      <label className="text-[11px] font-medium text-foreground">Select OAuth Provider</label>
                      <select
                        value={jsonOAuthProvider}
                        onChange={(e) => setJsonOAuthProvider(e.target.value as any)}
                        className="w-full bg-background border border-input rounded-lg px-2.5 py-1.5 text-xs outline-none focus:ring-1 focus:ring-primary"
                      >
                        <option value="github">GitHub (Zero-Config Device Flow)</option>
                        <option value="google">Google Workspace (InstalledAppFlow)</option>
                        <option value="slack">Slack (OAuth PKCE)</option>
                        <option value="custom">Custom Remote MCP Endpoints (PKCE)</option>
                      </select>
                    </div>

                    <div className="flex items-end">
                      <button
                        type="button"
                        onClick={handleTriggerAuthFromRawJson}
                        className="w-full py-2 px-3 bg-gradient-to-r from-amber-500 to-amber-600 hover:from-amber-600 hover:to-amber-700 text-slate-950 font-semibold text-xs rounded-lg transition-all shadow-sm active:scale-95 flex items-center justify-center gap-1.5"
                      >
                        <Zap size={13} className="fill-slate-950" />
                        <span>Authorize & Inject Tokens</span>
                      </button>
                    </div>
                  </div>

                  {jsonOAuthProvider === 'custom' && (
                    <div className="p-3 bg-background/80 rounded-lg border border-border/80 space-y-2 mt-2">
                      <span className="text-[10px] font-semibold uppercase text-muted-foreground block">
                        Custom OAuth PKCE Parameters
                      </span>
                      <div className="grid grid-cols-2 gap-2">
                        <input
                          type="text"
                          value={customOAuthParams.client_id}
                          onChange={(e) => setCustomOAuthParams({ ...customOAuthParams, client_id: e.target.value })}
                          placeholder="Client ID *"
                          className="bg-muted/40 border border-input rounded px-2 py-1 text-xs font-mono outline-none"
                        />
                        <input
                          type="text"
                          value={customOAuthParams.scopes}
                          onChange={(e) => setCustomOAuthParams({ ...customOAuthParams, scopes: e.target.value })}
                          placeholder="Scopes (e.g. read write)"
                          className="bg-muted/40 border border-input rounded px-2 py-1 text-xs font-mono outline-none"
                        />
                        <input
                          type="text"
                          value={customOAuthParams.auth_url}
                          onChange={(e) => setCustomOAuthParams({ ...customOAuthParams, auth_url: e.target.value })}
                          placeholder="Authorization URL *"
                          className="bg-muted/40 border border-input rounded px-2 py-1 text-xs font-mono outline-none col-span-2"
                        />
                        <input
                          type="text"
                          value={customOAuthParams.token_url}
                          onChange={(e) => setCustomOAuthParams({ ...customOAuthParams, token_url: e.target.value })}
                          placeholder="Token URL *"
                          className="bg-muted/40 border border-input rounded px-2 py-1 text-xs font-mono outline-none col-span-2"
                        />
                      </div>
                    </div>
                  )}
                </div>
              </div>
            )}

            {/* Modal Footer */}
            <div className="px-6 py-3.5 border-t border-border bg-muted/20 flex items-center justify-end gap-2 shrink-0">
              <button
                type="button"
                onClick={() => setIsMcpModalOpen(false)}
                className="px-4 py-2 rounded-lg text-xs font-medium hover:bg-muted text-muted-foreground hover:text-foreground transition-colors"
              >
                Cancel
              </button>
              <button
                type="button"
                onClick={handleSaveMcpServer}
                disabled={!mcpForm.name.trim() || (mcpForm.type === 'stdio' && !mcpForm.command.trim()) || (mcpForm.type === 'sse' && !mcpForm.url.trim())}
                className="px-4 py-2 bg-primary text-primary-foreground text-xs font-medium rounded-lg hover:bg-primary/90 transition-all shadow-sm active:scale-95 disabled:opacity-50 disabled:pointer-events-none flex items-center gap-1.5"
              >
                <Save size={14} />
                <span>{editingMcpId ? 'Update Server' : 'Register Server'}</span>
              </button>
            </div>
          </div>
        </div>
      )}

      {/* OAuth Authorization Dialog Modal */}
      {oauthModal && oauthModal.isOpen && (
        <div className="fixed inset-0 bg-background/80 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-card border border-border rounded-2xl w-full max-w-md shadow-2xl overflow-hidden flex flex-col animate-in fade-in zoom-in-95 duration-150">
            {/* Modal Header */}
            <div className="px-6 py-4 border-b border-border flex items-center justify-between">
              <div className="flex items-center gap-2">
                <ShieldCheck size={18} className="text-emerald-500" />
                <h3 className="font-semibold text-sm">
                  {oauthModal.provider.toUpperCase()} Authorization
                </h3>
              </div>
              <button
                type="button"
                onClick={() => setOauthModal(null)}
                className="p-1 hover:bg-muted rounded-lg text-muted-foreground hover:text-foreground"
              >
                <X size={16} />
              </button>
            </div>

            {/* Modal Content */}
            <div className="p-6 space-y-4">
              {oauthModal.status === 'success' ? (
                <div className="text-center py-6 space-y-3">
                  <div className="w-14 h-14 bg-emerald-500/10 text-emerald-500 rounded-full flex items-center justify-center mx-auto border border-emerald-500/20">
                    <CheckCircle2 size={32} />
                  </div>
                  <h4 className="text-base font-semibold text-foreground">Authorization Successful!</h4>
                  <p className="text-xs text-muted-foreground">
                    Connected to {oauthModal.provider.toUpperCase()}. Tokens stored in <code className="bg-muted px-1.5 py-0.5 rounded text-[11px] font-mono">~/.openagents/credentials/oauth_tokens.json</code>.
                  </p>
                </div>
              ) : oauthModal.status === 'error' ? (
                <div className="text-center py-4 space-y-3">
                  <div className="w-12 h-12 bg-destructive/10 text-destructive rounded-full flex items-center justify-center mx-auto border border-destructive/20">
                    <AlertCircle size={28} />
                  </div>
                  <h4 className="text-sm font-semibold text-foreground">Authorization Failed</h4>
                  <p className="text-xs text-muted-foreground max-w-xs mx-auto">
                    {oauthModal.error || 'The authentication process was cancelled or timed out.'}
                  </p>
                  <button
                    type="button"
                    onClick={() => handleConnectOAuth(oauthModal.provider)}
                    className="px-4 py-2 bg-primary text-primary-foreground text-xs font-medium rounded-lg hover:bg-primary/90 transition-all mt-2"
                  >
                    Try Again
                  </button>
                </div>
              ) : (
                <div className="space-y-4">
                  {oauthModal.userCode ? (
                    // GitHub Device Flow Presentation
                    <div className="space-y-3">
                      <div className="p-3.5 bg-muted/30 rounded-xl border border-border/60 text-center space-y-2">
                        <span className="text-xs text-muted-foreground block font-medium">Your One-Time Device Code</span>
                        <div className="flex items-center justify-center gap-2">
                          <code className="text-2xl font-mono font-bold tracking-widest text-primary px-3 py-1 bg-background rounded-lg border border-border">
                            {oauthModal.userCode}
                          </code>
                          <button
                            type="button"
                            onClick={() => {
                              navigator.clipboard.writeText(oauthModal.userCode || '');
                              setCopiedCode(true);
                              setTimeout(() => setCopiedCode(false), 2000);
                            }}
                            className="p-2 bg-background border border-border rounded-lg hover:bg-muted text-muted-foreground hover:text-foreground transition-colors"
                            title="Copy code"
                          >
                            {copiedCode ? <Check size={16} className="text-emerald-500" /> : <Copy size={16} />}
                          </button>
                        </div>
                        {copiedCode && (
                          <span className="text-[10px] text-emerald-500 font-medium block">
                            Copied to clipboard!
                          </span>
                        )}
                      </div>

                      <div className="space-y-2 text-xs text-muted-foreground leading-relaxed">
                        <p className="flex items-start gap-2">
                          <span className="w-4 h-4 rounded-full bg-primary/20 text-primary flex items-center justify-center text-[10px] font-bold shrink-0 mt-0.5">1</span>
                          <span>Browser opening to <a href={oauthModal.verificationUri || 'https://github.com/login/device'} target="_blank" rel="noreferrer" className="text-primary hover:underline font-mono inline-flex items-center gap-0.5">{oauthModal.verificationUri || 'https://github.com/login/device'} <ExternalLink size={10} /></a></span>
                        </p>
                        <p className="flex items-start gap-2">
                          <span className="w-4 h-4 rounded-full bg-primary/20 text-primary flex items-center justify-center text-[10px] font-bold shrink-0 mt-0.5">2</span>
                          <span>Paste the code above and click <strong>Authorize OpenAgents</strong>.</span>
                        </p>
                      </div>
                    </div>
                  ) : (
                    // Google / Loopback PKCE Presentation
                    <div className="py-2 text-center space-y-3">
                      <div className="w-12 h-12 bg-blue-500/10 text-blue-500 rounded-full flex items-center justify-center mx-auto border border-blue-500/20">
                        <Globe size={24} />
                      </div>
                      <h4 className="text-sm font-semibold text-foreground">Browser Window Opened</h4>
                      <p className="text-xs text-muted-foreground leading-relaxed">
                        Sign in with your Google account in the browser. When complete, OpenAgents will capture the authorization callback automatically.
                      </p>
                    </div>
                  )}

                  {/* Polling Spinner */}
                  <div className="pt-2 flex items-center justify-center gap-2 text-xs text-muted-foreground border-t border-border/40">
                    <div className="w-3.5 h-3.5 border-2 border-primary border-t-transparent rounded-full animate-spin"></div>
                    <span>Waiting for authorization in browser...</span>
                  </div>
                </div>
              )}
            </div>

            {/* Modal Footer */}
            <div className="px-6 py-3 border-t border-border bg-muted/20 flex justify-end">
              <button
                type="button"
                onClick={() => setOauthModal(null)}
                className="px-4 py-1.5 rounded-lg text-xs font-medium hover:bg-muted text-muted-foreground hover:text-foreground transition-colors"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default SettingsPage;
