import React, { useState, useEffect } from 'react';
import { 
  Sparkles, 
  Folder, 
  FileText, 
  Plus, 
  Trash2, 
  Search, 
  ExternalLink, 
  BookOpen, 
  Terminal, 
  Globe, 
  FolderGit2, 
  Database,
  X,
  Check,
  RotateCw
} from 'lucide-react';
import axios from 'axios';
import { cn } from '../lib/utils';
import toast from '../utils/toast';

const BASE_URL = 'http://localhost:8000';

interface SkillSummary {
  id: string;
  name: string;
  description: string;
  compatibility?: string;
  path: string;
  has_scripts?: boolean;
  has_resources?: boolean;
}

interface SkillDetail {
  name: string;
  description: string;
  compatibility?: string;
  instructions: string;
  path: string;
}

const SKILL_ICONS: Record<string, React.ReactNode> = {
  'terminal-execution': <Terminal size={20} className="text-emerald-400" />,
  'filesystem-management': <Folder size={20} className="text-amber-400" />,
  'knowledge-retrieval': <Database size={20} className="text-blue-400" />,
  'browser-automation': <Globe size={20} className="text-purple-400" />,
  'mcp-integration': <FolderGit2 size={20} className="text-cyan-400" />,
  'web-scraping': <Search size={20} className="text-rose-400" />,
};

