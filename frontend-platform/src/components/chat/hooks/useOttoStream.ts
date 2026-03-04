import { useCallback, useRef, useState } from "react";
import { useChatStore } from "../state/useChatStore";

interface UseOttoStreamOptions {
  onDone?: (messageId: string) => void;
  onError?: (error: Event) => void;
  maxRetries?: number;
}

/**
 * Hook that encapsulates SSE (Server-Sent Events) streaming for Otto chat.
 * Handles connection, token parsing, reconnection with exponential backoff,
 * and graceful cancellation.
 */
export function useOttoStream(options: UseOttoStreamOptions = {}) {
  const { onDone, onError, maxRetries = 3 } = options;
  const [isConnected, setIsConnected] = useState(false);
  const eventSourceRef = useRef<EventSource | null>(null);
  const retryCountRef = useRef(0);
  const activeMessageIdRef = useRef<string | null>(null);
  const { appendStreamToken, updateMessage, setStreaming } =
    useChatStore.getState();

  const stopStream = useCallback(() => {
    if (eventSourceRef.current) {
      eventSourceRef.current.close();
      eventSourceRef.current = null;
    }
    setIsConnected(false);

    // Finalize the streaming message
    const messageId = activeMessageIdRef.current;
    if (messageId) {
      updateMessage(messageId, { isStreaming: false });
      activeMessageIdRef.current = null;
    }
    setStreaming(false);
    retryCountRef.current = 0;
  }, [updateMessage, setStreaming]);

  const startStream = useCallback(
    (url: string, messageId: string) => {
      // Close any existing connection
      if (eventSourceRef.current) {
        eventSourceRef.current.close();
      }

      activeMessageIdRef.current = messageId;
      setStreaming(true);
      retryCountRef.current = 0;

      const connect = () => {
        const es = new EventSource(url);
        eventSourceRef.current = es;

        es.onopen = () => {
          setIsConnected(true);
          retryCountRef.current = 0;
        };

        es.onmessage = (event) => {
          const data = event.data as string;

          if (data === "[DONE]") {
            stopStream();
            onDone?.(messageId);
            return;
          }

          // Append token to the streaming message
          appendStreamToken(messageId, data);
        };

        es.onerror = (event) => {
          es.close();
          setIsConnected(false);

          if (retryCountRef.current < maxRetries) {
            retryCountRef.current++;
            const delay = Math.min(
              1000 * Math.pow(2, retryCountRef.current),
              16000,
            );
            setTimeout(connect, delay);
          } else {
            stopStream();
            onError?.(event);
          }
        };
      };

      connect();
    },
    [appendStreamToken, maxRetries, onDone, onError, setStreaming, stopStream],
  );

  return { startStream, stopStream, isConnected };
}
