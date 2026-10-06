import { useEffect, useRef, useState, useCallback } from 'react'

export function useWebSocket(path, options = {}) {
  const { onMessage, onOpen, onClose, onError, enabled = true } = options
  const [isConnected, setIsConnected] = useState(false)
  const [lastMessage, setLastMessage] = useState(null)

  const socketRef = useRef(null)
  const reconnectTimeoutRef = useRef(null)
  const reconnectCountRef = useRef(0)

  // Callbacks ref to avoid unnecessary socket reconnects on callback changes
  const callbacksRef = useRef({ onMessage, onOpen, onClose, onError })
  useEffect(() => {
    callbacksRef.current = { onMessage, onOpen, onClose, onError }
  }, [onMessage, onOpen, onClose, onError])

  const connect = useCallback(() => {
    if (!path || !enabled) return
    if (socketRef.current && (socketRef.current.readyState === WebSocket.OPEN || socketRef.current.readyState === WebSocket.CONNECTING)) {
      return
    }

    const token = localStorage.getItem('token')
    if (!token) return

    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    const host = import.meta.env.DEV ? '127.0.0.1:8000' : window.location.host
    const wsUrl = `${protocol}//${host}${path}?token=${encodeURIComponent(token)}`
    try {
      const ws = new WebSocket(wsUrl)
      socketRef.current = ws

      ws.onopen = (event) => {
        setIsConnected(true)
        reconnectCountRef.current = 0
        callbacksRef.current.onOpen?.(event)
      }

      ws.onmessage = (event) => {
        try {
          const parsed = JSON.parse(event.data)
          setLastMessage(parsed)
          callbacksRef.current.onMessage?.(parsed, event)
        } catch {
          setLastMessage(event.data)
          callbacksRef.current.onMessage?.(event.data, event)
        }
      }

      ws.onerror = (event) => {
        callbacksRef.current.onError?.(event)
      }

      ws.onclose = (event) => {
        setIsConnected(false)
        callbacksRef.current.onClose?.(event)

        // Attempt reconnection only if not closed cleanly (e.g. 1000) and within max retries limit
        if (enabled && !event.wasClean && event.code !== 1000 && reconnectCountRef.current < 5) {
          const timeout = Math.min(1000 * Math.pow(2, reconnectCountRef.current), 10000)
          reconnectCountRef.current += 1
          reconnectTimeoutRef.current = setTimeout(() => {
            connect()
          }, timeout)
        }
      }
    } catch (err) {
      console.error('WebSocket connection error:', err)
    }
  }, [path, enabled])

  useEffect(() => {
    connect()

    return () => {
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current)
      }
      if (socketRef.current) {
        socketRef.current.close(1000, 'Component unmounted')
      }
    }
  }, [connect])

  const sendMessage = useCallback((data) => {
    if (socketRef.current && socketRef.current.readyState === WebSocket.OPEN) {
      const payload = typeof data === 'object' ? JSON.stringify(data) : data
      socketRef.current.send(payload)
      return true
    }
    return false
  }, [])

  return {
    isConnected,
    lastMessage,
    sendMessage,
  }
}
