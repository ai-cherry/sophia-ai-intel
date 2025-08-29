'use client';

import { useState, useEffect } from 'react';
import { config } from '@/lib/config';

interface Metric {
  name: string;
  value: number;
  unit: string;
  status: 'good' | 'warning' | 'critical';
}

interface PrometheusResult {
  metric: { [key: string]: string };
  value: [number, string];
}

export default function MetricsPage() {
  const [metrics, setMetrics] = useState<Metric[]>([]);
  const [promData, setPromData] = useState<PrometheusResult[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [selectedQuery, setSelectedQuery] = useState('up');
  const [customQuery, setCustomQuery] = useState('');

  const predefinedQueries = [
    { label: 'Service Health', query: 'up' },
    { label: 'Request Rate', query: 'rate(http_requests_total[5m])' },
    { label: 'Error Rate', query: 'rate(http_requests_total{status=~"5.."}[5m])' },
    { label: 'Response Time', query: 'histogram_quantile(0.95, http_request_duration_seconds_bucket)' },
    { label: 'Memory Usage', query: 'process_resident_memory_bytes' },
    { label: 'CPU Usage', query: 'rate(process_cpu_seconds_total[5m])' }
  ];

  const fetchMetrics = async (query: string) => {
    setIsLoading(true);
    setError(null);
    
    try {
      const response = await fetch(`/api/metrics?query=${encodeURIComponent(query)}`);
      if (response.ok) {
        const data = await response.json();
        
        if (data.status === 'success' && data.data?.result) {
          setPromData(data.data.result);
          
          // Convert Prometheus data to metrics
          const convertedMetrics: Metric[] = data.data.result.map((r: PrometheusResult) => {
            const value = parseFloat(r.value[1]);
            const name = r.metric.__name__ || r.metric.job || query;
            
            return {
              name,
              value,
              unit: query.includes('bytes') ? 'bytes' : query.includes('seconds') ? 's' : '',
              status: value > 0.8 ? 'critical' : value > 0.5 ? 'warning' : 'good'
            };
          });
          
          setMetrics(convertedMetrics);
        }
      } else {
        throw new Error('Failed to fetch metrics');
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch metrics');
      // Use fallback mock metrics if Prometheus is not available
      setMetrics([
        { name: 'Swarm Success Rate', value: 98.5, unit: '%', status: 'good' },
        { name: 'Average Latency', value: 142, unit: 'ms', status: 'good' },
        { name: 'Active Swarms', value: 3, unit: '', status: 'good' },
        { name: 'Memory Usage', value: 72, unit: '%', status: 'warning' },
        { name: 'CPU Usage', value: 45, unit: '%', status: 'good' },
        { name: 'Error Rate', value: 0.2, unit: '%', status: 'good' }
      ]);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchMetrics(selectedQuery);
  }, [selectedQuery]);

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'good': return 'text-green-400 border-green-500/30';
      case 'warning': return 'text-yellow-400 border-yellow-500/30';
      case 'critical': return 'text-red-400 border-red-500/30';
      default: return 'text-gray-400 border-gray-500/30';
    }
  };

  const formatValue = (value: number, unit: string): string => {
    if (unit === '%') return `${value.toFixed(1)}%`;
    if (unit === 'ms') return `${Math.round(value)}ms`;
    if (unit === 's') return `${value.toFixed(2)}s`;
    if (unit === 'bytes') {
      if (value > 1e9) return `${(value / 1e9).toFixed(2)} GB`;
      if (value > 1e6) return `${(value / 1e6).toFixed(2)} MB`;
      if (value > 1e3) return `${(value / 1e3).toFixed(2)} KB`;
      return `${value} B`;
    }
    return value.toFixed(2);
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-purple-900/20 to-gray-900 p-8">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-white">Metrics Dashboard</h1>
          <p className="text-gray-400 mt-2">System performance and monitoring</p>
        </div>

        {/* Query Selector */}
        <div className="bg-black/30 backdrop-blur rounded-xl p-6 border border-purple-500/20 mb-8">
          <div className="flex flex-col lg:flex-row gap-4">
            <div className="flex-1">
              <label className="block text-sm text-gray-400 mb-2">Predefined Queries</label>
              <div className="flex flex-wrap gap-2">
                {predefinedQueries.map((q) => (
                  <button
                    key={q.query}
                    onClick={() => setSelectedQuery(q.query)}
                    className={`px-3 py-2 rounded-lg text-sm transition ${
                      selectedQuery === q.query
                        ? 'bg-purple-600 text-white'
                        : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
                    }`}
                  >
                    {q.label}
                  </button>
                ))}
              </div>
            </div>
            
            <div className="flex-1">
              <label className="block text-sm text-gray-400 mb-2">Custom Query</label>
              <div className="flex gap-2">
                <input
                  type="text"
                  value={customQuery}
                  onChange={(e) => setCustomQuery(e.target.value)}
                  placeholder="Enter PromQL query..."
                  className="flex-1 px-4 py-2 bg-gray-800 border border-purple-500/20 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:border-purple-500"
                />
                <button
                  onClick={() => customQuery && setSelectedQuery(customQuery)}
                  disabled={!customQuery}
                  className="px-4 py-2 bg-purple-600 hover:bg-purple-700 disabled:bg-gray-700 disabled:cursor-not-allowed text-white rounded-lg transition"
                >
                  Run
                </button>
              </div>
            </div>
          </div>
        </div>

        {/* Metrics Grid */}
        {isLoading ? (
          <div className="text-center py-12">
            <div className="text-2xl text-purple-400 animate-pulse">Loading metrics...</div>
          </div>
        ) : error ? (
          <div className="bg-yellow-900/20 border border-yellow-500/30 rounded-xl p-6 mb-8">
            <div className="text-yellow-400">Note: {error}</div>
            <div className="text-sm text-gray-400 mt-2">Showing fallback metrics</div>
          </div>
        ) : null}

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 mb-8">
          {metrics.map((metric, i) => (
            <div 
              key={i} 
              className={`bg-black/30 backdrop-blur rounded-xl p-6 border ${getStatusColor(metric.status)}`}
            >
              <div className="text-sm text-gray-400 mb-2">{metric.name}</div>
              <div className="text-3xl font-bold text-white mb-4">
                {formatValue(metric.value, metric.unit)}
              </div>
              
              {/* Progress Bar */}
              {metric.unit === '%' && (
                <div className="w-full bg-gray-700 rounded-full h-2">
                  <div 
                    className={`h-full rounded-full transition-all ${
                      metric.status === 'good' ? 'bg-green-500' :
                      metric.status === 'warning' ? 'bg-yellow-500' :
                      'bg-red-500'
                    }`}
                    style={{ width: `${Math.min(metric.value, 100)}%` }}
                  />
                </div>
              )}
            </div>
          ))}
        </div>

        {/* Raw Prometheus Data */}
        {promData.length > 0 && (
          <div className="bg-black/30 backdrop-blur rounded-xl p-6 border border-purple-500/20">
            <h2 className="text-xl font-semibold text-white mb-4">Raw Query Results</h2>
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead className="bg-purple-900/20">
                  <tr>
                    <th className="text-left px-4 py-3 text-sm text-gray-300">Metric</th>
                    <th className="text-left px-4 py-3 text-sm text-gray-300">Labels</th>
                    <th className="text-left px-4 py-3 text-sm text-gray-300">Value</th>
                    <th className="text-left px-4 py-3 text-sm text-gray-300">Timestamp</th>
                  </tr>
                </thead>
                <tbody>
                  {promData.slice(0, 10).map((result, i) => (
                    <tr key={i} className="border-t border-purple-500/10">
                      <td className="px-4 py-3 text-sm text-white">
                        {result.metric.__name__ || 'unnamed'}
                      </td>
                      <td className="px-4 py-3 text-xs text-gray-400">
                        {Object.entries(result.metric)
                          .filter(([k]) => k !== '__name__')
                          .map(([k, v]) => `${k}="${v}"`)
                          .join(', ')}
                      </td>
                      <td className="px-4 py-3 text-sm text-cyan-400">
                        {parseFloat(result.value[1]).toFixed(4)}
                      </td>
                      <td className="px-4 py-3 text-xs text-gray-500">
                        {new Date(result.value[0] * 1000).toLocaleTimeString()}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
              {promData.length > 10 && (
                <div className="text-center py-2 text-sm text-gray-400">
                  Showing 10 of {promData.length} results
                </div>
              )}
            </div>
          </div>
        )}

        {/* Grafana Embed */}
        {config.monitoring.grafanaUrl && (
          <div className="bg-black/30 backdrop-blur rounded-xl p-6 border border-purple-500/20 mt-8">
            <h2 className="text-xl font-semibold text-white mb-4">Grafana Dashboard</h2>
            <div className="aspect-video bg-gray-800 rounded-lg flex items-center justify-center">
              <div className="text-center">
                <div className="text-4xl mb-4">📊</div>
                <p className="text-gray-400">Grafana Dashboard</p>
                <a 
                  href={config.monitoring.grafanaUrl}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-block mt-4 px-4 py-2 bg-purple-600 hover:bg-purple-700 text-white rounded-lg transition"
                >
                  Open in Grafana
                </a>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
