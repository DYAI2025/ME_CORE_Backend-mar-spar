// Markerengine Core Types
export interface AnalysisSchema {
  id: string
  name: string
  description: string
  version: string
  markers: MarkerDefinition[]
}

export interface MarkerDefinition {
  id: string
  name: string
  pattern: string
  weight: number
  category: 'risk' | 'sentiment' | 'intent' | 'topic' | 'custom'
  color?: string
}

export interface AnalysisRequest {
  text: string
  schemaId: string
  options?: {
    highlightMarkers?: boolean
    includeConfidence?: boolean
    maxResults?: number
  }
}

export interface AnalysisResult {
  id: string
  requestId: string
  timestamp: Date
  text: string
  schema: AnalysisSchema
  riskScore: number
  markers: DetectedMarker[]
  analysis: {
    sentiment: SentimentAnalysis
    topics: TopicAnalysis[]
    summary: string
    confidence: number
  }
  metadata: {
    processingTime: number
    version: string
    model: string
  }
}

export interface DetectedMarker {
  id: string
  name: string
  category: string
  confidence: number
  positions: TextPosition[]
  weight: number
  color: string
}

export interface TextPosition {
  start: number
  end: number
  text: string
}

export interface SentimentAnalysis {
  score: number // -1 to 1
  label: 'positive' | 'neutral' | 'negative'
  confidence: number
}

export interface TopicAnalysis {
  topic: string
  confidence: number
  keywords: string[]
}

// UI Component Types
export interface InputCardProps {
  onAnalyze: (request: AnalysisRequest) => void
  schemas: AnalysisSchema[]
  isLoading?: boolean
  maxCharacters?: number
}

export interface ResultGridProps {
  result: AnalysisResult | null
  isLoading?: boolean
}

export interface RiskGaugeProps {
  score: number
  size?: 'sm' | 'md' | 'lg'
  showLabel?: boolean
}

export interface MarkerChipProps {
  marker: DetectedMarker
  onClick?: (marker: DetectedMarker) => void
  size?: 'sm' | 'md' | 'lg'
}

export interface LiveLogEntry {
  id: string
  timestamp: Date
  level: 'info' | 'success' | 'warning' | 'error'
  message: string
  source?: string
  data?: any
}

export interface LiveLogDrawerProps {
  isOpen: boolean
  onClose: () => void
  entries: LiveLogEntry[]
}

// Authentication & Security Types
export interface AuthUser {
  id: string
  email: string
  name: string
  avatar?: string
  role: 'admin' | 'user' | 'viewer'
  permissions: string[]
}

export interface JWTPayload {
  sub: string
  email: string
  name: string
  role: string
  permissions: string[]
  iat: number
  exp: number
}

export interface RateLimit {
  limit: number
  remaining: number
  reset: Date
  retryAfter?: number
}

export interface RateLimitIndicatorProps {
  rateLimit: RateLimit
  showDetails?: boolean
}

// WebSocket Types
export interface WebSocketMessage {
  type: 'log' | 'analysis_start' | 'analysis_progress' | 'analysis_complete' | 'error'
  payload: any
  timestamp: Date
}

export interface WebSocketConnection {
  isConnected: boolean
  lastHeartbeat?: Date
  reconnectAttempts: number
}

// API Types
export interface ApiResponse<T = any> {
  success: boolean
  data?: T
  error?: string
  message?: string
  metadata?: {
    requestId: string
    timestamp: Date
    version: string
  }
}

export interface ApiError {
  code: string
  message: string
  details?: any
  statusCode: number
}

// Theme Types
export interface ThemeConfig {
  mode: 'light' | 'dark' | 'system'
  primary: string
  secondary: string
  accent: string
}

// Form Types
export interface FormState<T> {
  data: T
  errors: Record<string, string>
  isSubmitting: boolean
  isValid: boolean
}

// Analytics Types
export interface AnalyticsEvent {
  event: string
  properties?: Record<string, any>
  timestamp: Date
  userId?: string
}

// Export utility types
export type RiskLevel = 'low' | 'medium' | 'high'
export type ChipVariant = 'primary' | 'secondary' | 'warning' | 'success'
export type LogLevel = 'info' | 'success' | 'warning' | 'error'
export type ResponseStatus = 'idle' | 'loading' | 'success' | 'error' 