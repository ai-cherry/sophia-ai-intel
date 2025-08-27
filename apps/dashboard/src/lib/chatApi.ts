interface ChatMessage {
  id: string
  role: 'user' | 'assistant' | 'system'
  content: string
  timestamp: Date
  metadata?: {
    model?: string
    processing_time?: number
    prompt_enhanced?: boolean
    enhancement_profile?: string
    swarm_task_id?: string
    swarm_type?: string
    agent_swarm_used?: boolean
  }
}

interface ChatSettings {
  verbosity: 'minimal' | 'standard' | 'detailed'
  askMeThreshold: number
  riskStance: 'conservative' | 'balanced' | 'aggressive'
  enableEnhancement: boolean
  model: string
}

interface EnhancementResult {
  enhanced_prompt: string
  metadata: {
    intent_analysis: {
      primary_intent: string
      confidence: number
    }
    context_enriched: boolean
    constraints_applied: string[]
    ambiguity_resolved: boolean
    plan_generated: boolean
  }
  execution_time_ms: number
}

interface ChatResponse {
  message: ChatMessage
  error?: string
}

class ChatAPI {
  private baseUrl = 'http://192.222.51.223:8082'  // Lambda Labs Context service
  private agentSwarmUrl = 'http://192.222.51.223:8087'  // Lambda Labs Agent Swarm

