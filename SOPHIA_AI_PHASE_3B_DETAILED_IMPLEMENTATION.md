# Sophia AI Phase 3B: User Experience Enhancement - Detailed Implementation Plan

**Date**: August 25, 2025  
**Duration**: 2 Weeks (Weeks 11-12)  
**Priority**: HIGH - Following Phase 3A  
**Goal**: Implement advanced UI/UX features including dark theme dashboard, voice/avatar integration, and proactive notifications

## Executive Summary

Phase 3B transforms the user experience of Sophia AI by implementing a modern, responsive dashboard with voice and avatar capabilities. This phase focuses on creating an intuitive, accessible interface that supports multiple interaction modalities while providing proactive insights and role-based access control.

### Key Objectives
1. Build dark-themed, mobile-responsive dashboard
2. Integrate voice interaction with 11 Labs
3. Implement avatar system for visual engagement
4. Create role-based access control (RBAC)
5. Develop proactive notification system

## User Experience Architecture

### Core Components

| Component | Purpose | Key Features |
|-----------|---------|--------------|
| Dashboard UI | Central control interface | Dark theme, responsive design, real-time updates |
| Voice Interface | Natural language interaction | Speech-to-text, text-to-speech, command processing |
| Avatar System | Visual representation | Animated responses, emotion states, customization |
| RBAC System | Security and permissions | Role management, fine-grained permissions |
| Notification Engine | Proactive communications | Smart alerts, priority routing, user preferences |

### User Interaction Flows

1. **Voice-First Flow**: Voice command → Processing → Visual feedback → Voice response
2. **Dashboard Flow**: Visual interaction → Real-time updates → Action feedback
3. **Hybrid Flow**: Combined voice and visual interaction
4. **Mobile Flow**: Touch-optimized interface with voice support
5. **Notification Flow**: Event trigger → Smart routing → User notification

## Week 11: Core UI Implementation

### Day 1-2: Dark Theme Dashboard

#### 11.1 Dashboard Foundation
```typescript
// apps/dashboard/src/components/Dashboard.tsx
import React, { useState, useEffect } from 'react';
import { ThemeProvider } from '@mui/material/styles';
import { CssBaseline, Box, Grid } from '@mui/material';
import { darkTheme } from '../themes/darkTheme';
import { useWebSocket } from '../hooks/useWebSocket';
import { useAuth } from '../hooks/useAuth';

interface DashboardProps {
  userId: string;
  role: UserRole;
}

const Dashboard: React.FC<DashboardProps> = ({ userId, role }) => {
  const { user, permissions } = useAuth();
  const { messages, sendMessage, connectionStatus } = useWebSocket();
  
  const [activeView, setActiveView] = useState<string>('overview');
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [aiState, setAiState] = useState<AIState>({
    status: 'idle',
    activeAgents: [],
    currentTasks: []
  });

  return (
    <ThemeProvider theme={darkTheme}>
      <CssBaseline />
      <Box sx={{ display: 'flex', height: '100vh' }}>
        {/* Sidebar Navigation */}
        <Sidebar 
          activeView={activeView}
          onViewChange={setActiveView}
          permissions={permissions}
        />
        
        {/* Main Content Area */}
        <Box sx={{ flex: 1, display: 'flex', flexDirection: 'column' }}>
          {/* Top Bar with Notifications */}
          <TopBar 
            notifications={notifications}
            connectionStatus={connectionStatus}
            user={user}
          />
          
          {/* Dynamic Content Based on View */}
          <Box sx={{ flex: 1, overflow: 'auto', p: 3 }}>
            <Grid container spacing={3}>
              {renderContent(activeView, { aiState, messages, role })}
            </Grid>
          </Box>
          
          {/* Avatar and Voice Interface */}
          <AvatarInterface 
            onVoiceCommand={handleVoiceCommand}
            aiState={aiState}
          />
        </Box>
      </Box>
    </ThemeProvider>
  );
};

// Theme Configuration
// apps/dashboard/src/themes/darkTheme.ts
import { createTheme } from '@mui/material/styles';

export const darkTheme = createTheme({
  palette: {
    mode: 'dark',
    primary: {
      main: '#6366f1',
      light: '#818cf8',
      dark: '#4f46e5',
      contrastText: '#ffffff'
    },
    secondary: {
      main: '#22d3ee',
      light: '#67e8f9',
      dark: '#06b6d4'
    },
    background: {
      default: '#0f172a',
      paper: '#1e293b'
    },
    text: {
      primary: '#f1f5f9',
      secondary: '#cbd5e1'
    },
    error: {
      main: '#ef4444'
    },
    warning: {
      main: '#f59e0b'
    },
    success: {
      main: '#10b981'
    }
  },
  typography: {
    fontFamily: '"Inter", "Helvetica", "Arial", sans-serif',
    h1: {
      fontSize: '2.5rem',
      fontWeight: 700,
      letterSpacing: '-0.02em'
    },
    h2: {
      fontSize: '2rem',
      fontWeight: 600,
      letterSpacing: '-0.01em'
    },
    body1: {
      fontSize: '1rem',
      lineHeight: 1.7
    }
  },
  shape: {
    borderRadius: 12
  },
  components: {
    MuiButton: {
      styleOverrides: {
        root: {
          textTransform: 'none',
          fontWeight: 600,
          borderRadius: 8
        }
      }
    },
    MuiCard: {
      styleOverrides: {
        root: {
          backgroundImage: 'linear-gradient(to bottom right, rgba(99, 102, 241, 0.05), transparent)',
          backdropFilter: 'blur(10px)',
          border: '1px solid rgba(255, 255, 255, 0.1)'
        }
      }
    }
  }
});

// Responsive Grid Component
// apps/dashboard/src/components/ResponsiveGrid.tsx
interface ResponsiveGridProps {
  children: React.ReactNode;
  columns?: { xs?: number; sm?: number; md?: number; lg?: number };
}

const ResponsiveGrid: React.FC<ResponsiveGridProps> = ({ 
  children, 
  columns = { xs: 12, sm: 6, md: 4, lg: 3 } 
}) => {
  return (
    <Grid container spacing={3}>
      {React.Children.map(children, (child, index) => (
        <Grid item {...columns} key={index}>
          {child}
        </Grid>
      ))}
    </Grid>
  );
};
```

