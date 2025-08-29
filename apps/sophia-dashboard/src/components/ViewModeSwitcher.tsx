'use client';

interface ViewMode {
  id: string;
  label: string;
  icon: string;
  description: string;
  color: string;
}

interface ViewModeSwitcherProps {
  currentView: string;
  onViewChange: (view: string) => void;
}

const viewModes: ViewMode[] = [
  { 
    id: 'chat', 
    label: 'Chat', 
    icon: '💬', 
    description: 'Converse with Sophia Supreme',
    color: 'from-blue-600 to-cyan-600'
  },
  { 
    id: 'swarm', 
    label: 'Swarm', 
    icon: '🐝', 
    description: 'Visualize agent networks',
    color: 'from-purple-600 to-pink-600'
  },
  { 
    id: 'code', 
    label: 'Code', 
    icon: '💻', 
    description: 'Live code generation',
    color: 'from-green-600 to-emerald-600'
  },
  { 
    id: 'research', 
    label: 'Research', 
    icon: '🔍', 
    description: 'Knowledge exploration',
    color: 'from-orange-600 to-red-600'
  },
  { 
    id: 'metrics', 
    label: 'Metrics', 
    icon: '📊', 
    description: 'Performance analytics',
    color: 'from-indigo-600 to-blue-600'
  }
];

export default function ViewModeSwitcher({ currentView, onViewChange }: ViewModeSwitcherProps) {
  return (
    <div className="flex items-center gap-2 p-2 bg-gray-900/70 backdrop-blur-lg rounded-xl border border-cyan-500/20">
      {viewModes.map((mode) => (
        <button
          key={mode.id}
          onClick={() => onViewChange(mode.id)}
          className={`
            relative px-4 py-2 rounded-lg transition-all duration-300
            ${currentView === mode.id 
              ? `bg-gradient-to-r ${mode.color} text-white shadow-lg transform scale-105` 
              : 'bg-gray-800/50 text-gray-400 hover:bg-gray-800 hover:text-white hover:scale-102'
            }
          `}
          title={mode.description}
        >
          <div className="flex items-center gap-2">
            <span className="text-lg">{mode.icon}</span>
            <span className="text-sm font-medium">{mode.label}</span>
          </div>
          {currentView === mode.id && (
            <div className="absolute -bottom-1 left-1/2 transform -translate-x-1/2 w-1 h-1 bg-white rounded-full animate-pulse" />
          )}
        </button>
      ))}
    </div>
  );
}