  async enhancePrompt(prompt: string, settings: ChatSettings): Promise<EnhancementResult | null> {
    try {
      const response = await fetch(`${this.baseUrl}/enhance-prompt`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          prompt,
          profile: settings.verbosity,
          ask_me_threshold: settings.askMeThreshold,
          risk_stance: settings.riskStance,
          enable_plan_generation: true,
          enable_context_enrichment: true
        })
      })

      if (response.ok) {
        return await response.json()
      } else {
        console.warn('Prompt enhancement failed, using fallback')
        return this.fallbackEnhancement(prompt, settings)
      }
    } catch (error) {
      console.error('Prompt enhancement error:', error)
      return this.fallbackEnhancement(prompt, settings)
    }
  }

  private fallbackEnhancement(prompt: string, settings: ChatSettings): EnhancementResult {
    return {
      enhanced_prompt: `[${settings.riskStance.toUpperCase()} MODE] ${prompt}`,
      metadata: {
        intent_analysis: {
          primary_intent: 'general_inquiry',
          confidence: 0.8
        },
        context_enriched: false,
        constraints_applied: [`${settings.riskStance}_safety`, 'fallback_mode'],
        ambiguity_resolved: false,
        plan_generated: false
      },
      execution_time_ms: 10
    }
  }

  async sendMessage(prompt: string, settings: ChatSettings, conversationHistory: ChatMessage[]): Promise<ChatResponse> {
    try {
      // Check if this should be handled by agent swarm
      const shouldUseSwarm = this.shouldUseAgentSwarm(prompt)
      
      if (shouldUseSwarm) {
        return await this.processWithAgentSwarm(prompt, settings, conversationHistory)
      }

      // Step 1: Enhance the prompt if enabled
      const enhancement = settings.enableEnhancement 
        ? await this.enhancePrompt(prompt, settings)
        : null

      const finalPrompt = enhancement ? enhancement.enhanced_prompt : prompt

      // Step 2: Send to LLM via Context MCP (which has access to prompt enhancement)
      const response = await fetch(`${this.baseUrl}/chat/completions`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          messages: [
            {
              role: 'system',
              content: 'You are Sophia, an AI intelligence system with access to advanced agent swarm capabilities. Use your knowledge base and reasoning capabilities to provide helpful responses.'
            },
            ...conversationHistory.slice(-10).map(msg => ({
              role: msg.role,
              content: msg.content
            })),
            {
              role: 'user',
              content: finalPrompt
            }
          ],
          model: this.getModelMapping(settings.model),
          temperature: settings.riskStance === 'conservative' ? 0.3 : 
                      settings.riskStance === 'balanced' ? 0.7 : 0.9,
          max_tokens: settings.verbosity === 'minimal' ? 150 :
                     settings.verbosity === 'standard' ? 500 : 1000
        })
      })

      if (response.ok) {
        const result = await response.json()
        const assistantMessage: ChatMessage = {
          id: Date.now().toString(),
          role: 'assistant',
          content: result.choices[0].message.content,
          timestamp: new Date(),
          metadata: {
            model: settings.model,
            processing_time: enhancement?.execution_time_ms || 0,
            prompt_enhanced: !!enhancement,
            enhancement_profile: enhancement ? settings.verbosity : undefined
          }
        }

        return { message: assistantMessage }
      } else {
        // Fallback to simulated response
        return this.fallbackResponse(prompt, settings, enhancement)
      }
    } catch (error) {
      console.error('Chat API error:', error)
      return this.fallbackResponse(prompt, settings)
    }
  }

  private shouldUseAgentSwarm(prompt: string): boolean {
    /**
     * Determine if a prompt should be handled by the agent swarm
     */
    const swarmKeywords = [
      'analyze repository', 'code analysis', 'repository analysis',
      'examine codebase', 'review code', 'analyze code',
      'code patterns', 'architecture analysis', 'code quality',
      'implement feature', 'generate code', 'write code',
      'plan implementation', 'design solution', 'create plan',
      'refactor', 'optimize', 'improve code'
    ]

    const promptLower = prompt.toLowerCase()
    return swarmKeywords.some(keyword => promptLower.includes(keyword))
  }

  private async processWithAgentSwarm(
    prompt: string, 
    settings: ChatSettings, 
    conversationHistory: ChatMessage[]
  ): Promise<ChatResponse> {
    /**
     * Process the prompt using the agent swarm system
     */
    try {
      // Call agent swarm API endpoint
      const swarmResponse = await fetch(`${this.agentSwarmUrl}/agent-swarm/process`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          message: prompt,
          session_id: `chat_${Date.now()}`,
          user_context: {
            settings: settings,
            conversation_history: conversationHistory.slice(-5) // Last 5 messages for context
          }
        })
      })

      if (swarmResponse.ok) {
        const swarmResult = await swarmResponse.json()
        
        const assistantMessage: ChatMessage = {
          id: Date.now().toString(),
          role: 'assistant',
          content: swarmResult.message || 'Agent swarm processing completed.',
          timestamp: new Date(),
          metadata: {
            model: 'agent-swarm',
            processing_time: swarmResult.processing_time_ms || 0,
            prompt_enhanced: true,
            enhancement_profile: 'agent_swarm',
            swarm_task_id: swarmResult.task_id,
            swarm_type: swarmResult.type
          }
        }

        return { message: assistantMessage }
      } else {
        // Fallback to regular processing if swarm unavailable
        console.warn('Agent swarm unavailable, falling back to standard processing')
        return await this.standardProcessing(prompt, settings, conversationHistory)
      }
    } catch (error) {
      console.error('Agent swarm processing error:', error)
      // Fallback to regular processing
      return await this.standardProcessing(prompt, settings, conversationHistory)
    }
  }

  private async standardProcessing(
    prompt: string,
    settings: ChatSettings,
    conversationHistory: ChatMessage[]
  ): Promise<ChatResponse> {
    /**
     * Standard chat processing without agent swarm
     */
    const enhancement = settings.enableEnhancement 
      ? await this.enhancePrompt(prompt, settings)
      : null

    const finalPrompt = enhancement ? enhancement.enhanced_prompt : prompt

    const response = await fetch(`${this.baseUrl}/chat/completions`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        messages: [
          {
            role: 'system',
            content: 'You are Sophia, an AI intelligence system. Use your knowledge base and reasoning capabilities to provide helpful responses.'
          },
          ...conversationHistory.slice(-10).map(msg => ({
            role: msg.role,
            content: msg.content
          })),
          {
            role: 'user',
            content: finalPrompt
          }
        ],
        model: this.getModelMapping(settings.model),
        temperature: settings.riskStance === 'conservative' ? 0.3 : 
                    settings.riskStance === 'balanced' ? 0.7 : 0.9,
        max_tokens: settings.verbosity === 'minimal' ? 150 :
                   settings.verbosity === 'standard' ? 500 : 1000
      })
    })

    if (response.ok) {
      const result = await response.json()
      const assistantMessage: ChatMessage = {
        id: Date.now().toString(),
        role: 'assistant',
        content: result.choices[0].message.content,
        timestamp: new Date(),
        metadata: {
          model: settings.model,
          processing_time: enhancement?.execution_time_ms || 0,
          prompt_enhanced: !!enhancement,
          enhancement_profile: enhancement ? settings.verbosity : undefined
        }
      }

      return { message: assistantMessage }
    } else {
      return this.fallbackResponse(prompt, settings, enhancement)
    }
  }

  private fallbackResponse(prompt: string, settings: ChatSettings, enhancement?: EnhancementResult | null): ChatResponse {
    const responses = [
      `I understand you're asking about "${prompt}". Based on my analysis, here's what I can help with...`,
      `Regarding your question about "${prompt}", let me provide some insights...`,
      `Thank you for your query: "${prompt}". Here's my assessment...`
    ]

    const enhancementNote = enhancement 
      ? ` [Enhanced with ${settings.riskStance} approach, ${settings.verbosity} verbosity]`
      : ' [Standard processing]'

    const assistantMessage: ChatMessage = {
      id: Date.now().toString(),
      role: 'assistant', 
      content: responses[Math.floor(Math.random() * responses.length)] + enhancementNote + 
               '\n\n*Note: This is a simulated response. Full integration with LLM services is in progress.*',
      timestamp: new Date(),
      metadata: {
        model: settings.model + '-simulated',
        processing_time: enhancement?.execution_time_ms || 50,
        prompt_enhanced: !!enhancement,
        enhancement_profile: enhancement ? settings.verbosity : undefined
      }
    }

    return { message: assistantMessage }
  }

  private getModelMapping(model: string): string {
    const modelMap: Record<string, string> = {
      'gpt-5': 'gpt-4-turbo-preview', // Fallback until GPT-5 available
      'claude-opus-4.1': 'claude-opus-4.1', // Claude Opus 4.1
      'gpt-4o': 'gpt-4o-2024-08-06',
      'deepseek-coder': 'deepseek-coder-33b-instruct'
    }
    return modelMap[model] || 'gpt-4o-2024-08-06'
  }

  async getContextualSuggestions(prompt: string): Promise<string[]> {
    try {
      const response = await fetch(`${this.baseUrl}/context/suggestions`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ query: prompt })
      })

      if (response.ok) {
        const result = await response.json()
        return result.suggestions || []
      }
    } catch (error) {
      console.error('Failed to get contextual suggestions:', error)
    }

    // Fallback suggestions
    return [
      'Tell me more about the context',
      'What are the implications?',
      'Can you provide examples?',
      'How does this relate to our goals?'
    ]
  }
}

export const chatAPI = new ChatAPI()
export type { ChatMessage, ChatSettings, EnhancementResult, ChatResponse }