#### 11.2 Mobile Responsive Design
```typescript
// apps/dashboard/src/hooks/useResponsive.ts
import { useTheme, useMediaQuery } from '@mui/material';

interface ResponsiveBreakpoints {
  isMobile: boolean;
  isTablet: boolean;
  isDesktop: boolean;
  isLargeScreen: boolean;
}

export const useResponsive = (): ResponsiveBreakpoints => {
  const theme = useTheme();
  
  const isMobile = useMediaQuery(theme.breakpoints.down('sm'));
  const isTablet = useMediaQuery(theme.breakpoints.between('sm', 'md'));
  const isDesktop = useMediaQuery(theme.breakpoints.between('md', 'lg'));
  const isLargeScreen = useMediaQuery(theme.breakpoints.up('lg'));
  
  return { isMobile, isTablet, isDesktop, isLargeScreen };
};

// Mobile-Optimized Chat Interface
// apps/dashboard/src/components/mobile/MobileChatInterface.tsx
const MobileChatInterface: React.FC = () => {
  const [isVoiceMode, setIsVoiceMode] = useState(false);
  const [messages, setMessages] = useState<Message[]>([]);
  
  return (
    <Box sx={{ 
      height: '100vh', 
      display: 'flex', 
      flexDirection: 'column',
      position: 'relative'
    }}>
      {/* Collapsible Header */}
      <MobileHeader />
      
      {/* Messages Area */}
      <Box sx={{ 
        flex: 1, 
        overflow: 'auto',
        px: 2,
        py: 1
      }}>
        <MessageList messages={messages} />
      </Box>
      
      {/* Input Area with Voice Toggle */}
      <Box sx={{ 
        p: 2, 
        borderTop: '1px solid rgba(255,255,255,0.1)',
        display: 'flex',
        gap: 1
      }}>
        {isVoiceMode ? (
          <VoiceInput onTranscript={handleVoiceInput} />
        ) : (
          <TextInput onSend={handleTextSend} />
        )}
        
        <IconButton 
          onClick={() => setIsVoiceMode(!isVoiceMode)}
          color={isVoiceMode ? 'primary' : 'default'}
        >
          {isVoiceMode ? <KeyboardIcon /> : <MicIcon />}
        </IconButton>
      </Box>
      
      {/* Floating Avatar */}
      <FloatingAvatar 
        position="bottom-right"
        size="small"
        animated={true}
      />
    </Box>
  );
};
```

