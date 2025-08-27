'use client';

import { useState } from 'react';

// Mock interfaces for now
interface PersonaConfig {
  humorLevel: number;
  formality: number;
}

export default function PersonaControls() {
  const [config, setConfig] = useState<PersonaConfig>({
    humorLevel: 0.25,
    formality: 0.5,
  });

  return (
    <div className="p-4 bg-white rounded-lg shadow-md">
      <h4 className="text-lg font-semibold mb-4">Persona Controls</h4>
      <div className="space-y-4">
        <div>
          <label className="block text-sm font-medium text-gray-700">
            Humor Level: {Math.round(config.humorLevel * 100)}%
          </label>
          <input
            type="range"
            min="0"
            max="1"
            step="0.05"
            value={config.humorLevel}
            onChange={(e) => setConfig({ ...config, humorLevel: parseFloat(e.target.value) })}
            className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer"
          />
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700">
            Formality: {Math.round(config.formality * 100)}%
          </label>
          <input
            type="range"
            min="0"
            max="1"
            step="0.05"
            value={config.formality}
            onChange={(e) => setConfig({ ...config, formality: parseFloat(e.target.value) })}
            className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer"
          />
        </div>
      </div>
    </div>
  );
}