const SkillsPage: React.FC = () => {
  const [skills, setSkills] = useState<SkillSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  
  // Inspection modal
  const [selectedSkill, setSelectedSkill] = useState<SkillDetail | null>(null);

  // Create Skill modal
  const [isCreateOpen, setIsCreateOpen] = useState(false);
  const [newSkillId, setNewSkillId] = useState('');
  const [newSkillName, setNewSkillName] = useState('');
  const [newSkillDesc, setNewSkillDesc] = useState('');
  const [newSkillCompat, setNewSkillCompat] = useState('');
  const [newSkillContent, setNewSkillContent] = useState(
`# Skill Workflow & Instructions

## Overview
Describe what this skill enables the agents to accomplish.

## Guidelines & Rules
1. Step-by-step guidance for agent reasoning.
2. Precision tool invocation instructions.
3. Edge-case handling rules.
`
  );
  const [isSubmitting, setIsSubmitting] = useState(false);

  useEffect(() => {
    fetchSkills();
  }, []);

  const fetchSkills = async () => {
    try {
      setLoading(true);
      const res = await axios.get(`${BASE_URL}/skills`);
      setSkills(res.data);
    } catch (err: any) {
      toast.error('Failed to load skills from ~/.openagents/skills');
    } finally {
      setLoading(false);
    }
  };

  const handleInspectSkill = async (skillId: string) => {
    try {
      const res = await axios.get(`${BASE_URL}/skills/${skillId}`);
      setSelectedSkill(res.data);
    } catch (err: any) {
      toast.error(`Failed to load skill details for ${skillId}`);
    }
  };

  const handleDeleteSkill = async (skillId: string, e: React.MouseEvent) => {
    e.stopPropagation();
    if (!confirm(`Are you sure you want to delete skill '${skillId}' from ~/.openagents/skills?`)) {
      return;
    }
    try {
      await axios.delete(`${BASE_URL}/skills/${skillId}`);
      toast.success(`Skill '${skillId}' deleted.`);
      fetchSkills();
      if (selectedSkill?.name === skillId) {
        setSelectedSkill(null);
      }
    } catch (err: any) {
      toast.error(err.response?.data?.detail || 'Failed to delete skill.');
    }
  };

  const handleCreateSkill = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newSkillId.trim() || !newSkillName.trim()) {
      toast.error('Skill ID and Name are required.');
      return;
    }

    const sanitizedId = newSkillId.toLowerCase().replace(/[^a-z0-9-_]/g, '-');

    try {
      setIsSubmitting(true);
      await axios.post(`${BASE_URL}/skills`, {
        id: sanitizedId,
        content: newSkillContent,
        metadata: {
          name: newSkillName,
          description: newSkillDesc,
          compatibility: newSkillCompat || undefined
        }
      });
      toast.success(`Skill '${newSkillName}' saved to ~/.openagents/skills/${sanitizedId}/`);
      setIsCreateOpen(false);
      setNewSkillId('');
      setNewSkillName('');
      setNewSkillDesc('');
      setNewSkillCompat('');
      fetchSkills();
    } catch (err: any) {
      toast.error(err.response?.data?.detail || 'Failed to save skill.');
    } finally {
      setIsSubmitting(false);
    }
  };

  const filteredSkills = skills.filter((s) =>
    s.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
    s.id.toLowerCase().includes(searchQuery.toLowerCase()) ||
    s.description.toLowerCase().includes(searchQuery.toLowerCase())
  );

  return (
    <div className="h-full flex flex-col bg-background text-foreground overflow-y-auto">
      {/* Header */}
      <div className="border-b border-border bg-card/40 backdrop-blur p-6">
        <div className="max-w-6xl mx-auto flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-2">
              <Sparkles className="text-primary w-6 h-6" />
              <h1 className="text-2xl font-bold tracking-tight">OpenAgents Skills</h1>
              <span className="text-xs px-2 py-0.5 rounded-full bg-primary/10 text-primary border border-primary/20 font-mono">
                ~/.openagents/skills
              </span>
            </div>
            <p className="text-muted-foreground text-sm mt-1">
              Autonomous skill workflows and playbooks that agents automatically discover and execute.
            </p>
          </div>

          <div className="flex items-center gap-3">
            <button
              onClick={fetchSkills}
              disabled={loading}
              className="p-2 border border-border rounded-lg hover:bg-hover transition-colors text-muted-foreground hover:text-foreground"
              title="Refresh Skills"
            >
              <RotateCw size={18} className={cn(loading && 'animate-spin')} />
            </button>
            <button
              onClick={() => setIsCreateOpen(true)}
              className="flex items-center gap-2 bg-primary text-primary-foreground px-4 py-2 rounded-lg font-medium hover:bg-primary/90 transition-all shadow-sm active:scale-95 text-sm"
            >
              <Plus size={16} />
              Create Skill
            </button>
          </div>
        </div>

        {/* Search */}
        <div className="max-w-6xl mx-auto mt-4">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground" size={16} />
            <input
              type="text"
              placeholder="Filter installed skills by name, ID, or capability..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-9 pr-4 py-2 rounded-lg bg-background border border-border text-sm placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-primary/40 transition-all"
            />
          </div>
        </div>
      </div>

      {/* Content */}
      <div className="flex-1 max-w-6xl w-full mx-auto p-6">
        {loading ? (
          <div className="flex items-center justify-center py-20 text-muted-foreground gap-3">
            <RotateCw className="animate-spin text-primary" size={24} />
            <span>Discovering skills in ~/.openagents/skills/...</span>
          </div>
        ) : filteredSkills.length === 0 ? (
          <div className="text-center py-16 border border-dashed border-border rounded-2xl bg-card/30 p-8">
            <BookOpen className="mx-auto w-12 h-12 text-muted-foreground/60 mb-3" />
            <h3 className="text-lg font-semibold">No skills found</h3>
            <p className="text-sm text-muted-foreground max-w-md mx-auto mt-1 mb-4">
              {searchQuery ? `No skills match query '${searchQuery}'.` : 'No skills are currently installed in ~/.openagents/skills.'}
            </p>
            <button
              onClick={() => setIsCreateOpen(true)}
              className="inline-flex items-center gap-2 text-sm text-primary font-medium hover:underline"
            >
              <Plus size={16} />
              Create your first custom skill
            </button>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {filteredSkills.map((skill) => {
              const icon = SKILL_ICONS[skill.id] || <Sparkles size={20} className="text-primary" />;
              return (
                <div
                  key={skill.id}
                  onClick={() => handleInspectSkill(skill.id)}
                  className="group relative flex flex-col justify-between border border-border bg-card hover:border-primary/50 hover:shadow-md transition-all duration-200 rounded-xl p-5 cursor-pointer"
                >
                  <div>
                    <div className="flex items-start justify-between gap-3">
                      <div className="flex items-center gap-3">
                        <div className="p-2.5 rounded-lg bg-secondary/80 border border-border/60 group-hover:scale-105 transition-transform">
                          {icon}
                        </div>
                        <div>
                          <h3 className="font-semibold text-base tracking-tight group-hover:text-primary transition-colors">
                            {skill.name}
                          </h3>
                          <span className="text-xs font-mono text-muted-foreground">
                            {skill.id}
                          </span>
                        </div>
                      </div>

                      <button
                        onClick={(e) => handleDeleteSkill(skill.id, e)}
                        className="opacity-0 group-hover:opacity-100 p-1.5 rounded-md hover:bg-destructive/10 text-muted-foreground hover:text-destructive transition-all"
                        title="Delete Skill"
                      >
                        <Trash2 size={15} />
                      </button>
                    </div>

                    <p className="text-sm text-muted-foreground mt-3 line-clamp-3 leading-relaxed">
                      {skill.description || 'No description provided.'}
                    </p>
                  </div>

                  <div className="mt-4 pt-3 border-t border-border/60 flex items-center justify-between text-xs text-muted-foreground">
                    <div className="flex items-center gap-1.5">
                      <FileText size={13} />
                      <span>SKILL.md</span>
                      {skill.has_scripts && (
                        <span className="px-1.5 py-0.5 rounded bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 text-[10px]">
                          Scripts
                        </span>
                      )}
                    </div>
                    <span className="text-primary font-medium group-hover:translate-x-0.5 transition-transform flex items-center gap-1">
                      Inspect <ExternalLink size={12} />
                    </span>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* Inspect Skill Modal */}
      {selectedSkill && (
        <div className="fixed inset-0 bg-background/80 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-card border border-border rounded-2xl w-full max-w-3xl max-h-[85vh] flex flex-col shadow-2xl overflow-hidden animate-in fade-in zoom-in-95 duration-150">
            {/* Modal Header */}
            <div className="p-5 border-b border-border flex items-center justify-between bg-muted/40">
              <div className="flex items-center gap-3">
                <BookOpen size={20} className="text-primary" />
                <div>
                  <h2 className="font-bold text-lg">{selectedSkill.name}</h2>
                  <p className="text-xs font-mono text-muted-foreground">{selectedSkill.path}</p>
                </div>
              </div>
              <button
                onClick={() => setSelectedSkill(null)}
                className="p-1.5 rounded-lg hover:bg-hover text-muted-foreground hover:text-foreground transition-colors"
              >
                <X size={18} />
              </button>
            </div>

            {/* Modal Content */}
            <div className="p-6 overflow-y-auto flex-1 font-mono text-xs bg-background/50">
              {selectedSkill.description && (
                <div className="mb-4 p-3 rounded-lg bg-secondary/50 border border-border font-sans text-sm">
                  <span className="font-semibold text-primary">Purpose: </span>
                  {selectedSkill.description}
                </div>
              )}
              <pre className="whitespace-pre-wrap leading-relaxed text-foreground/90 font-mono">
                {selectedSkill.instructions}
              </pre>
            </div>

            {/* Modal Footer */}
            <div className="p-4 border-t border-border bg-muted/20 flex justify-end">
              <button
                onClick={() => setSelectedSkill(null)}
                className="px-4 py-2 bg-secondary text-secondary-foreground rounded-lg text-sm font-medium hover:bg-secondary/80 transition-colors"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Create Skill Modal */}
      {isCreateOpen && (
        <div className="fixed inset-0 bg-background/80 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-card border border-border rounded-2xl w-full max-w-2xl max-h-[90vh] flex flex-col shadow-2xl overflow-hidden animate-in fade-in zoom-in-95 duration-150">
            <div className="p-5 border-b border-border flex items-center justify-between bg-muted/40">
              <div className="flex items-center gap-3">
                <Plus size={20} className="text-primary" />
                <div>
                  <h2 className="font-bold text-lg">Create New Skill</h2>
                  <p className="text-xs text-muted-foreground">Will be saved to ~/.openagents/skills/&lt;id&gt;/SKILL.md</p>
                </div>
              </div>
              <button
                onClick={() => setIsCreateOpen(false)}
                className="p-1.5 rounded-lg hover:bg-hover text-muted-foreground hover:text-foreground transition-colors"
              >
                <X size={18} />
              </button>
            </div>

            <form onSubmit={handleCreateSkill} className="p-6 overflow-y-auto flex-1 space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-medium text-muted-foreground mb-1">
                    Skill ID (folder name)
                  </label>
                  <input
                    type="text"
                    required
                    placeholder="e.g. docker-compose-ops"
                    value={newSkillId}
                    onChange={(e) => setNewSkillId(e.target.value)}
                    className="w-full px-3 py-2 rounded-lg bg-background border border-border text-sm font-mono focus:outline-none focus:ring-2 focus:ring-primary/40"
                  />
                </div>
                <div>
                  <label className="block text-xs font-medium text-muted-foreground mb-1">
                    Skill Name
                  </label>
                  <input
                    type="text"
                    required
                    placeholder="e.g. Docker Compose Operations"
                    value={newSkillName}
                    onChange={(e) => setNewSkillName(e.target.value)}
                    className="w-full px-3 py-2 rounded-lg bg-background border border-border text-sm focus:outline-none focus:ring-2 focus:ring-primary/40"
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs font-medium text-muted-foreground mb-1">
                  Description
                </label>
                <input
                  type="text"
                  placeholder="Concise summary for Orchestrator task routing"
                  value={newSkillDesc}
                  onChange={(e) => setNewSkillDesc(e.target.value)}
                  className="w-full px-3 py-2 rounded-lg bg-background border border-border text-sm focus:outline-none focus:ring-2 focus:ring-primary/40"
                />
              </div>

              <div>
                <label className="block text-xs font-medium text-muted-foreground mb-1">
                  SKILL.md Instructions (Markdown)
                </label>
                <textarea
                  rows={10}
                  value={newSkillContent}
                  onChange={(e) => setNewSkillContent(e.target.value)}
                  className="w-full p-3 rounded-lg bg-background border border-border text-xs font-mono focus:outline-none focus:ring-2 focus:ring-primary/40 resize-y"
                />
              </div>

              <div className="flex justify-end gap-3 pt-2">
                <button
                  type="button"
                  onClick={() => setIsCreateOpen(false)}
                  className="px-4 py-2 border border-border rounded-lg text-sm hover:bg-hover transition-colors"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={isSubmitting}
                  className="px-4 py-2 bg-primary text-primary-foreground rounded-lg text-sm font-medium hover:bg-primary/90 transition-colors flex items-center gap-2"
                >
                  {isSubmitting ? <RotateCw className="animate-spin" size={16} /> : <Check size={16} />}
                  Save Skill
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

export default SkillsPage;
