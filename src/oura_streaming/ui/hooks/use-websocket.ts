import { useEffect, useRef, useState, useCallback } from "react";

export type ConnectionStatus = "connecting" | "connected" | "disconnected";

interface UseWebSocketOptions {
  /** Max events to buffer (oldest dropped first) */
  maxBuffer?: number;
  /** Reconnect delay in ms */
  reconnectDelay?: number;
}

export interface WebSocketEvent {
  id: string;
  received_at: string;
  event: {
    data_type: string;
    event_type: string;
    user_id: string | null;
    timestamp: string | null;
    data: Record<string, unknown> | null;
  };
}

export function useWebSocket(
  url: string,
  { maxBuffer = 100, reconnectDelay = 3000 }: UseWebSocketOptions = {},
) {
  const [status, setStatus] = useState<ConnectionStatus>("disconnected");
  const [events, setEvents] = useState<WebSocketEvent[]>([]);
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimer = useRef<ReturnType<typeof setTimeout>>();

  const connect = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) return;

    setStatus("connecting");
    const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
    const wsUrl = `${protocol}//${window.location.host}${url}`;
    const ws = new WebSocket(wsUrl);

    ws.onopen = () => setStatus("connected");

    ws.onmessage = (msg) => {
      try {
        const event = JSON.parse(msg.data) as WebSocketEvent;
        setEvents((prev) => {
          const next = [event, ...prev];
          return next.length > maxBuffer ? next.slice(0, maxBuffer) : next;
        });
      } catch {
        // skip malformed messages
      }
    };

    ws.onclose = () => {
      setStatus("disconnected");
      wsRef.current = null;
      reconnectTimer.current = setTimeout(connect, reconnectDelay);
    };

    ws.onerror = () => ws.close();

    wsRef.current = ws;
  }, [url, maxBuffer, reconnectDelay]);

  useEffect(() => {
    connect();
    return () => {
      clearTimeout(reconnectTimer.current);
      wsRef.current?.close();
    };
  }, [connect]);

  return { status, events };
}