### Day 3: Voice Integration

#### 11.3 11 Labs Voice Integration
```typescript
// apps/dashboard/src/services/voiceService.ts
import { ElevenLabsClient } from '@11labs/api';

interface VoiceConfig {
  apiKey: string;
  voiceId: string;
  modelId: string;
  stability: number;
  similarityBoost: number;
}

export class VoiceService {
  private client: ElevenLabsClient;
  private audioContext: AudioContext;
  private voiceConfig: VoiceConfig;
  
  constructor(config: VoiceConfig) {
    this.voiceConfig = config;
    this.client = new ElevenLabsClient({ apiKey: config.apiKey });
    this.audioContext = new (window.AudioContext || window.webkitAudioContext)();
  }
  
  async textToSpeech(text: string): Promise<AudioBuffer> {
    try {
      // Generate speech using 11 Labs
      const audio = await this.client.textToSpeech(this.voiceConfig.voiceId, {
        text,
        model_id: this.voiceConfig.modelId,
        voice_settings: {
          stability: this.voiceConfig.stability,
          similarity_boost: this.voiceConfig.similarityBoost
        }
      });
      
      // Convert to AudioBuffer
      const arrayBuffer = await audio.arrayBuffer();
      return await this.audioContext.decodeAudioData(arrayBuffer);
      
    } catch (error) {
      console.error('Text-to-speech error:', error);
      throw error;
    }
  }
  
  async streamTextToSpeech(
    text: string, 
    onChunk: (chunk: AudioBuffer) => void
  ): Promise<void> {
    const stream = await this.client.textToSpeechStream(this.voiceConfig.voiceId, {
      text,
      model_id: this.voiceConfig.modelId,
      voice_settings: {
        stability: this.voiceConfig.stability,
        similarity_boost: this.voiceConfig.similarityBoost
      },
      optimize_streaming_latency: 3
    });
    
    for await (const chunk of stream) {
      const audioBuffer = await this.processStreamChunk(chunk);
      onChunk(audioBuffer);
    }
  }
}

// Voice Command Processing
// apps/dashboard/src/services/voiceCommandProcessor.ts
interface VoiceCommand {
  transcript: string;
  confidence: number;
  intent?: string;
  entities?: Record<string, any>;
}

export class VoiceCommandProcessor {
  private speechRecognition: SpeechRecognition;
  private isListening: boolean = false;
  
  constructor() {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    this.speechRecognition = new SpeechRecognition();
    
    // Configure recognition
    this.speechRecognition.continuous = true;
    this.speechRecognition.interimResults = true;
    this.speechRecognition.lang = 'en-US';
  }
  
  startListening(
    onResult: (command: VoiceCommand) => void,
    onInterim?: (transcript: string) => void
  ): void {
    if (this.isListening) return;
    
    this.isListening = true;
    
    this.speechRecognition.onresult = (event) => {
      const last = event.results.length - 1;
      const transcript = event.results[last][0].transcript;
      const confidence = event.results[last][0].confidence;
      
      if (event.results[last].isFinal) {
        // Process final result
        const command = this.processCommand(transcript, confidence);
        onResult(command);
      } else if (onInterim) {
        // Send interim results for UI feedback
        onInterim(transcript);
      }
    };
    
    this.speechRecognition.start();
  }
  
  private processCommand(transcript: string, confidence: number): VoiceCommand {
    // Extract intent and entities
    const processed = this.extractIntentAndEntities(transcript);
    
    return {
      transcript,
      confidence,
      intent: processed.intent,
      entities: processed.entities
    };
  }
  
  private extractIntentAndEntities(transcript: string): {
    intent?: string;
    entities?: Record<string, any>;
  } {
    const lowerTranscript = transcript.toLowerCase();
    
    // Intent patterns
    const intentPatterns = [
      { pattern: /show me (.+)/, intent: 'show', entityKey: 'target' },
      { pattern: /analyze (.+)/, intent: 'analyze', entityKey: 'subject' },
      { pattern: /create (.+)/, intent: 'create', entityKey: 'type' },
      { pattern: /what is the status of (.+)/, intent: 'status', entityKey: 'item' },
      { pattern: /help with (.+)/, intent: 'help', entityKey: 'topic' }
    ];
    
    for (const { pattern, intent, entityKey } of intentPatterns) {
      const match = lowerTranscript.match(pattern);
      if (match) {
        return {
          intent,
          entities: { [entityKey]: match[1] }
        };
      }
    }
    
    // Default to general query
    return { intent: 'query' };
  }
  
  stopListening(): void {
    if (!this.isListening) return;
    
    this.isListening = false;
    this.speechRecognition.stop();
  }
}
```

