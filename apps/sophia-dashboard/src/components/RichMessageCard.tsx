'use client';

import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { vscDarkPlus } from 'react-syntax-highlighter/dist/esm/styles/prism';

interface MessageMetadata {
  actions?: string[];
  services?: string[];
  research?: any[];
  code?: any[];
  plans?: any;
  agents?: any[];
  github_pr?: any;
}

interface Message {
  id: string;
  role: 'user' | 'assistant' | 'agent' | 'system';
  content: string;
  metadata?: MessageMetadata;
  timestamp: Date;
  status?: 'pending' | 'streaming' | 'complete' | 'error';
}

interface RichMessageCardProps {
  message: Message;
  isStreaming?: boolean;
}

export default function RichMessageCard({ message, isStreaming }: RichMessageCardProps) {
  const [expandedSections, setExpandedSections] = useState<Set<string>>(new Set());
  const [copiedCode, setCopiedCode] = useState<string | null>(null);

  const toggleSection = (section: string) => {
    setExpandedSections(prev => {
      const newSet = new Set(prev);
      if (newSet.has(section)) {
        newSet.delete(section);
      } else {
        newSet.add(section);
      }
      return newSet;
    });
  };

  const copyToClipboard = async (text: string, id: string) => {
    await navigator.clipboard.writeText(text);
    setCopiedCode(id);
    setTimeout(() => setCopiedCode(null), 2000);
  };

  const roleConfig = {
    user: {
      bg: 'bg-gradient-to-r from-blue-900/20 to-purple-900/20',
      border: 'border-blue-500/20',
      icon: '👤',
      label: 'You'
    },
    assistant: {
      bg: 'bg-gradient-to-r from-cyan-900/20 to-teal-900/20',
      border: 'border-cyan-500/20',
      icon: '🤖',
      label: 'Sophia'
    },
    agent: {
      bg: 'bg-gradient-to-r from-purple-900/20 to-pink-900/20',
      border: 'border-purple-500/20',
      icon: '🐝',
      label: 'Agent'
    },
    system: {
      bg: 'bg-gradient-to-r from-yellow-900/20 to-orange-900/20',
      border: 'border-yellow-500/20',
      icon: '⚙️',
      label: 'System'
    }
  };

  const config = roleConfig[message.role];

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className={`
        relative p-4 rounded-xl border ${config.border} ${config.bg}
        backdrop-blur-sm transition-all duration-200
        hover:shadow-lg hover:shadow-cyan-500/5
      `}
    >
      {/* Header */}
      <div className="flex items-start justify-between mb-3">
        <div className="flex items-center gap-3">
          <span className="text-2xl">{config.icon}</span>
          <div>
            <span className="text-sm font-semibold text-white">{config.label}</span>
            <span className="ml-2 text-xs text-gray-500">
              {message.timestamp.toLocaleTimeString()}
            </span>
          </div>
        </div>
        
        {message.status && (
          <span className={`
            px-2 py-1 text-xs rounded-full
            ${message.status === 'streaming' ? 'bg-yellow-500/20 text-yellow-400 animate-pulse' :
              message.status === 'complete' ? 'bg-green-500/20 text-green-400' :
              message.status === 'error' ? 'bg-red-500/20 text-red-400' :
              'bg-gray-500/20 text-gray-400'}
          `}>
            {message.status}
          </span>
        )}
      </div>

      {/* Main Content with Markdown */}
      <div className="prose prose-invert prose-sm max-w-none">
        <ReactMarkdown
          remarkPlugins={[remarkGfm]}
          components={{
            code({ node, inline, className, children, ...props }: any) {
              const match = /language-(\w+)/.exec(className || '');
              const language = match ? match[1] : '';
              const codeId = `code-${message.id}-${Math.random()}`;
              
              if (!inline && language) {
                return (
                  <div className="relative my-3">
                    <div className="flex items-center justify-between px-3 py-2 bg-gray-800 rounded-t-lg border-b border-gray-700">
                      <span className="text-xs text-gray-400 font-mono">{language}</span>
                      <button
                        onClick={() => copyToClipboard(String(children), codeId)}
                        className="text-xs px-2 py-1 bg-gray-700 hover:bg-gray-600 text-gray-300 rounded transition-colors"
                      >
                        {copiedCode === codeId ? 'Copied!' : 'Copy'}
                      </button>
                    </div>
                    <SyntaxHighlighter
                      language={language}
                      style={vscDarkPlus}
                      customStyle={{
                        margin: 0,
                        borderRadius: '0 0 0.5rem 0.5rem',
                        fontSize: '0.875rem'
                      }}
                      {...props}
                    >
                      {String(children).replace(/\n$/, '')}
                    </SyntaxHighlighter>
                  </div>
                );
              }
              
              return (
                <code className="px-1.5 py-0.5 bg-gray-800 text-cyan-400 rounded text-sm" {...props}>
                  {children}
                </code>
              );
            },
            a({ href, children }: any) {
              return (
                <a 
                  href={href} 
                  target="_blank" 
                  rel="noopener noreferrer"
                  className="text-cyan-400 hover:text-cyan-300 underline transition-colors"
                >
                  {children}
                </a>
              );
            }
          }}
        >
          {message.content}
        </ReactMarkdown>
      </div>

      {/* Streaming Indicator */}
      {isStreaming && (
        <div className="mt-3 flex items-center gap-2">
          <div className="flex gap-1">
            <span className="w-2 h-2 bg-cyan-400 rounded-full animate-bounce" />
            <span className="w-2 h-2 bg-cyan-400 rounded-full animate-bounce" style={{ animationDelay: '0.1s' }} />
            <span className="w-2 h-2 bg-cyan-400 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }} />
          </div>
          <span className="text-xs text-gray-400">Generating...</span>
        </div>
      )}

      {/* Metadata Sections */}
      {message.metadata && (
        <div className="mt-4 space-y-3">
          {/* Actions */}
          {message.metadata.actions && message.metadata.actions.length > 0 && (
            <div className="flex flex-wrap gap-2">
              {message.metadata.actions.map((action, idx) => (
                <span key={idx} className="px-2 py-1 bg-blue-500/20 text-blue-400 text-xs rounded-full">
                  {action}
                </span>
              ))}
            </div>
          )}

          {/* Services */}
          {message.metadata.services && message.metadata.services.length > 0 && (
            <div className="flex flex-wrap gap-2">
              {message.metadata.services.map((service, idx) => (
                <span key={idx} className="px-2 py-1 bg-green-500/20 text-green-400 text-xs rounded-full">
                  {service}
                </span>
              ))}
            </div>
          )}

          {/* Plans */}
          {message.metadata.plans && (
            <div className="border-t border-white/10 pt-3">
              <button
                onClick={() => toggleSection('plans')}
                className="flex items-center gap-2 text-sm font-semibold text-white hover:text-cyan-400 transition-colors"
              >
                <span className={`transform transition-transform ${expandedSections.has('plans') ? 'rotate-90' : ''}`}>
                  ▶
                </span>
                Strategic Plans Generated
              </button>
              
              <AnimatePresence>
                {expandedSections.has('plans') && (
                  <motion.div
                    initial={{ height: 0, opacity: 0 }}
                    animate={{ height: 'auto', opacity: 1 }}
                    exit={{ height: 0, opacity: 0 }}
                    className="mt-3 grid grid-cols-3 gap-3 overflow-hidden"
                  >
                    {Object.entries(message.metadata.plans).map(([key, plan]: [string, any]) => (
                      <div key={key} className="p-3 bg-gray-800/50 rounded-lg border border-white/10">
                        <h4 className="text-sm font-semibold text-white mb-2 capitalize">
                          {key.replace('_', ' ')}
                        </h4>
                        <p className="text-xs text-gray-400">{plan.philosophy || plan.approach}</p>
                      </div>
                    ))}
                  </motion.div>
                )}
              </AnimatePresence>
            </div>
          )}

          {/* GitHub PR */}
          {message.metadata.github_pr && (
            <div className="p-3 bg-green-900/20 border border-green-500/30 rounded-lg">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <span className="text-lg">🎉</span>
                  <span className="text-sm text-white font-semibold">Pull Request Created</span>
                </div>
                <a
                  href={message.metadata.github_pr.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-sm text-green-400 hover:text-green-300 transition-colors"
                >
                  View PR →
                </a>
              </div>
            </div>
          )}
        </div>
      )}
    </motion.div>
  );
}