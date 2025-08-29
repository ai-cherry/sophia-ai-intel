/**
 * DebateScorecards - Shows judge scoring and debate outcomes
 * NO MOCK DATA - Real scores from debate events
 */

import React, { useState, useEffect } from 'react';

interface JudgeScore {
  judge: string;
  confidence: number;
  agreement: number;
  contradictions: number;
  tool_pass_rate: number;
  latency_ms: number;
  recommendation: string;
}

interface DebateOutcome {
  debate_id: string;
  topic: string;
  participants: string[];
  scores: JudgeScore[];
  winner?: string;
  consensus?: boolean;
  timestamp: string;
}

interface DebateScorecardsProps {
  swarmId?: string;
  onOutcome?: (outcome: DebateOutcome) => void;
}

export default function DebateScorecards({ swarmId, onOutcome }: DebateScorecardsProps) {
  const [outcomes, setOutcomes] = useState<DebateOutcome[]>([]);
  const [activeDebate, setActiveDebate] = useState<DebateOutcome | null>(null);
  
  useEffect(() => {
    // Subscribe to debate events via WebSocket if swarmId provided
    if (swarmId) {
      const ws = new WebSocket(`${process.env.NEXT_PUBLIC_SWARM_WS_URL || 'ws://localhost:8100'}/ws/debate/${swarmId}`);
      
      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          if (data.type === 'debate_outcome') {
            const outcome: DebateOutcome = data.outcome;
            setOutcomes(prev => [outcome, ...prev].slice(0, 10));
            setActiveDebate(outcome);
            if (onOutcome) onOutcome(outcome);
          }
        } catch (e) {
          console.error('Failed to parse debate event:', e);
        }
      };
      
      return () => ws.close();
    }
  }, [swarmId, onOutcome]);
  
  const getScoreColor = (score: number) => {
    if (score >= 0.8) return 'text-green-400';
    if (score >= 0.6) return 'text-yellow-400';
    return 'text-red-400';
  };
  
  return (
    <div className="space-y-4">
      {/* Active Debate */}
      {activeDebate && (
        <div className="bg-gradient-to-br from-purple-900/20 to-blue-900/20 rounded-lg p-4 border border-purple-500/30">
          <div className="flex justify-between items-start mb-3">
            <div>
              <h3 className="text-lg font-semibold text-white">Active Debate</h3>
              <p className="text-sm text-gray-400">{activeDebate.topic}</p>
            </div>
            {activeDebate.consensus && (
              <span className="px-3 py-1 bg-green-600/20 text-green-400 rounded-full text-xs">
                Consensus Reached
              </span>
            )}
          </div>
          
          {/* Participants */}
          <div className="flex gap-2 mb-3">
            {activeDebate.participants.map((p, i) => (
              <span key={i} className="px-2 py-1 bg-gray-700/50 text-gray-300 rounded text-xs">
                {p}
              </span>
            ))}
          </div>
          
          {/* Judge Scores */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            {activeDebate.scores.map((score, i) => (
              <div key={i} className="bg-black/30 rounded-lg p-3">
                <div className="flex justify-between items-center mb-2">
                  <span className="text-sm font-medium text-white">{score.judge}</span>
                  <span className="text-xs text-gray-400">{score.latency_ms}ms</span>
                </div>
                
                <div className="space-y-1 text-xs">
                  <div className="flex justify-between">
                    <span className="text-gray-400">Confidence:</span>
                    <span className={getScoreColor(score.confidence)}>
                      {(score.confidence * 100).toFixed(1)}%
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-400">Agreement:</span>
                    <span className={getScoreColor(score.agreement)}>
                      {(score.agreement * 100).toFixed(1)}%
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-400">Tool Pass:</span>
                    <span className={getScoreColor(score.tool_pass_rate)}>
                      {(score.tool_pass_rate * 100).toFixed(1)}%
                    </span>
                  </div>
                  {score.contradictions > 0 && (
                    <div className="flex justify-between">
                      <span className="text-gray-400">Contradictions:</span>
                      <span className="text-yellow-400">{score.contradictions}</span>
                    </div>
                  )}
                </div>
                
                {score.recommendation && (
                  <div className="mt-2 pt-2 border-t border-gray-700">
                    <p className="text-xs text-cyan-400">"{score.recommendation}"</p>
                  </div>
                )}
              </div>
            ))}
          </div>
          
          {/* Winner */}
          {activeDebate.winner && (
            <div className="mt-3 text-center">
              <span className="text-sm text-gray-400">Winner: </span>
              <span className="text-sm font-semibold text-cyan-400">{activeDebate.winner}</span>
            </div>
          )}
        </div>
      )}
      
      {/* Historical Outcomes */}
      {outcomes.length > 1 && (
        <div className="space-y-2">
          <h4 className="text-sm font-medium text-gray-300">Previous Debates</h4>
          {outcomes.slice(1).map((outcome, i) => (
            <div key={i} className="bg-gray-800/30 rounded p-2 flex justify-between items-center">
              <div>
                <span className="text-xs text-white">{outcome.topic}</span>
                <div className="text-xs text-gray-400">
                  {new Date(outcome.timestamp).toLocaleTimeString()}
                </div>
              </div>
              <div className="text-right">
                {outcome.consensus ? (
                  <span className="text-xs text-green-400">✓ Consensus</span>
                ) : outcome.winner ? (
                  <span className="text-xs text-cyan-400">{outcome.winner}</span>
                ) : (
                  <span className="text-xs text-yellow-400">No winner</span>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
      
      {/* Empty State */}
      {outcomes.length === 0 && !activeDebate && (
        <div className="text-center py-8 text-gray-400">
          <div className="text-2xl mb-2">⚖️</div>
          <p className="text-sm">No debate outcomes yet</p>
          <p className="text-xs mt-1">Debates will appear here when judges evaluate</p>
        </div>
      )}
    </div>
  );
}
