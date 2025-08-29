'use client';

import { useEffect } from 'react';

interface QuickAction {
  id: string;
  icon: string;
  label: string;
  command: string;
  shortcut?: string;
  color: string;
}

interface QuickActionsProps {
  onAction: (command: string) => void;
  isLoading?: boolean;
}

const quickActions: QuickAction[] = [
  {
    id: 'deploy',
    icon: '🚀',
    label: 'Deploy Agent',
    command: 'deploy a swarm of research agents',
    shortcut: 'Cmd+1',
    color: 'from-purple-600 to-pink-600'
  },
  {
    id: 'research',
    icon: '🔍',
    label: 'Research',
    command: 'research the latest AI developments',
    shortcut: 'Cmd+2',
    color: 'from-blue-600 to-cyan-600'
  },
  {
    id: 'code',
    icon: '💻',
    label: 'Generate Code',
    command: 'generate code for a REST API',
    shortcut: 'Cmd+3',
    color: 'from-green-600 to-emerald-600'
  },
  {
    id: 'plan',
    icon: '📋',
    label: 'Create Plan',
    command: 'create a detailed plan for building an AI system',
    shortcut: 'Cmd+4',
    color: 'from-orange-600 to-red-600'
  },
  {
    id: 'status',
    icon: '📊',
    label: 'Agent Status',
    command: 'show status of all active agents',
    shortcut: 'Cmd+5',
    color: 'from-indigo-600 to-blue-600'
  }
];

export default function QuickActions({ onAction, isLoading = false }: QuickActionsProps) {
  // Set up keyboard shortcuts
  useEffect(() => {
    const handleKeyPress = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key >= '1' && e.key <= '5') {
        e.preventDefault();
        const index = parseInt(e.key) - 1;
        if (quickActions[index] && !isLoading) {
          onAction(quickActions[index].command);
        }
      }
    };

    window.addEventListener('keydown', handleKeyPress);
    return () => window.removeEventListener('keydown', handleKeyPress);
  }, [onAction, isLoading]);

  return (
    <div className="p-4 bg-gray-900/50 backdrop-blur-lg rounded-xl border border-cyan-500/20">
      <div className="flex items-center justify-between mb-3">
        <h3 className="text-sm font-semibold text-white">Quick Actions</h3>
        <span className="text-xs text-gray-500">Press shortcuts to execute</span>
      </div>
      
      <div className="grid grid-cols-5 gap-2">
        {quickActions.map((action) => (
          <button
            key={action.id}
            onClick={() => onAction(action.command)}
            disabled={isLoading}
            className={`
              group relative p-3 rounded-lg transition-all duration-300
              bg-gradient-to-br ${action.color}
              hover:scale-105 hover:shadow-xl
              disabled:opacity-50 disabled:cursor-not-allowed
              transform-gpu
            `}
            title={`${action.label} (${action.shortcut})`}
          >
            <div className="flex flex-col items-center gap-1">
              <span className="text-2xl filter drop-shadow-lg">{action.icon}</span>
              <span className="text-xs text-white/90 font-medium">{action.label}</span>
            </div>
            
            {/* Shortcut badge */}
            <div className="absolute top-1 right-1 opacity-0 group-hover:opacity-100 transition-opacity">
              <span className="text-[10px] px-1.5 py-0.5 bg-black/30 text-white/80 rounded">
                {action.shortcut}
              </span>
            </div>
            
            {/* Loading indicator */}
            {isLoading && (
              <div className="absolute inset-0 bg-black/50 rounded-lg flex items-center justify-center">
                <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
              </div>
            )}
          </button>
        ))}
      </div>
      
      <div className="mt-3 text-xs text-gray-500 text-center">
        Click or use keyboard shortcuts to execute actions instantly
      </div>
    </div>
  );
}

// Also export for use elsewhere
export { quickActions };