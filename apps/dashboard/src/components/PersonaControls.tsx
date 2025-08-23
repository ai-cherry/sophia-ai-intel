/**
 * Sophia AI Persona Controls
 * Exposes persona toggles and humor slider with cooldowns
 */

import { useState, useEffect } from 'react';

// Mock interfaces to avoid import issues during development
interface PersonaConfig {
  humorLevel: number;
  formality: number;
  terseness: number;
  humorFrequency: {
    maxPerSession: number;
    cooldownMessages: number;
  };
  contextAwareness: {
    errorHandling: boolean;
    securityContext: boolean;
    financeContext: boolean;
    infrastructureContext: boolean;
  };
  followUpPolicy: 'always' | 'only-if-ambiguous-or-high-value' | 'never';
}

interface SessionStats {
  messageCount: number;
  humorCount: number;
  humorRate: number;
  enforcementStats: {
    byContext: Record<string, number>;
  };
}

// Mock managers - will be replaced with actual imports when persona system is integrated
const mockPersonaConfigManager = {
  getConfig: (): PersonaConfig => ({
    humorLevel: 0.25,
    formality: 0.45,
    terseness: 0.6,
    humorFrequency: {
      maxPerSession: 5,
      cooldownMessages: 3
    },
    contextAwareness: {
      errorHandling: true,
      securityContext: true,
      financeContext: true,
      infrastructureContext: true
    },
    followUpPolicy: 'only-if-ambiguous-or-high-value'
  }),
  updateConfig: (config: PersonaConfig) => {
    console.log('PersonaConfig updated:', config);
  }
};

const mockToneMiddleware = {
  getSessionStats: (): SessionStats => ({
    messageCount: 12,
    humorCount: 2,
    humorRate: 0.167,
    enforcementStats: {
      byContext: {
        error: 1,
        security: 0,
        finance: 1
      }
    }
  }),
  resetSession: () => {
    console.log('Session reset');
  }
};

interface PersonaControlsProps {
  onConfigChange?: (config: PersonaConfig) => void;
}

