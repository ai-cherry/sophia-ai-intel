'use client';

import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';

interface NavItem {
  id: string;
  label: string;
  icon: string;
  shortcut?: string;
  section: 'primary' | 'system' | 'user';
}

interface NavigationRailProps {
  collapsed: boolean;
  onToggle: () => void;
  activeView: string;
  onViewChange: (view: string) => void;
}

const navItems: NavItem[] = [
  // Primary Actions
  { id: 'chat', label: 'Chat', icon: '💬', shortcut: 'Cmd+1', section: 'primary' },
  { id: 'agents', label: 'Agents', icon: '🤖', shortcut: 'Cmd+2', section: 'primary' },
  { id: 'code', label: 'Code', icon: '💻', shortcut: 'Cmd+3', section: 'primary' },
  { id: 'research', label: 'Research', icon: '🔍', shortcut: 'Cmd+4', section: 'primary' },
  { id: 'swarm', label: 'Swarm', icon: '🐝', shortcut: 'Cmd+5', section: 'primary' },
  
  // System
  { id: 'metrics', label: 'Metrics', icon: '📊', section: 'system' },
  { id: 'logs', label: 'Logs', icon: '📝', section: 'system' },
  { id: 'settings', label: 'Settings', icon: '⚙️', section: 'system' },
  
  // User
  { id: 'profile', label: 'Profile', icon: '👤', section: 'user' },
  { id: 'help', label: 'Help', icon: '❓', section: 'user' },
];

export default function NavigationRail({ collapsed, onToggle, activeView, onViewChange }: NavigationRailProps) {
  const [hoveredItem, setHoveredItem] = useState<string | null>(null);
  
  const width = collapsed ? 80 : 240;
  
  const renderNavItem = (item: NavItem) => {
    const isActive = activeView === item.id;
    const isHovered = hoveredItem === item.id;
    
    return (
      <motion.button
        key={item.id}
        onClick={() => onViewChange(item.id)}
        onMouseEnter={() => setHoveredItem(item.id)}
        onMouseLeave={() => setHoveredItem(null)}
        className={`
          relative w-full flex items-center gap-3 px-4 py-3 
          transition-all duration-200 rounded-lg
          ${isActive 
            ? 'bg-gradient-to-r from-cyan-600/20 to-purple-600/20 text-white border border-cyan-500/30' 
            : 'text-gray-400 hover:text-white hover:bg-white/5'
          }
        `}
        whileHover={{ x: collapsed ? 0 : 4 }}
        whileTap={{ scale: 0.98 }}
      >
        <span className="text-xl flex-shrink-0">{item.icon}</span>
        
        <AnimatePresence>
          {!collapsed && (
            <motion.div
              initial={{ opacity: 0, width: 0 }}
              animate={{ opacity: 1, width: 'auto' }}
              exit={{ opacity: 0, width: 0 }}
              className="flex-1 flex items-center justify-between overflow-hidden"
            >
              <span className="text-sm font-medium whitespace-nowrap">{item.label}</span>
              {item.shortcut && (
                <span className="text-xs text-gray-500 ml-2">{item.shortcut}</span>
              )}
            </motion.div>
          )}
        </AnimatePresence>
        
        {/* Tooltip for collapsed state */}
        {collapsed && isHovered && (
          <div className="absolute left-full ml-2 px-2 py-1 bg-gray-900 text-white text-xs rounded whitespace-nowrap z-50 pointer-events-none">
            {item.label}
            {item.shortcut && <span className="ml-2 text-gray-400">{item.shortcut}</span>}
          </div>
        )}
        
        {/* Active indicator */}
        {isActive && (
          <motion.div
            layoutId="activeIndicator"
            className="absolute left-0 w-1 h-8 bg-gradient-to-b from-cyan-400 to-purple-600 rounded-r"
          />
        )}
      </motion.button>
    );
  };
  
  return (
    <motion.nav
      animate={{ width }}
      transition={{ duration: 0.3, ease: 'easeInOut' }}
      className="relative flex flex-col h-full bg-gradient-to-b from-gray-900 via-gray-900/95 to-gray-950 border-r border-white/10"
    >
      {/* Header */}
      <div className="p-4 border-b border-white/10">
        <button
          onClick={onToggle}
          className="w-full flex items-center gap-3 group"
        >
          <div className="relative w-10 h-10 rounded-xl overflow-hidden flex-shrink-0">
            <div className="absolute inset-0 bg-gradient-to-br from-cyan-500 to-purple-600" />
            <div className="absolute inset-0 flex items-center justify-center text-white font-bold text-lg">
              S
            </div>
          </div>
          
          <AnimatePresence>
            {!collapsed && (
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                className="flex-1"
              >
                <h1 className="text-white font-bold text-lg">Sophia AI</h1>
                <p className="text-xs text-cyan-400/80">Command Center</p>
              </motion.div>
            )}
          </AnimatePresence>
          
          <AnimatePresence>
            {!collapsed && (
              <motion.div
                initial={{ opacity: 0, rotate: 180 }}
                animate={{ opacity: 1, rotate: 0 }}
                exit={{ opacity: 0, rotate: 180 }}
                className="text-gray-400 group-hover:text-white transition-colors"
              >
                ←
              </motion.div>
            )}
          </AnimatePresence>
        </button>
      </div>
      
      {/* Navigation Items */}
      <div className="flex-1 overflow-y-auto py-4 px-2 space-y-6">
        {/* Primary Section */}
        <div>
          {!collapsed && (
            <div className="px-4 mb-2 text-xs font-semibold text-gray-500 uppercase">
              Primary
            </div>
          )}
          <div className="space-y-1">
            {navItems.filter(item => item.section === 'primary').map(renderNavItem)}
          </div>
        </div>
        
        {/* System Section */}
        <div>
          {!collapsed && (
            <div className="px-4 mb-2 text-xs font-semibold text-gray-500 uppercase">
              System
            </div>
          )}
          <div className="space-y-1">
            {navItems.filter(item => item.section === 'system').map(renderNavItem)}
          </div>
        </div>
      </div>
      
      {/* Footer */}
      <div className="p-4 border-t border-white/10">
        <div className="space-y-2">
          {navItems.filter(item => item.section === 'user').map(renderNavItem)}
        </div>
        
        {/* Status Indicator */}
        <div className="mt-4 flex items-center gap-2">
          <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse" />
          {!collapsed && (
            <span className="text-xs text-gray-400">All Systems Operational</span>
          )}
        </div>
      </div>
    </motion.nav>
  );
}