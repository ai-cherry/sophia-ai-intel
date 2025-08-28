'use client';

import { useState, useEffect } from 'react';
import { apiClient } from '../lib/api';

interface GitHubFile {
  name: string;
  path: string;
  type: 'file' | 'dir';
  size?: number;
}

interface GitHubHealth {
  status: string;
  service: string;
  version: string;
  repo: string;
}

export default function GitHubIntegration() {
  const [health, setHealth] = useState<GitHubHealth | null>(null);
  const [files, setFiles] = useState<GitHubFile[]>([]);
  const [currentPath, setCurrentPath] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    checkHealth();
    loadDirectory('');
  }, []);

  const checkHealth = async () => {
    try {
      const response = await apiClient.getGitHubHealth();
      if (response.data) {
        setHealth(response.data);
      } else {
        setError(response.error || 'GitHub service unavailable');
      }
    } catch (err) {
      setError('Failed to connect to GitHub service');
    }
  };

  const loadDirectory = async (path: string) => {
    setLoading(true);
    setError(null);
    try {
      const response = await apiClient.getGitHubTree(path);
      if (response.data?.entries) {
        setFiles(response.data.entries);
        setCurrentPath(path);
      } else {
        setError(response.error || 'Failed to load directory');
      }
    } catch (err) {
      setError('Failed to load directory');
    } finally {
      setLoading(false);
    }
  };

  const handleFileClick = async (file: GitHubFile) => {
    if (file.type === 'dir') {
      loadDirectory(file.path);
    } else {
      try {
        const response = await apiClient.getGitHubFile(file.path);
        if (response.data) {
          // Decode base64 content
          const content = atob(response.data.content);
          alert(`File: ${file.name}\n\nContent (first 500 chars):\n${content.substring(0, 500)}...`);
        }
      } catch (err) {
        setError(`Failed to load file: ${file.name}`);
      }
    }
  };

  const goUp = () => {
    const pathParts = currentPath.split('/').filter(p => p);
    pathParts.pop();
    loadDirectory(pathParts.join('/'));
  };

  return (
    <div className="p-4 border rounded-lg bg-white">
      <div className="flex justify-between items-center mb-4">
        <h3 className="text-lg font-semibold">GitHub Integration</h3>
        <button
          onClick={checkHealth}
          className="px-3 py-1 text-sm bg-blue-600 text-white rounded-md hover:bg-blue-700"
        >
          Refresh Health
        </button>
      </div>

      {/* Health Status */}
      <div className="mb-4 p-3 bg-gray-50 rounded-md">
        <h4 className="font-medium mb-2">Service Status</h4>
        {health ? (
          <div className="text-sm">
            <div className={`inline-block px-2 py-1 rounded text-white text-xs ${
              health.status === 'healthy' ? 'bg-green-600' : 'bg-red-600'
            }`}>
              {health.status}
            </div>
            <span className="ml-2">Service: {health.service}</span>
            <span className="ml-4">Repository: {health.repo}</span>
          </div>
        ) : (
          <div className="text-red-600 text-sm">
            {error || 'Service status unknown'}
          </div>
        )}
      </div>

      {/* File Browser */}
      <div className="mb-4">
        <div className="flex items-center gap-2 mb-2">
          <span className="text-sm text-gray-600">Path:</span>
          <code className="text-sm bg-gray-100 px-2 py-1 rounded">
            /{currentPath}
          </code>
          {currentPath && (
            <button
              onClick={goUp}
              className="text-sm text-blue-600 hover:underline"
            >
              ← Up
            </button>
          )}
        </div>

        {loading ? (
          <div className="text-center py-4">
            <div className="inline-block w-4 h-4 border-2 border-blue-600 border-t-transparent rounded-full animate-spin"></div>
            <span className="ml-2 text-sm text-gray-600">Loading...</span>
          </div>
        ) : (
          <div className="border rounded-md max-h-64 overflow-y-auto">
            {files.length > 0 ? (
              files.map((file, index) => (
                <div
                  key={index}
                  className="p-2 hover:bg-gray-50 cursor-pointer border-b last:border-b-0 flex items-center gap-2"
                  onClick={() => handleFileClick(file)}
                >
                  <span className="text-lg">
                    {file.type === 'dir' ? '📁' : '📄'}
                  </span>
                  <span className="flex-1 text-sm">{file.name}</span>
                  {file.size !== undefined && (
                    <span className="text-xs text-gray-500">
                      {(file.size / 1024).toFixed(1)}KB
                    </span>
                  )}
                </div>
              ))
            ) : (
              <div className="p-4 text-center text-gray-500 text-sm">
                {error || 'No files found'}
              </div>
            )}
          </div>
        )}
      </div>

      <div className="text-xs text-gray-500">
        Click directories to navigate, click files to preview content
      </div>
    </div>
  );
}