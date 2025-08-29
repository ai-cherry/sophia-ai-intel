'use client';

import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import ActivityFeed from './ActivityFeed';

interface ContextPanelProps {
  mode: 'activity' | 'code' | 'research' | 'agents';
  data?: any;
}

export default function ContextPanel({ mode, data }: ContextPanelProps) {
  const [activeTab, setActiveTab] = useState(mode);
  const [agents, setAgents] = useState<any[]>([]);
  const [codeFiles, setCodeFiles] = useState<any[]>([]);
  const [researchResults, setResearchResults] = useState<any[]>([]);

  useEffect(() => {
    setActiveTab(mode);
  }, [mode]);

  // Connect to WebSocket for real-time updates
  useEffect(() => {
    const ws = new WebSocket('ws://localhost:8096/ws/context');
    
    ws.onopen = () => {
      console.log('Context panel connected to WebSocket');
      ws.send(JSON.stringify({ type: 'subscribe', channels: ['agents', 'code', 'research'] }));
    };

    ws.onmessage = (event) => {
      try {
        const message = JSON.parse(event.data);
        
        if (message.type === 'agent_update') {
          setAgents(prev => {
            const index = prev.findIndex(a => a.id === message.agent.id);
            if (index >= 0) {
              const updated = [...prev];
              updated[index] = message.agent;
              return updated;
            }
            return [...prev, message.agent];
          });
        }
        
        if (message.type === 'code_generated') {
          setCodeFiles(prev => [...prev, ...message.files]);
        }
        
        if (message.type === 'research_result') {
          setResearchResults(prev => [...prev, message.result]);
        }
      } catch (error) {
        console.error('Failed to parse WebSocket message:', error);
      }
    };

    return () => {
      if (ws.readyState === WebSocket.OPEN) {
        ws.close();
      }
    };
  }, []);

  const renderAgentCard = (agent: any) => (
    <motion.div
      key={agent.id}
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="p-4 bg-gray-800/50 rounded-lg border border-white/10 hover:border-cyan-500/30 transition-all"
    >
      <div className="flex items-start justify-between mb-3">
        <div className="flex items-center gap-2">
          <span className="text-2xl">{agent.icon || '🤖'}</span>
          <div>
            <h4 className="text-sm font-semibold text-white">{agent.name || agent.type}</h4>
            <p className="text-xs text-gray-400">{agent.id?.slice(0, 8)}...</p>
          </div>
        </div>
        <span className={`
          px-2 py-1 text-xs rounded-full
          ${agent.status === 'active' ? 'bg-green-500/20 text-green-400' : 
            agent.status === 'idle' ? 'bg-yellow-500/20 text-yellow-400' :
            'bg-gray-500/20 text-gray-400'}
        `}>
          {agent.status}
        </span>
      </div>
      
      {agent.currentTask && (
        <div className="mb-3">
          <p className="text-xs text-gray-400 mb-1">Current Task:</p>
          <p className="text-sm text-white">{agent.currentTask}</p>
        </div>
      )}
      
      {agent.progress !== undefined && (
        <div>
          <div className="flex justify-between text-xs text-gray-400 mb-1">
            <span>Progress</span>
            <span>{agent.progress}%</span>
          </div>
          <div className="w-full bg-gray-700 rounded-full h-1.5">
            <motion.div 
              initial={{ width: 0 }}
              animate={{ width: `${agent.progress}%` }}
              className="bg-gradient-to-r from-cyan-500 to-purple-500 h-1.5 rounded-full"
            />
          </div>
        </div>
      )}
    </motion.div>
  );

  const renderCodeFile = (file: any) => (
    <motion.div
      key={file.path}
      initial={{ opacity: 0, x: -20 }}
      animate={{ opacity: 1, x: 0 }}
      className="p-3 bg-gray-800/30 rounded-lg border border-white/5 hover:bg-gray-800/50 hover:border-cyan-500/30 transition-all cursor-pointer"
    >
      <div className="flex items-center gap-2">
        <span className="text-lg">📄</span>
        <div className="flex-1">
          <p className="text-sm text-white font-mono">{file.name}</p>
          <p className="text-xs text-gray-500">{file.path}</p>
        </div>
        <span className="text-xs text-gray-400">{file.lines} lines</span>
      </div>
    </motion.div>
  );

  const renderResearchCard = (result: any) => (
    <motion.div
      key={result.id}
      initial={{ opacity: 0, scale: 0.95 }}
      animate={{ opacity: 1, scale: 1 }}
      className="p-4 bg-gray-800/50 rounded-lg border border-white/10 hover:border-cyan-500/30 transition-all"
    >
      <h4 className="text-sm font-semibold text-white mb-2">{result.title}</h4>
      <p className="text-xs text-gray-400 mb-3 line-clamp-3">{result.summary}</p>
      <div className="flex items-center justify-between">
        <span className="text-xs px-2 py-1 bg-cyan-600/20 text-cyan-400 rounded">
          {result.source}
        </span>
        <button className="text-xs text-cyan-400 hover:text-cyan-300 transition-colors">
          View →
        </button>
      </div>
    </motion.div>
  );

  return (
    <div className="h-full flex flex-col">
      {/* Header with Tabs */}
      <div className="p-4 border-b border-white/10">
        <div className="flex gap-2">
          {[
            { id: 'activity', label: 'Activity', icon: '📊' },
            { id: 'agents', label: 'Agents', icon: '🤖', count: agents.length },
            { id: 'code', label: 'Code', icon: '💻', count: codeFiles.length },
            { id: 'research', label: 'Research', icon: '🔍', count: researchResults.length }
          ].map(tab => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id as any)}
              className={`
                flex items-center gap-2 px-3 py-1.5 rounded-lg text-sm transition-all
                ${activeTab === tab.id 
                  ? 'bg-cyan-600/20 text-cyan-400 border border-cyan-600/30' 
                  : 'text-gray-400 hover:text-white hover:bg-white/5'
                }
              `}
            >
              <span>{tab.icon}</span>
              <span>{tab.label}</span>
              {tab.count !== undefined && tab.count > 0 && (
                <span className="ml-1 px-1.5 py-0.5 bg-gray-700 rounded text-xs">
                  {tab.count}
                </span>
              )}
            </button>
          ))}
        </div>
      </div>

      {/* Content Area */}
      <div className="flex-1 overflow-y-auto p-4">
        <AnimatePresence mode="wait">
          {activeTab === 'activity' && (
            <motion.div
              key="activity"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="h-full"
            >
              <ActivityFeed />
            </motion.div>
          )}

          {activeTab === 'agents' && (
            <motion.div
              key="agents"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="space-y-3"
            >
              {agents.length === 0 ? (
                <div className="text-center py-8">
                  <div className="text-4xl mb-3 opacity-20">🤖</div>
                  <p className="text-gray-500 text-sm">No active agents</p>
                  <p className="text-gray-600 text-xs mt-1">Deploy agents to see them here</p>
                </div>
              ) : (
                agents.map(renderAgentCard)
              )}
            </motion.div>
          )}

          {activeTab === 'code' && (
            <motion.div
              key="code"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="space-y-2"
            >
              {codeFiles.length === 0 ? (
                <div className="text-center py-8">
                  <div className="text-4xl mb-3 opacity-20">💻</div>
                  <p className="text-gray-500 text-sm">No code generated yet</p>
                  <p className="text-gray-600 text-xs mt-1">Generate code to see files here</p>
                </div>
              ) : (
                codeFiles.map(renderCodeFile)
              )}
            </motion.div>
          )}

          {activeTab === 'research' && (
            <motion.div
              key="research"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="space-y-3"
            >
              {researchResults.length === 0 ? (
                <div className="text-center py-8">
                  <div className="text-4xl mb-3 opacity-20">🔍</div>
                  <p className="text-gray-500 text-sm">No research results</p>
                  <p className="text-gray-600 text-xs mt-1">Start a research task to see results</p>
                </div>
              ) : (
                researchResults.map(renderResearchCard)
              )}
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </div>
  );
}