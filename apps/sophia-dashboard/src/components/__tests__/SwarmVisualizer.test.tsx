import React from 'react'
import { render, screen, fireEvent } from '@testing-library/react'
import { SwarmVisualizer } from '../SwarmVisualizer'

describe('SwarmVisualizer', () => {
  const mockSwarmData = {
    swarms: [
      {
        id: 'research',
        name: 'Research Swarm',
        agents: ['scout1', 'scout2', 'scout3'],
        status: 'active',
        progress: 75,
      },
      {
        id: 'development',
        name: 'Development Swarm',
        agents: ['coder1', 'coder2'],
        status: 'idle',
        progress: 0,
      },
    ],
    connections: [
      { from: 'research', to: 'development', strength: 0.8 },
    ],
  }

  it('renders swarm visualization correctly', () => {
    render(<SwarmVisualizer data={mockSwarmData} />)

    expect(screen.getByText('Research Swarm')).toBeInTheDocument()
    expect(screen.getByText('Development Swarm')).toBeInTheDocument()
  })

  it('displays agent counts for each swarm', () => {
    render(<SwarmVisualizer data={mockSwarmData} />)

    expect(screen.getByText(/3 agents/i)).toBeInTheDocument()
    expect(screen.getByText(/2 agents/i)).toBeInTheDocument()
  })

  it('shows swarm status indicators', () => {
    render(<SwarmVisualizer data={mockSwarmData} />)

    const activeSwarm = screen.getByTestId('swarm-research')
    const idleSwarm = screen.getByTestId('swarm-development')

    expect(activeSwarm).toHaveClass('status-active')
    expect(idleSwarm).toHaveClass('status-idle')
  })

  it('displays progress bars for active swarms', () => {
    render(<SwarmVisualizer data={mockSwarmData} />)

    const progressBar = screen.getByRole('progressbar', { name: /research swarm progress/i })
    expect(progressBar).toHaveAttribute('aria-valuenow', '75')
  })

  it('renders connections between swarms', () => {
    render(<SwarmVisualizer data={mockSwarmData} />)

    const connection = screen.getByTestId('connection-research-development')
    expect(connection).toBeInTheDocument()
    expect(connection).toHaveAttribute('data-strength', '0.8')
  })

  it('handles swarm selection on click', () => {
    const onSwarmSelect = jest.fn()
    
    render(
      <SwarmVisualizer 
        data={mockSwarmData} 
        onSwarmSelect={onSwarmSelect}
      />
    )

    const researchSwarm = screen.getByTestId('swarm-research')
    fireEvent.click(researchSwarm)

    expect(onSwarmSelect).toHaveBeenCalledWith('research')
  })

  it('shows tooltip on hover with swarm details', async () => {
    render(<SwarmVisualizer data={mockSwarmData} />)

    const researchSwarm = screen.getByTestId('swarm-research')
    fireEvent.mouseEnter(researchSwarm)

    expect(await screen.findByRole('tooltip')).toBeInTheDocument()
    expect(screen.getByText(/scout1, scout2, scout3/)).toBeInTheDocument()
  })

  it('animates transitions when data updates', () => {
    const { rerender } = render(<SwarmVisualizer data={mockSwarmData} />)

    const updatedData = {
      ...mockSwarmData,
      swarms: [
        ...mockSwarmData.swarms,
        {
          id: 'validation',
          name: 'Validation Swarm',
          agents: ['judge1'],
          status: 'active',
          progress: 50,
        },
      ],
    }

    rerender(<SwarmVisualizer data={updatedData} />)

    const newSwarm = screen.getByTestId('swarm-validation')
    expect(newSwarm).toHaveClass('swarm-entering')
  })

  it('handles empty data gracefully', () => {
    render(<SwarmVisualizer data={{ swarms: [], connections: [] }} />)

    expect(screen.getByText(/no active swarms/i)).toBeInTheDocument()
  })

  it('supports different visualization modes', () => {
    render(<SwarmVisualizer data={mockSwarmData} mode="compact" />)

    expect(screen.getByTestId('visualization-container')).toHaveClass('mode-compact')
  })
})