export default function PersonaControls({ onConfigChange }: PersonaControlsProps) {
  const [config, setConfig] = useState<PersonaConfig>(mockPersonaConfigManager.getConfig());
  const [stats, setStats] = useState<SessionStats>(mockToneMiddleware.getSessionStats());
  const [cooldownTime, setCooldownTime] = useState(0);

  useEffect(() => {
    const interval = setInterval(() => {
      setStats(mockToneMiddleware.getSessionStats());
      
      // Update cooldown timer
      const messagesSinceHumor = stats.messageCount - (stats.humorCount * config.humorFrequency.cooldownMessages);
      const remainingCooldown = Math.max(0, config.humorFrequency.cooldownMessages - messagesSinceHumor);
      setCooldownTime(remainingCooldown);
    }, 1000);

    return () => clearInterval(interval);
  }, [config, stats]);

  const updateConfig = (updates: Partial<PersonaConfig>) => {
    const newConfig = { ...config, ...updates };
    setConfig(newConfig);
    mockPersonaConfigManager.updateConfig(newConfig);
    onConfigChange?.(newConfig);
  };

  const resetSession = () => {
    mockToneMiddleware.resetSession();
    setStats({ messageCount: 0, humorCount: 0, humorRate: 0, enforcementStats: { byContext: {} } });
  };

  return (
    <div style={{
      background: 'white',
      borderRadius: '8px',
      boxShadow: '0 1px 3px 0 rgba(0, 0, 0, 0.1)',
      border: '1px solid #e5e7eb',
      padding: '1.5rem'
    }}>
      {/* Header */}
      <div style={{
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        marginBottom: '1.5rem'
      }}>
        <h3 style={{ margin: 0, fontSize: '1.125rem', fontWeight: '600', color: '#111827' }}>
          Persona Controls
        </h3>
        <button
          onClick={resetSession}
          style={{
            fontSize: '0.875rem',
            color: '#2563eb',
            background: 'none',
            border: 'none',
            cursor: 'pointer',
            fontWeight: '500'
          }}
        >
          Reset Session
        </button>
      </div>

      {/* Humor Controls */}
      <div style={{ marginBottom: '1.5rem' }}>
        <div style={{ marginBottom: '1rem' }}>
          <label style={{
            display: 'block',
            fontSize: '0.875rem',
            fontWeight: '500',
            color: '#374151',
            marginBottom: '0.5rem'
          }}>
            Humor Level: {(config.humorLevel * 100).toFixed(0)}%
          </label>
          <input
            type="range"
            min="0"
            max="1"
            step="0.05"
            value={config.humorLevel}
            onChange={(e) => updateConfig({ humorLevel: parseFloat(e.target.value) })}
            style={{ width: '100%' }}
          />
          <div style={{
            display: 'flex',
            justifyContent: 'space-between',
            fontSize: '0.75rem',
            color: '#6b7280',
            marginTop: '0.25rem'
          }}>
            <span>None</span>
            <span>Subtle</span>
            <span>Maximum</span>
          </div>
        </div>

        {/* Humor Status */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '1rem', marginBottom: '1rem' }}>
          <div style={{
            padding: '0.25rem 0.75rem',
            borderRadius: '9999px',
            fontSize: '0.75rem',
            fontWeight: '500',
            backgroundColor: config.humorLevel > 0 ? '#dcfce7' : '#f3f4f6',
            color: config.humorLevel > 0 ? '#166534' : '#374151'
          }}>
            {config.humorLevel > 0 ? 'Humor Enabled' : 'Humor Disabled'}
          </div>
          {cooldownTime > 0 && (
            <div style={{
              padding: '0.25rem 0.75rem',
              borderRadius: '9999px',
              backgroundColor: '#fef3c7',
              color: '#92400e',
              fontSize: '0.75rem',
              fontWeight: '500'
            }}>
              Cooldown: {cooldownTime} messages
            </div>
          )}
        </div>

        {/* Frequency Controls */}
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
          <div>
            <label style={{
              display: 'block',
              fontSize: '0.875rem',
              fontWeight: '500',
              color: '#374151',
              marginBottom: '0.25rem'
            }}>
              Max per Session: {config.humorFrequency.maxPerSession}
            </label>
            <input
              type="range"
              min="1"
              max="20"
              value={config.humorFrequency.maxPerSession}
              onChange={(e) => updateConfig({
                humorFrequency: {
                  ...config.humorFrequency,
                  maxPerSession: parseInt(e.target.value)
                }
              })}
              style={{ width: '100%' }}
            />
          </div>
          <div>
            <label style={{
              display: 'block',
              fontSize: '0.875rem',
              fontWeight: '500',
              color: '#374151',
              marginBottom: '0.25rem'
            }}>
              Cooldown: {config.humorFrequency.cooldownMessages} msgs
            </label>
            <input
              type="range"
              min="1"
              max="15"
              value={config.humorFrequency.cooldownMessages}
              onChange={(e) => updateConfig({
                humorFrequency: {
                  ...config.humorFrequency,
                  cooldownMessages: parseInt(e.target.value)
                }
              })}
              style={{ width: '100%' }}
            />
          </div>
        </div>
      </div>

      {/* Communication Style */}
      <div style={{ marginBottom: '1.5rem' }}>
        <h4 style={{
          margin: '0 0 1rem 0',
          fontSize: '1rem',
          fontWeight: '500',
          color: '#111827'
        }}>
          Communication Style
        </h4>
        
        <div style={{ marginBottom: '1rem' }}>
          <label style={{
            display: 'block',
            fontSize: '0.875rem',
            fontWeight: '500',
            color: '#374151',
            marginBottom: '0.5rem'
          }}>
            Formality: {(config.formality * 100).toFixed(0)}%
          </label>
          <input
            type="range"
            min="0"
            max="1"
            step="0.05"
            value={config.formality}
            onChange={(e) => updateConfig({ formality: parseFloat(e.target.value) })}
            style={{ width: '100%' }}
          />
          <div style={{
            display: 'flex',
            justifyContent: 'space-between',
            fontSize: '0.75rem',
            color: '#6b7280',
            marginTop: '0.25rem'
          }}>
            <span>Casual</span>
            <span>Professional</span>
            <span>Formal</span>
          </div>
        </div>

        <div>
          <label style={{
            display: 'block',
            fontSize: '0.875rem',
            fontWeight: '500',
            color: '#374151',
            marginBottom: '0.5rem'
          }}>
            Terseness: {(config.terseness * 100).toFixed(0)}%
          </label>
          <input
            type="range"
            min="0"
            max="1"
            step="0.05"
            value={config.terseness}
            onChange={(e) => updateConfig({ terseness: parseFloat(e.target.value) })}
            style={{ width: '100%' }}
          />
          <div style={{
            display: 'flex',
            justifyContent: 'space-between',
            fontSize: '0.75rem',
            color: '#6b7280',
            marginTop: '0.25rem'
          }}>
            <span>Verbose</span>
            <span>Balanced</span>
            <span>Brief</span>
          </div>
        </div>
      </div>

      {/* Session Statistics */}
      <div style={{
        backgroundColor: '#f9fafb',
        borderRadius: '8px',
        padding: '1rem',
        marginBottom: '1rem'
      }}>
        <h4 style={{
          margin: '0 0 0.75rem 0',
          fontSize: '1rem',
          fontWeight: '500',
          color: '#111827'
        }}>
          Session Statistics
        </h4>
        
        <div style={{
          display: 'grid',
          gridTemplateColumns: '1fr 1fr 1fr',
          gap: '1rem',
          textAlign: 'center'
        }}>
          <div>
            <div style={{ fontSize: '1.5rem', fontWeight: 'bold', color: '#2563eb' }}>
              {stats.messageCount}
            </div>
            <div style={{ fontSize: '0.75rem', color: '#6b7280' }}>Messages</div>
          </div>
          <div>
            <div style={{ fontSize: '1.5rem', fontWeight: 'bold', color: '#059669' }}>
              {stats.humorCount}
            </div>
            <div style={{ fontSize: '0.75rem', color: '#6b7280' }}>Humor Used</div>
          </div>
          <div>
            <div style={{ fontSize: '1.5rem', fontWeight: 'bold', color: '#7c3aed' }}>
              {(stats.humorRate * 100).toFixed(1)}%
            </div>
            <div style={{ fontSize: '0.75rem', color: '#6b7280' }}>Humor Rate</div>
          </div>
        </div>

        {/* Enforcement Statistics */}
        {stats.enforcementStats && Object.keys(stats.enforcementStats.byContext).length > 0 && (
          <div style={{ marginTop: '1rem' }}>
            <h5 style={{
              fontSize: '0.875rem',
              fontWeight: '500',
              color: '#374151',
              marginBottom: '0.5rem'
            }}>
              Context Enforcements
            </h5>
            <div>
              {Object.entries(stats.enforcementStats.byContext).map(([context, count]) => (
                <div key={context} style={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  fontSize: '0.875rem',
                  marginBottom: '0.25rem'
                }}>
                  <span style={{ color: '#6b7280', textTransform: 'capitalize' }}>
                    {context}:
                  </span>
                  <span style={{ fontWeight: '500' }}>{count}</span>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Quick Actions */}
      <div style={{ display: 'flex', gap: '0.75rem' }}>
        <button
          onClick={() => updateConfig({
            humorLevel: 0.25,
            formality: 0.45,
            terseness: 0.6
          })}
          style={{
            flex: 1,
            padding: '0.5rem 0.75rem',
            backgroundColor: '#eff6ff',
            color: '#1d4ed8',
            border: 'none',
            borderRadius: '6px',
            fontSize: '0.875rem',
            fontWeight: '500',
            cursor: 'pointer'
          }}
        >
          Default Settings
        </button>
        <button
          onClick={() => updateConfig({
            humorLevel: 0,
            formality: 0.8,
            terseness: 0.7
          })}
          style={{
            flex: 1,
            padding: '0.5rem 0.75rem',
            backgroundColor: '#f9fafb',
            color: '#374151',
            border: 'none',
            borderRadius: '6px',
            fontSize: '0.875rem',
            fontWeight: '500',
            cursor: 'pointer'
          }}
        >
          Professional Mode
        </button>
        <button
          onClick={() => updateConfig({
            humorLevel: 0.4,
            formality: 0.2,
            terseness: 0.3
          })}
          style={{
            flex: 1,
            padding: '0.5rem 0.75rem',
            backgroundColor: '#f0fdf4',
            color: '#166534',
            border: 'none',
            borderRadius: '6px',
            fontSize: '0.875rem',
            fontWeight: '500',
            cursor: 'pointer'
          }}
        >
          Casual Mode
        </button>
      </div>
    </div>
  );
}