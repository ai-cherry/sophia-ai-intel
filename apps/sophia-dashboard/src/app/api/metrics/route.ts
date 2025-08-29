import { NextRequest, NextResponse } from 'next/server';

// Prometheus endpoint (configurable via env or fallback to local)
const PROMETHEUS_URL = process.env.PROMETHEUS_URL || 'http://localhost:9090';

interface PrometheusQueryResponse {
  status: 'success' | 'error';
  data?: {
    resultType: string;
    result: Array<{
      metric: Record<string, string>;
      value?: [number, string];  // instant query
      values?: Array<[number, string]>;  // range query
    }>;
  };
  errorType?: string;
  error?: string;
}

interface PrometheusTargetsResponse {
  status: 'success' | 'error';
  data?: {
    activeTargets: Array<{
      discoveredLabels: Record<string, string>;
      labels: Record<string, string>;
      scrapePool: string;
      scrapeUrl: string;
      globalUrl: string;
      lastError: string;
      lastScrape: string;
      lastScrapeDuration: number;
      health: 'up' | 'down' | 'unknown';
    }>;
  };
}

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const { query, start, end, step, time } = body;

    if (!query) {
      return NextResponse.json(
        { error: 'Query parameter is required' },
        { status: 400 }
      );
    }

    // Determine query type and build URL
    let url: string;
    const params = new URLSearchParams();
    params.append('query', query);

    if (start && end) {
      // Range query
      url = `${PROMETHEUS_URL}/api/v1/query_range`;
      params.append('start', start);
      params.append('end', end);
      if (step) params.append('step', step);
    } else {
      // Instant query
      url = `${PROMETHEUS_URL}/api/v1/query`;
      if (time) params.append('time', time);
    }

    // Execute Prometheus query
    const response = await fetch(`${url}?${params.toString()}`, {
      method: 'GET',
      headers: {
        'Accept': 'application/json',
      },
      signal: AbortSignal.timeout(10000), // 10s timeout
    });

    if (!response.ok) {
      throw new Error(`Prometheus returned ${response.status}: ${response.statusText}`);
    }

    const data: PrometheusQueryResponse = await response.json();

    if (data.status === 'error') {
      return NextResponse.json(
        { 
          error: data.error || 'Query failed',
          errorType: data.errorType 
        },
        { status: 400 }
      );
    }

    // Transform and return results
    return NextResponse.json({
      status: 'success',
      resultType: data.data?.resultType,
      results: data.data?.result || [],
    });

  } catch (error) {
    console.error('Prometheus query error:', error);
    
    // If Prometheus is unavailable, return fallback metrics
    if (error instanceof Error && (error.message.includes('ECONNREFUSED') || error.message.includes('fetch failed'))) {
      const body = await request.json().catch(() => ({ query: '' }));
      return NextResponse.json({
        status: 'fallback',
        message: 'Prometheus unavailable, returning simulated metrics',
        results: generateFallbackMetrics(body.query || ''),
      });
    }

    return NextResponse.json(
      { 
        error: error instanceof Error ? error.message : 'Failed to query Prometheus',
        status: 'error' 
      },
      { status: 500 }
    );
  }
}

