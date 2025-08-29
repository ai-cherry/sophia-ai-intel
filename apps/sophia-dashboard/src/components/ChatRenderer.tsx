/**
 * ChatRenderer - Renders chat messages with structured sections
 * NO MOCK DATA
 */

import React from 'react';

interface ChatSection {
  summary?: string;
  actions?: Array<{type: string; status: string; swarm_id?: string}>;
  research?: Array<{source: string; url: string; title?: string}>;
  plans?: any;
  code?: Array<{task: string; language: string; code: string}>;
  github?: {pr_url?: string; branch?: string};
  events?: Array<any>;
}

interface ChatRendererProps {
  content: string;
  sections?: ChatSection;
  role: 'user' | 'assistant' | 'system';
  timestamp?: Date;
}

export default function ChatRenderer({ content, sections, role, timestamp }: ChatRendererProps) {
  // If structured sections exist, render them
  if (sections && role === 'assistant') {
    return (
      <div className="space-y-3">
        {/* Summary */}
        {sections.summary && (
          <div className="text-white">{sections.summary}</div>
        )}
        
        {/* Actions */}
        {sections.actions && sections.actions.length > 0 && (
          <div className="flex flex-wrap gap-2">
            {sections.actions.map((action, i) => (
              <span key={i} className="px-3 py-1 bg-blue-600/20 text-blue-400 rounded-full text-xs">
                {action.type}: {action.status}
                {action.swarm_id && <span className="ml-1 text-gray-400">#{action.swarm_id.slice(0,8)}</span>}
              </span>
            ))}
          </div>
        )}
        
        {/* Research Citations */}
        {sections.research && sections.research.length > 0 && (
          <div className="border-l-2 border-cyan-500 pl-3 space-y-1">
            <div className="text-xs text-gray-400">Research Sources:</div>
            {sections.research.map((cite, i) => (
              <div key={i} className="text-sm">
                <a href={cite.url} target="_blank" rel="noopener noreferrer" className="text-cyan-400 hover:underline">
                  {cite.title || cite.source}
                </a>
              </div>
            ))}
          </div>
        )}
        
        {/* Plans */}
        {sections.plans && (
          <div className="bg-gray-800/30 rounded-lg p-3">
            <div className="text-xs text-gray-400 mb-2">Strategic Plans</div>
            {Object.entries(sections.plans).map(([key, plan]: [string, any]) => (
              <details key={key} className="mb-2">
                <summary className="cursor-pointer text-sm text-white">
                  {plan.approach} ({key})
                </summary>
                <div className="mt-1 pl-4 text-xs text-gray-300">
                  {plan.steps?.map((step: string, i: number) => (
                    <div key={i}>• {step}</div>
                  ))}
                </div>
              </details>
            ))}
          </div>
        )}
        
        {/* Code */}
        {sections.code && sections.code.length > 0 && (
          <div className="space-y-2">
            {sections.code.map((code, i) => (
              <div key={i} className="bg-gray-900 rounded-lg p-3">
                <div className="flex justify-between items-center mb-2">
                  <span className="text-xs text-gray-400">{code.task}</span>
                  <button 
                    onClick={() => navigator.clipboard.writeText(code.code)}
                    className="text-xs px-2 py-1 bg-gray-700 hover:bg-gray-600 rounded text-white"
                  >
                    Copy
                  </button>
                </div>
                <pre className="text-xs text-green-400 overflow-x-auto">
                  <code>{code.code}</code>
                </pre>
              </div>
            ))}
          </div>
        )}
        
        {/* GitHub PR */}
        {sections.github?.pr_url && (
          <div className="inline-flex items-center gap-2 px-3 py-1 bg-green-600/20 rounded-lg">
            <span className="text-green-400">✓ PR Created:</span>
            <a href={sections.github.pr_url} target="_blank" rel="noopener noreferrer" className="text-cyan-400 hover:underline">
              {sections.github.pr_url.split('/').pop()}
            </a>
          </div>
        )}
      </div>
    );
  }
  
  // Default text rendering
  return (
    <div className="whitespace-pre-wrap text-white">
      {content}
    </div>
  );
}
