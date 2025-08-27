'use client';

import { useState, useEffect } from 'react';

// Mock interfaces and API for now
interface JobStatus {
  id: string;
  type: 'reindex' | 'knowledge_sync' | 'eval_run' | 'canary_check';
  status: 'queued' | 'running' | 'completed' | 'failed';
  started_at: string;
  completed_at?: string;
  progress: number;
}

export default function JobsPanel() {
  const [activeJobs, setActiveJobs] = useState<JobStatus[]>([]);
  const [jobHistory, setJobHistory] = useState<JobStatus[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [selectedJobType, setSelectedJobType] = useState<JobStatus['type']>('reindex');

  const fetchJobStatus = async () => {
    // MOCK DATA
    setActiveJobs([
      { id: '1', type: 'reindex', status: 'running', started_at: new Date().toISOString(), progress: 50 },
      { id: '2', type: 'knowledge_sync', status: 'queued', started_at: new Date().toISOString(), progress: 0 },
    ]);
    setJobHistory([
        { id: '3', type: 'reindex', status: 'completed', started_at: new Date().toISOString(), completed_at: new Date().toISOString(), progress: 100 },
        { id: '4', type: 'eval_run', status: 'failed', started_at: new Date().toISOString(), completed_at: new Date().toISOString(), progress: 100 },
      ]);
  };

  useEffect(() => {
    fetchJobStatus();
    const interval = setInterval(fetchJobStatus, 5000);
    return () => clearInterval(interval);
  }, []);

  const runJobNow = async () => {
    setIsLoading(true);
    setError(null);
    try {
      // Simulate API call
      await new Promise(resolve => setTimeout(resolve, 1000));
      alert(`Job "${selectedJobType}" started!`);
    } catch (err) {
      setError(`Failed to start job: ${err instanceof Error ? err.message : 'Unknown error'}`);
    } finally {
      setIsLoading(false);
    }
  };

  const getStatusColor = (status: JobStatus['status']) => {
    switch (status) {
      case 'queued': return 'bg-gray-500';
      case 'running': return 'bg-blue-500';
      case 'completed': return 'bg-green-500';
      case 'failed': return 'bg-red-500';
    }
  };

  return (
    <div className="p-6 bg-white rounded-lg shadow-md">
      <div className="flex justify-between items-center mb-6 pb-4 border-b">
        <h3 className="text-xl font-bold">🔧 Jobs Management</h3>
        <div className="flex gap-2 items-center">
          <select
            value={selectedJobType}
            onChange={(e) => setSelectedJobType(e.target.value as JobStatus['type'])}
            className="p-2 border rounded-md text-sm"
          >
            <option value="reindex">🔄 Reindex Symbols</option>
            <option value="knowledge_sync">📚 Knowledge Sync</option>
            <option value="eval_run">🧪 Eval Run</option>
            <option value="canary_check">🐤 Canary Check</option>
          </select>
          <button
            onClick={runJobNow}
            disabled={isLoading}
            className="px-4 py-2 font-semibold text-white bg-blue-600 rounded-md disabled:bg-gray-400"
          >
            {isLoading ? 'Starting...' : '▶️ Run Now'}
          </button>
        </div>
      </div>

      {error && (
        <div className="p-4 mb-4 text-red-800 bg-red-100 border border-red-200 rounded-md">
          <strong>Error:</strong> {error}
        </div>
      )}

      <div>
        <h4 className="font-semibold mb-3">Active Jobs ({activeJobs.length})</h4>
        <div className="space-y-3">
          {activeJobs.map(job => (
            <div key={job.id} className="p-3 bg-gray-50 rounded-md border">
              <div className="flex justify-between items-center">
                <span className="font-semibold">{job.type.replace('_', ' ')}</span>
                <span className={`px-2 py-1 text-xs text-white rounded-full ${getStatusColor(job.status)}`}>
                  {job.status}
                </span>
              </div>
              {job.status === 'running' && (
                <div className="mt-2 h-2 bg-gray-200 rounded-full">
                  <div
                    className="h-full bg-blue-500 rounded-full"
                    style={{ width: `${job.progress}%` }}
                  />
                </div>
              )}
            </div>
          ))}
        </div>
      </div>

      <div className="mt-6">
        <h4 className="font-semibold mb-3">Job History ({jobHistory.length})</h4>
        <div className="space-y-2 text-sm text-gray-600">
          {jobHistory.map(job => (
            <div key={job.id} className="flex justify-between p-2 rounded-md bg-gray-50 border">
              <span>{job.type.replace('_', ' ')}</span>
              <span className={`font-semibold ${job.status === 'completed' ? 'text-green-600' : 'text-red-600'}`}>
                {job.status}
              </span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}