export async function GET(request: NextRequest) {
  try {
    const { searchParams } = new URL(request.url);
    const target = searchParams.get('target');

    if (target === 'health') {
      // Check Prometheus health
      const response = await fetch(`${PROMETHEUS_URL}/-/healthy`, {
        signal: AbortSignal.timeout(5000),
      });

      return NextResponse.json({
        status: response.ok ? 'healthy' : 'unhealthy',
        prometheus_url: PROMETHEUS_URL,
        timestamp: new Date().toISOString(),
      });
    }

    if (target === 'targets') {
      // Get scrape targets
      const response = await fetch(`${PROMETHEUS_URL}/api/v1/targets`, {
        headers: { 'Accept': 'application/json' },
        signal: AbortSignal.timeout(5000),
      });

      if (!response.ok) {
        throw new Error(`Failed to fetch targets: ${response.statusText}`);
      }

      const data: PrometheusTargetsResponse = await response.json();
      
      return NextResponse.json({
        status: 'success',
        targets: data.data?.activeTargets || [],
        summary: {
          total: data.data?.activeTargets.length || 0,
          up: data.data?.activeTargets.filter(t => t.health === 'up').length || 0,
          down: data.data?.activeTargets.filter(t => t.health === 'down').length || 0,
        },
      });
    }

    // Default: return available metrics
    const response = await fetch(`${PROMETHEUS_URL}/api/v1/label/__name__/values`, {
      headers: { 'Accept': 'application/json' },
      signal: AbortSignal.timeout(5000),
    });

    if (!response.ok) {
      throw new Error(`Failed to fetch metrics: ${response.statusText}`);
    }

    const data = await response.json();
    
    return NextResponse.json({
      status: 'success',
      metrics: data.data || [],
      total: data.data?.length || 0,
      prometheus_url: PROMETHEUS_URL,
    });

  } catch (error) {
    console.error('Prometheus GET error:', error);
    
    // Return fallback response
    return NextResponse.json({
      status: 'fallback',
      message: 'Prometheus unavailable',
      metrics: [
        'up',
        'http_requests_total',
        'http_request_duration_seconds',
        'process_cpu_seconds_total',
        'process_resident_memory_bytes',
        'nodejs_heap_size_total_bytes',
        'swarm_tasks_total',
        'swarm_active_agents',
        'llm_tokens_used_total',
        'llm_request_duration_seconds',
      ],
      prometheus_url: PROMETHEUS_URL,
    });
  }
}

function generateFallbackMetrics(query: string): any[] {
  const now = Date.now() / 1000;
  
  // Generate realistic-looking fallback data based on query
  if (query.includes('up')) {
    return [
      { metric: { job: 'sophia-dashboard', instance: 'localhost:3000' }, value: [now, '1'] },
      { metric: { job: 'sophia-agents', instance: 'localhost:5001' }, value: [now, '1'] },
      { metric: { job: 'mcp-context', instance: 'localhost:3002' }, value: [now, '1'] },
      { metric: { job: 'prometheus', instance: 'localhost:9090' }, value: [now, '0'] },
    ];
  }
  
  if (query.includes('http_requests_total')) {
    return [
      { metric: { method: 'GET', status: '200', endpoint: '/api/chat' }, value: [now, '1543'] },
      { metric: { method: 'POST', status: '200', endpoint: '/api/chat' }, value: [now, '892'] },
      { metric: { method: 'GET', status: '200', endpoint: '/api/health' }, value: [now, '3421'] },
      { metric: { method: 'GET', status: '404', endpoint: '/api/unknown' }, value: [now, '23'] },
    ];
  }
  
  if (query.includes('swarm_tasks_total')) {
    return [
      { metric: { swarm_type: 'research', status: 'completed' }, value: [now, '45'] },
      { metric: { swarm_type: 'planning', status: 'completed' }, value: [now, '38'] },
      { metric: { swarm_type: 'coding', status: 'completed' }, value: [now, '52'] },
      { metric: { swarm_type: 'research', status: 'failed' }, value: [now, '3'] },
    ];
  }
  
  if (query.includes('llm_tokens_used_total')) {
    return [
      { metric: { model: 'claude-3-sonnet', provider: 'anthropic' }, value: [now, '285943'] },
      { metric: { model: 'gpt-4', provider: 'openai' }, value: [now, '194832'] },
      { metric: { model: 'mixtral-8x7b', provider: 'together' }, value: [now, '423891'] },
    ];
  }
  
  if (query.includes('process_resident_memory_bytes')) {
    return [
      { metric: { job: 'sophia-dashboard' }, value: [now, '134217728'] }, // 128MB
      { metric: { job: 'sophia-agents' }, value: [now, '268435456'] }, // 256MB
      { metric: { job: 'mcp-context' }, value: [now, '201326592'] }, // 192MB
    ];
  }
  
  // Default fallback
  return [
    { metric: { service: 'sophia', type: 'default' }, value: [now, Math.random() * 100 + ''] }
  ];
}
