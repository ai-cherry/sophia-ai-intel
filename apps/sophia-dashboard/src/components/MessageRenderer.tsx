'use client';

import { useEffect, useRef } from 'react';

interface MessageRendererProps {
  content: string;
  role: 'user' | 'assistant' | 'system';
}

export default function MessageRenderer({ content, role }: MessageRendererProps) {
  const codeBlockRef = useRef<HTMLDivElement>(null);

  // Parse markdown-style formatting
  const renderContent = (text: string) => {
    // Handle code blocks
    const codeBlockRegex = /```(\w+)?\n([\s\S]*?)```/g;
    const parts = [];
    let lastIndex = 0;
    let match;

    while ((match = codeBlockRegex.exec(text)) !== null) {
      // Add text before code block
      if (match.index > lastIndex) {
        parts.push({
          type: 'text',
          content: text.slice(lastIndex, match.index)
        });
      }

      // Add code block
      parts.push({
        type: 'code',
        language: match[1] || 'plaintext',
        content: match[2].trim()
      });

      lastIndex = match.index + match[0].length;
    }

    // Add remaining text
    if (lastIndex < text.length) {
      parts.push({
        type: 'text',
        content: text.slice(lastIndex)
      });
    }

    // If no code blocks found, treat entire content as text
    if (parts.length === 0) {
      parts.push({ type: 'text', content: text });
    }

    return parts;
  };

  const formatText = (text: string) => {
    // Handle inline code
    text = text.replace(/`([^`]+)`/g, '<code class="inline-code">$1</code>');
    
    // Handle bold
    text = text.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>');
    
    // Handle italic
    text = text.replace(/\*([^*]+)\*/g, '<em>$1</em>');
    
    // Handle headers
    text = text.replace(/^### (.+)$/gm, '<h3 class="text-lg font-bold mt-4 mb-2">$1</h3>');
    text = text.replace(/^## (.+)$/gm, '<h2 class="text-xl font-bold mt-4 mb-2">$1</h2>');
    text = text.replace(/^# (.+)$/gm, '<h1 class="text-2xl font-bold mt-4 mb-2">$1</h1>');
    
    // Handle bullet points
    text = text.replace(/^• (.+)$/gm, '<li class="ml-4">$1</li>');
    text = text.replace(/^- (.+)$/gm, '<li class="ml-4">$1</li>');
    text = text.replace(/^\* (.+)$/gm, '<li class="ml-4">$1</li>');
    text = text.replace(/^(\d+)\. (.+)$/gm, '<li class="ml-4"><span class="font-semibold">$1.</span> $2</li>');
    
    // Wrap consecutive list items in ul
    text = text.replace(/(<li[^>]*>.*?<\/li>\n?)+/g, '<ul class="list-disc list-inside my-2">$&</ul>');
    
    // Handle line breaks
    text = text.replace(/\n/g, '<br />');
    
    // Handle links
    text = text.replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2" target="_blank" class="text-cyan-400 hover:text-cyan-300 underline">$1</a>');
    
    return text;
  };

  const renderParts = () => {
    const parts = renderContent(content);
    
    return parts.map((part, index) => {
      if (part.type === 'code') {
        return (
          <div key={index} className="my-3">
            <div className="bg-gray-900 rounded-lg overflow-hidden border border-gray-700">
              <div className="flex items-center justify-between px-3 py-2 bg-gray-800 border-b border-gray-700">
                <span className="text-xs text-gray-400 font-mono">{part.language}</span>
                <button
                  onClick={() => {
                    navigator.clipboard.writeText(part.content || '');
                    // Show toast or feedback
                  }}
                  className="text-xs px-2 py-1 bg-gray-700 hover:bg-gray-600 text-gray-300 rounded transition-colors"
                >
                  Copy
                </button>
              </div>
              <pre className="p-4 overflow-x-auto">
                <code className={`language-${part.language} text-sm text-gray-300 font-mono`}>
                  {part.content}
                </code>
              </pre>
            </div>
          </div>
        );
      } else {
        return (
          <div 
            key={index}
            className="prose prose-invert max-w-none"
            dangerouslySetInnerHTML={{ __html: formatText(part.content || '') }}
          />
        );
      }
    });
  };

  return (
    <div className={`message-content ${role}-content`}>
      {/* Special formatting for system messages */}
      {role === 'system' && (
        <div className="flex items-center gap-2 mb-2">
          <span className="text-xs px-2 py-1 bg-yellow-500/20 text-yellow-400 rounded">System</span>
        </div>
      )}
      
      {/* Render formatted content */}
      <div className="message-text-formatted">
        {renderParts()}
      </div>
      
      {/* Add styling for different message types */}
      <style jsx global>{`
        .inline-code {
          background: rgba(0, 255, 204, 0.1);
          color: #00ffcc;
          padding: 2px 6px;
          border-radius: 4px;
          font-family: 'Monaco', 'Courier New', monospace;
          font-size: 0.9em;
        }
        
        .user-content {
          color: white;
        }
        
        .assistant-content {
          color: #e5e7eb;
        }
        
        .system-content {
          color: #fbbf24;
          font-style: italic;
        }
        
        .message-text-formatted strong {
          color: #00ffcc;
          font-weight: 600;
        }
        
        .message-text-formatted em {
          color: #a78bfa;
        }
        
        .message-text-formatted h1,
        .message-text-formatted h2,
        .message-text-formatted h3 {
          color: white;
          margin-top: 1rem;
          margin-bottom: 0.5rem;
        }
        
        .message-text-formatted ul {
          margin: 0.5rem 0;
        }
        
        .message-text-formatted li {
          margin: 0.25rem 0;
        }
        
        .message-text-formatted a {
          transition: color 0.2s;
        }
      `}</style>
    </div>
  );
}