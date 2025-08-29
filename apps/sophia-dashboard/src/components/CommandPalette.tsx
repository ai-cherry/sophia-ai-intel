'use client';

import { useState, useEffect, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Command } from 'cmdk';

interface CommandItem {
  id: string;
  label: string;
  description?: string;
  icon: string;
  action: () => void;
  shortcut?: string;
  category: 'agent' | 'research' | 'code' | 'navigation' | 'system';
}

interface CommandPaletteProps {
  isOpen: boolean;
  onClose: () => void;
  onCommand: (command: string) => void;
}

export default function CommandPalette({ isOpen, onClose, onCommand }: CommandPaletteProps) {
  const [search, setSearch] = useState('');
  const [selectedCategory, setSelectedCategory] = useState<string | null>(null);

  const commands: CommandItem[] = [
    // Agent Commands
    {
      id: 'deploy-research',
      label: 'Deploy Research Swarm',
      description: 'Launch research agents for deep analysis',
      icon: '🔍',
      action: () => onCommand('deploy a swarm of research agents for comprehensive analysis'),
      shortcut: 'Cmd+Shift+R',
      category: 'agent'
    },
    {
      id: 'deploy-code',
      label: 'Deploy Code Agent',
      description: 'Start code generation agent',
      icon: '💻',
      action: () => onCommand('deploy code generation agent'),
      shortcut: 'Cmd+Shift+C',
      category: 'agent'
    },
    {
      id: 'deploy-planning',
      label: 'Deploy Planning Swarm',
      description: 'Create strategic plans with multiple perspectives',
      icon: '📋',
      action: () => onCommand('deploy planning swarm for strategic analysis'),
      category: 'agent'
    },
    {
      id: 'agent-status',
      label: 'Show Agent Status',
      description: 'View all active agents',
      icon: '📊',
      action: () => onCommand('show status of all active agents'),
      shortcut: 'Cmd+A',
      category: 'agent'
    },
    
    // Research Commands
    {
      id: 'research-ai',
      label: 'Research AI Papers',
      description: 'Search latest AI research',
      icon: '📚',
      action: () => onCommand('research the latest AI papers and breakthroughs'),
      category: 'research'
    },
    {
      id: 'research-web',
      label: 'Web Research',
      description: 'Search the web for information',
      icon: '🌐',
      action: () => onCommand('search the web for information'),
      category: 'research'
    },
    
    // Code Commands
    {
      id: 'code-api',
      label: 'Generate API Code',
      description: 'Create REST API endpoints',
      icon: '🔌',
      action: () => onCommand('generate a REST API with CRUD operations'),
      category: 'code'
    },
    {
      id: 'code-component',
      label: 'Generate React Component',
      description: 'Create React/Next.js component',
      icon: '⚛️',
      action: () => onCommand('generate a React component'),
      category: 'code'
    },
    {
      id: 'code-python',
      label: 'Generate Python Script',
      description: 'Create Python automation script',
      icon: '🐍',
      action: () => onCommand('generate a Python script'),
      category: 'code'
    },
    
    // Navigation Commands
    {
      id: 'nav-chat',
      label: 'Go to Chat',
      icon: '💬',
      action: () => console.log('Navigate to chat'),
      shortcut: 'Cmd+1',
      category: 'navigation'
    },
    {
      id: 'nav-agents',
      label: 'Go to Agents',
      icon: '🤖',
      action: () => console.log('Navigate to agents'),
      shortcut: 'Cmd+2',
      category: 'navigation'
    },
    
    // System Commands
    {
      id: 'clear-chat',
      label: 'Clear Chat History',
      icon: '🗑️',
      action: () => console.log('Clear chat'),
      category: 'system'
    },
    {
      id: 'export-conversation',
      label: 'Export Conversation',
      icon: '💾',
      action: () => console.log('Export conversation'),
      shortcut: 'Cmd+S',
      category: 'system'
    }
  ];

  const filteredCommands = commands.filter(cmd => {
    const matchesSearch = search === '' || 
      cmd.label.toLowerCase().includes(search.toLowerCase()) ||
      cmd.description?.toLowerCase().includes(search.toLowerCase());
    
    const matchesCategory = !selectedCategory || cmd.category === selectedCategory;
    
    return matchesSearch && matchesCategory;
  });

  const categories = [
    { id: 'agent', label: 'Agents', icon: '🤖' },
    { id: 'research', label: 'Research', icon: '🔍' },
    { id: 'code', label: 'Code', icon: '💻' },
    { id: 'navigation', label: 'Navigation', icon: '🧭' },
    { id: 'system', label: 'System', icon: '⚙️' }
  ];

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
        e.preventDefault();
        // This would be handled by parent component
      }
      
      if (e.key === 'Escape' && isOpen) {
        onClose();
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  return (
    <AnimatePresence>
      <div className="fixed inset-0 z-50 flex items-start justify-center pt-20">
        {/* Backdrop */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          onClick={onClose}
          className="absolute inset-0 bg-black/60 backdrop-blur-sm"
        />
        
        {/* Command Palette */}
        <motion.div
          initial={{ opacity: 0, scale: 0.95, y: -20 }}
          animate={{ opacity: 1, scale: 1, y: 0 }}
          exit={{ opacity: 0, scale: 0.95, y: -20 }}
          className="relative w-full max-w-2xl bg-gray-900 rounded-xl shadow-2xl border border-cyan-500/20 overflow-hidden"
        >
          <Command className="h-full">
            {/* Search Input */}
            <div className="border-b border-white/10 p-4">
              <div className="flex items-center gap-3">
                <span className="text-gray-400">🔍</span>
                <Command.Input
                  value={search}
                  onValueChange={setSearch}
                  placeholder="Type a command or search..."
                  className="flex-1 bg-transparent text-white placeholder-gray-500 outline-none"
                />
                <span className="text-xs text-gray-500">ESC to close</span>
              </div>
            </div>
            
            {/* Category Filters */}
            <div className="flex gap-2 p-4 border-b border-white/10">
              <button
                onClick={() => setSelectedCategory(null)}
                className={`px-3 py-1 text-xs rounded-lg transition-all ${
                  !selectedCategory 
                    ? 'bg-cyan-600/20 text-cyan-400 border border-cyan-600/30' 
                    : 'text-gray-400 hover:text-white hover:bg-white/5'
                }`}
              >
                All
              </button>
              {categories.map(cat => (
                <button
                  key={cat.id}
                  onClick={() => setSelectedCategory(cat.id)}
                  className={`px-3 py-1 text-xs rounded-lg transition-all flex items-center gap-1 ${
                    selectedCategory === cat.id 
                      ? 'bg-cyan-600/20 text-cyan-400 border border-cyan-600/30' 
                      : 'text-gray-400 hover:text-white hover:bg-white/5'
                  }`}
                >
                  <span>{cat.icon}</span>
                  <span>{cat.label}</span>
                </button>
              ))}
            </div>
            
            {/* Command List */}
            <Command.List className="max-h-96 overflow-y-auto p-2">
              {filteredCommands.length === 0 ? (
                <div className="text-center py-8 text-gray-500">
                  No commands found
                </div>
              ) : (
                filteredCommands.map(cmd => (
                  <Command.Item
                    key={cmd.id}
                    value={cmd.label}
                    onSelect={() => {
                      cmd.action();
                      onClose();
                    }}
                    className="px-3 py-2 rounded-lg cursor-pointer transition-all hover:bg-white/5 group"
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-3">
                        <span className="text-xl">{cmd.icon}</span>
                        <div>
                          <div className="text-sm text-white group-hover:text-cyan-400 transition-colors">
                            {cmd.label}
                          </div>
                          {cmd.description && (
                            <div className="text-xs text-gray-500">
                              {cmd.description}
                            </div>
                          )}
                        </div>
                      </div>
                      {cmd.shortcut && (
                        <span className="text-xs text-gray-600 group-hover:text-gray-400">
                          {cmd.shortcut}
                        </span>
                      )}
                    </div>
                  </Command.Item>
                ))
              )}
            </Command.List>
          </Command>
        </motion.div>
      </div>
    </AnimatePresence>
  );
}