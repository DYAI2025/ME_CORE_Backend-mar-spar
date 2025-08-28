/**
 * WebSocket hook for live logs and real-time updates
 * Connects to the backend WebSocket endpoint for live streaming
 */

import { useState, useEffect, useRef, useCallback } from 'react'
import type { WebSocketMessage, WebSocketConnection } from '@/types'

interface UseWebSocketOptions {
  autoConnect?: boolean
  reconnectInterval?: number
  maxReconnectAttempts?: number
}

interface UseWebSocketReturn {
  connection: WebSocketConnection
  messages: WebSocketMessage[]
  connect: () => void
  disconnect: () => void
  sendMessage: (message: any) => void
  clearMessages: () => void
}

export function useWebSocket(
  endpoint: string = '/api/dashboard/ws',
  options: UseWebSocketOptions = {}
): UseWebSocketReturn {
  const {
    autoConnect = false,
    reconnectInterval = 3000,
    maxReconnectAttempts = 5,
  } = options

  const [connection, setConnection] = useState<WebSocketConnection>({
    isConnected: false,
    reconnectAttempts: 0,
  })
  
  const [messages, setMessages] = useState<WebSocketMessage[]>([])
  const wsRef = useRef<WebSocket | null>(null)
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null)
  const heartbeatIntervalRef = useRef<NodeJS.Timeout | null>(null)

  // Get WebSocket URL
  const getWebSocketUrl = useCallback(() => {
    const baseUrl = process.env.NEXT_PUBLIC_WS_URL || process.env.NEXT_PUBLIC_API_URL || 'ws://localhost:8000'
    const wsUrl = baseUrl.replace(/^http/, 'ws')
    return `${wsUrl}${endpoint}`
  }, [endpoint])

  // Add new message
  const addMessage = useCallback((message: WebSocketMessage) => {
    setMessages(prev => [...prev.slice(-99), message]) // Keep last 100 messages
  }, [])

  // Setup heartbeat
  const setupHeartbeat = useCallback(() => {
    if (heartbeatIntervalRef.current) {
      clearInterval(heartbeatIntervalRef.current)
    }

    heartbeatIntervalRef.current = setInterval(() => {
      if (wsRef.current?.readyState === WebSocket.OPEN) {
        wsRef.current.send(JSON.stringify({ type: 'ping' }))
        setConnection(prev => ({
          ...prev,
          lastHeartbeat: new Date(),
        }))
      }
    }, 30000) // Ping every 30 seconds
  }, [])

  // Connect to WebSocket
  const connect = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      return // Already connected
    }

    try {
      const wsUrl = getWebSocketUrl()
      wsRef.current = new WebSocket(wsUrl)

      wsRef.current.onopen = () => {
        setConnection(prev => ({
          ...prev,
          isConnected: true,
          reconnectAttempts: 0,
        }))
        
        setupHeartbeat()
        
        addMessage({
          type: 'log',
          payload: { level: 'info', message: 'WebSocket connected' },
          timestamp: new Date(),
        })
      }

      wsRef.current.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data)
          
          // Handle pong response
          if (data.type === 'pong') {
            return
          }

          // Add received message
          const message: WebSocketMessage = {
            type: data.type || 'log',
            payload: data.payload || data,
            timestamp: new Date(data.timestamp || Date.now()),
          }
          
          addMessage(message)
        } catch (error) {
          console.error('Failed to parse WebSocket message:', error)
          addMessage({
            type: 'error',
            payload: { message: 'Failed to parse WebSocket message' },
            timestamp: new Date(),
          })
        }
      }

      wsRef.current.onerror = (error) => {
        console.error('WebSocket error:', error)
        addMessage({
          type: 'error',
          payload: { message: 'WebSocket connection error' },
          timestamp: new Date(),
        })
      }

      wsRef.current.onclose = (event) => {
        setConnection(prev => ({
          ...prev,
          isConnected: false,
        }))

        if (heartbeatIntervalRef.current) {
          clearInterval(heartbeatIntervalRef.current)
        }

        // Auto-reconnect if not manually disconnected
        if (event.code !== 1000 && connection.reconnectAttempts < maxReconnectAttempts) {
          setConnection(prev => ({
            ...prev,
            reconnectAttempts: prev.reconnectAttempts + 1,
          }))

          reconnectTimeoutRef.current = setTimeout(() => {
            addMessage({
              type: 'log',
              payload: { 
                level: 'warning', 
                message: `Reconnecting... (${connection.reconnectAttempts + 1}/${maxReconnectAttempts})` 
              },
              timestamp: new Date(),
            })
            connect()
          }, reconnectInterval)
        } else {
          addMessage({
            type: 'log',
            payload: { level: 'warning', message: 'WebSocket disconnected' },
            timestamp: new Date(),
          })
        }
      }
    } catch (error) {
      console.error('Failed to create WebSocket connection:', error)
      addMessage({
        type: 'error',
        payload: { message: 'Failed to create WebSocket connection' },
        timestamp: new Date(),
      })
    }
  }, [getWebSocketUrl, setupHeartbeat, addMessage, connection.reconnectAttempts, maxReconnectAttempts, reconnectInterval])

  // Disconnect from WebSocket
  const disconnect = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current)
    }
    
    if (heartbeatIntervalRef.current) {
      clearInterval(heartbeatIntervalRef.current)
    }

    if (wsRef.current) {
      wsRef.current.close(1000, 'Manual disconnect')
      wsRef.current = null
    }

    setConnection(prev => ({
      ...prev,
      isConnected: false,
      reconnectAttempts: 0,
    }))
  }, [])

  // Send message through WebSocket
  const sendMessage = useCallback((message: any) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(message))
    } else {
      console.warn('WebSocket is not connected')
    }
  }, [])

  // Clear messages
  const clearMessages = useCallback(() => {
    setMessages([])
  }, [])

  // Auto-connect on mount if enabled
  useEffect(() => {
    if (autoConnect) {
      connect()
    }

    return () => {
      disconnect()
    }
  }, [autoConnect, connect, disconnect])

  return {
    connection,
    messages,
    connect,
    disconnect,
    sendMessage,
    clearMessages,
  }
}