### Day 4: Avatar System

#### 11.4 Interactive Avatar Implementation
```typescript
// apps/dashboard/src/components/avatar/AvatarSystem.tsx
import React, { useRef, useEffect, useState } from 'react';
import { Canvas } from '@react-three/fiber';
import { useGLTF, useAnimations } from '@react-three/drei';

interface AvatarProps {
  emotion: 'neutral' | 'happy' | 'thinking' | 'speaking' | 'concerned';
  isSpeaking: boolean;
  message?: string;
}

const Avatar: React.FC<AvatarProps> = ({ emotion, isSpeaking, message }) => {
  const group = useRef();
  const { scene, animations } = useGLTF('/models/sophia-avatar.glb');
  const { actions } = useAnimations(animations, group);
  
  // Emotion to animation mapping
  const emotionAnimations = {
    neutral: 'idle',
    happy: 'happy_gesture',
    thinking: 'thinking_pose',
    speaking: 'talking',
    concerned: 'concerned_expression'
  };
  
  useEffect(() => {
    // Play appropriate animation
    const animationName = isSpeaking ? 'talking' : emotionAnimations[emotion];
    const action = actions[animationName];
    
    if (action) {
      action.reset().fadeIn(0.5).play();
      
      return () => {
        action.fadeOut(0.5);
      };
    }
  }, [emotion, isSpeaking, actions]);
  
  return <primitive ref={group} object={scene} />;
};

// Avatar Interface Component
export const AvatarInterface: React.FC<{
  onVoiceCommand: (command: VoiceCommand) => void;
  aiState: AIState;
}> = ({ onVoiceCommand, aiState }) => {
  const [isListening, setIsListening] = useState(false);
  const [currentEmotion, setCurrentEmotion] = useState<AvatarProps['emotion']>('neutral');
  const [isSpeaking, setIsSpeaking] = useState(false);
  const voiceProcessor = useRef(new VoiceCommandProcessor());
  const voiceService = useRef(new VoiceService(voiceConfig));
  
  // Update emotion based on AI state
  useEffect(() => {
    if (aiState.status === 'processing') {
      setCurrentEmotion('thinking');
    } else if (aiState.status === 'error') {
      setCurrentEmotion('concerned');
    } else if (aiState.status === 'success') {
      setCurrentEmotion('happy');
    } else {
      setCurrentEmotion('neutral');
    }
  }, [aiState.status]);
  
  const handleSpeak = async (text: string) => {
    setIsSpeaking(true);
    setCurrentEmotion('speaking');
    
    try {
      await voiceService.current.streamTextToSpeech(
        text,
        (chunk) => {
          // Play audio chunk
          playAudioBuffer(chunk);
        }
      );
    } finally {
      setIsSpeaking(false);
      setCurrentEmotion('neutral');
    }
  };
  
  return (
    <Box sx={{ 
      position: 'fixed',
      bottom: 20,
      right: 20,
      width: 200,
      height: 200,
      background: 'rgba(0, 0, 0, 0.8)',
      borderRadius: '50%',
      overflow: 'hidden',
      border: '2px solid',
      borderColor: isListening ? 'primary.main' : 'transparent',
      transition: 'all 0.3s ease'
    }}>
      <Canvas camera={{ position: [0, 0, 5], fov: 35 }}>
        <ambientLight intensity={0.5} />
        <spotLight position={[10, 10, 10]} angle={0.15} penumbra={1} />
        <Avatar 
          emotion={currentEmotion}
          isSpeaking={isSpeaking}
        />
      </Canvas>
      
      {/* Voice Activation Button */}
      <IconButton
        sx={{
          position: 'absolute',
          bottom: 10,
          left: '50%',
          transform: 'translateX(-50%)',
          backgroundColor: 'primary.main',
          '&:hover': {
            backgroundColor: 'primary.dark'
          }
        }}
        onClick={() => {
          if (isListening) {
            voiceProcessor.current.stopListening();
          } else {
            voiceProcessor.current.startListening(onVoiceCommand);
          }
          setIsListening(!isListening);
        }}
      >
        <MicIcon />
      </IconButton>
    </Box>
  );
};
```

