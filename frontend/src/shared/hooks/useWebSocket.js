import { useState, useEffect, useRef } from 'react';

/**
 * Reusable FSD Shared Hook: useWebSocket
 * Maintains persistent WebSocket connection to backend ws://localhost:8000/ws/telemetry
 * and returns live streaming agent telemetry events.
 */
export function useWebSocket(url = 'ws://localhost:8000/ws/telemetry') {
  const [events, setEvents] = useState([]);
  const [isConnected, setIsConnected] = useState(false);
  const socketRef = useRef(null);

  useEffect(() => {
    console.log('[WebSocket UI] Connecting to:', url);
    const socket = new WebSocket(url);
    socketRef.current = socket;

    socket.onopen = () => {
      console.log('[WebSocket UI] Connected to Telemetry Stream');
      setIsConnected(true);
    };

    socket.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        console.log('[WebSocket UI] Received Event:', data);
        if (data.node_name) {
          setEvents((prev) => [data, ...prev.slice(0, 49)]);
        }
      } catch (err) {
        console.warn('[WebSocket UI] Parse error:', err);
      }
    };

    socket.onclose = () => {
      console.log('[WebSocket UI] Disconnected from Telemetry Stream');
      setIsConnected(false);
    };

    socket.onerror = (err) => {
      console.error('[WebSocket UI] Socket error:', err);
    };

    return () => {
      socket.close();
    };
  }, [url]);

  return { events, isConnected };
}
