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
  private baseUrl = 'https://sophiaai-mcp-context-v2.fly.dev'

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
        // Fallback to simulated response
        return this.fallbackResponse(prompt, settings, enhancement)
      }
    } catch (error) {
      console.error('Chat API error:', error)
      return this.fallbackResponse(prompt, settings)
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
      'claude-3.5-sonnet': 'claude-3-5-sonnet-20241022',
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