## Week 12: Access Control & Notifications

### Day 5-6: Role-Based Access Control

#### 12.1 RBAC Implementation
```typescript
// apps/dashboard/src/auth/rbac.ts
export interface Permission {
  resource: string;
  action: string;
  conditions?: Record<string, any>;
}

export interface Role {
  id: string;
  name: string;
  description: string;
  permissions: Permission[];
  inherits?: string[];  // Role inheritance
}

export interface User {
  id: string;
  email: string;
  name: string;
  roles: string[];
  customPermissions?: Permission[];  // User-specific permissions
}

export class RBACService {
  private roles: Map<string, Role> = new Map();
  private userCache: Map<string, Set<string>> = new Map();
  
  constructor() {
    this.initializeDefaultRoles();
  }
  
  private initializeDefaultRoles(): void {
    // Admin role - full access
    this.addRole({
      id: 'admin',
      name: 'Administrator',
      description: 'Full system access',
      permissions: [
        { resource: '*', action: '*' }
      ]
    });
    
    // Manager role
    this.addRole({
      id: 'manager',
      name: 'Manager',
      description: 'Team and project management',
      permissions: [
        { resource: 'dashboard', action: 'read' },
        { resource: 'analytics', action: 'read' },
        { resource: 'team', action: '*' },
        { resource: 'projects', action: '*' },
        { resource: 'ai_agents', action: 'read' },
        { resource: 'ai_agents', action: 'execute' }
      ]
    });
    
    // Analyst role
    this.addRole({
      id: 'analyst',
      name: 'Data Analyst',
      description: 'Data analysis and reporting',
      permissions: [
        { resource: 'dashboard', action: 'read' },
        { resource: 'analytics', action: '*' },
        { resource: 'reports', action: '*' },
        { resource: 'data_export', action: 'execute' }
      ],
      inherits: ['viewer']
    });
    
    // Developer role
    this.addRole({
      id: 'developer',
      name: 'Developer',
      description: 'Development and technical access',
      permissions: [
        { resource: 'code_analysis', action: '*' },
        { resource: 'ai_agents', action: '*' },
        { resource: 'integrations', action: '*' },
        { resource: 'logs', action: 'read' }
      ],
      inherits: ['analyst']
    });
    
    // Viewer role
    this.addRole({
      id: 'viewer',
      name: 'Viewer',
      description: 'Read-only access',
      permissions: [
        { resource: 'dashboard', action: 'read' },
        { resource: 'reports', action: 'read' }
      ]
    });
  }
  
  hasPermission(
    user: User,
    resource: string,
    action: string,
    context?: Record<string, any>
  ): boolean {
    // Get all permissions for user
    const permissions = this.getUserPermissions(user);
    
    // Check permissions
    return permissions.some(permission => {
      // Check wildcard
      if (permission.resource === '*' || permission.action === '*') {
        return true;
      }
      
      // Check exact match
      if (permission.resource === resource && permission.action === action) {
        // Check conditions if present
        if (permission.conditions && context) {
          return this.evaluateConditions(permission.conditions, context);
        }
        return true;
      }
      
      // Check resource wildcards (e.g., 'projects.*')
      if (permission.resource.endsWith('.*')) {
        const baseResource = permission.resource.slice(0, -2);
        if (resource.startsWith(baseResource) && permission.action === action) {
          return true;
        }
      }
      
      return false;
    });
  }
  
  private getUserPermissions(user: User): Permission[] {
    const cacheKey = `${user.id}:${user.roles.join(',')}`;
    
    // Check cache
    if (this.userCache.has(cacheKey)) {
      return Array.from(this.userCache.get(cacheKey)!).map(p => JSON.parse(p));
    }
    
    const permissions = new Set<string>();
    
    // Collect permissions from all roles (with inheritance)
    const processedRoles = new Set<string>();
    const rolesToProcess = [...user.roles];
    
    while (rolesToProcess.length > 0) {
      const roleId = rolesToProcess.pop()!;
      
      if (processedRoles.has(roleId)) continue;
      processedRoles.add(roleId);
      
      const role = this.roles.get(roleId);
      if (role) {
        // Add role permissions
        role.permissions.forEach(p => permissions.add(JSON.stringify(p)));
        
        // Add inherited roles to process
        if (role.inherits) {
          rolesToProcess.push(...role.inherits);
        }
      }
    }
    
    // Add custom user permissions
    if (user.customPermissions) {
      user.customPermissions.forEach(p => permissions.add(JSON.stringify(p)));
    }
    
    // Cache the result
    this.userCache.set(cacheKey, permissions);
    
    return Array.from(permissions).map(p => JSON.parse(p));
  }
  
  private evaluateConditions(
    conditions: Record<string, any>,
    context: Record<string, any>
  ): boolean {
    for (const [key, value] of Object.entries(conditions)) {
      if (context[key] !== value) {
        return false;
      }
    }
    return true;
  }
}

// React Hook for RBAC
export const useRBAC = () => {
  const { user } = useAuth();
  const rbac = useRef(new RBACService());
  
  const can = useCallback((resource: string, action: string, context?: any) => {
    if (!user) return false;
    return rbac.current.hasPermission(user, resource, action, context);
  }, [user]);
  
  const requirePermission = useCallback((
    resource: string,
    action: string,
    context?: any
  ) => {
    if (!can(resource, action, context)) {
      throw new Error(`Insufficient permissions: ${resource}.${action}`);
    }
  }, [can]);
  
  return { can, requirePermission };
};
```

### Day 7-8: Proactive Notifications

#### 12.2 Smart Notification System
```typescript
// apps/dashboard/src/services/notificationService.ts
export interface Notification {
  id: string;
  type: 'info' | 'warning' | 'error' | 'success' | 'ai_insight';
  priority: 'low' | 'medium' | 'high' | 'urgent';
  title: string;
  message: string;
  source: string;
  timestamp: Date;
  actions?: NotificationAction[];
  metadata?: Record<string, any>;
  read: boolean;
  dismissed: boolean;
}

interface NotificationAction {
  label: string;
  action: string;
  params?: Record<string, any>;
}

export class NotificationService {
  private notifications: Map<string, Notification> = new Map();
  private subscribers: Set<(notifications: Notification[]) => void> = new Set();
  private userPreferences: UserNotificationPreferences;
  private aiInsightEngine: AIInsightEngine;
  
  constructor(preferences: UserNotificationPreferences) {
    this.userPreferences = preferences;
    this.aiInsightEngine = new AIInsightEngine();
    
    // Start proactive monitoring
    this.startProactiveMonitoring();
  }
  
  private startProactiveMonitoring(): void {
    // Monitor system events
    this.monitorSystemHealth();
    this.monitorBusinessMetrics();
    this.monitorUserActivity();
    this.monitorAIInsights();
  }
  
  private async monitorAIInsights(): Promise<void> {
    setInterval(async () => {
      try {
        // Get AI insights
        const insights = await this.aiInsightEngine.generateInsights();
        
        for (const insight of insights) {
          if (this.shouldNotify(insight)) {
            this.createNotification({
              type: 'ai_insight',
              priority: insight.importance as any,
              title: insight.title,
              message: insight.description,
              source: 'AI Insight Engine',
              actions: insight.suggestedActions?.map(a => ({
                label: a.label,
                action: a.type,
                params: a.params
              })),
              metadata: {
                insightType: insight.type,
                confidence: insight.confidence,
                impact: insight.estimatedImpact
              }
            });
          }
        }
      } catch (error) {
        console.error('Failed to generate AI insights:', error);
      }
    }, 60000); // Check every minute
  }
  
  private shouldNotify(insight: AIInsight): boolean {
    const { preferences } = this.userPreferences;
    
    // Check if user wants this type of insight
    if (!preferences.aiInsights[insight.type]) {
      return false;
    }
    
    // Check priority threshold
    const priorityLevels = ['low', 'medium', 'high', 'urgent'];
    const insightPriority = priorityLevels.indexOf(insight.importance);
    const thresholdPriority = priorityLevels.indexOf(preferences.priorityThreshold);
    
    if (insightPriority < thresholdPriority) {
      return false;
    }
    
    // Check quiet hours
    if (preferences.quietHours.enabled) {
      const now = new Date();
      const currentHour = now.getHours();
      const { start, end } = preferences.quietHours;
      
      if (start <= end) {
        if (currentHour >= start && currentHour < end) {
          return false;
        }
      } else {
        if (currentHour >= start || currentHour < end) {
          return false;
        }
      }
    }
    
    return true;
  }
  
  createNotification(params: Omit<Notification, 'id' | 'timestamp' | 'read' | 'dismissed'>): voi
