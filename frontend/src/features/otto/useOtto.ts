/**
 * useOtto — SSE hook for the Otto universal chat.
 *
 * Manages SSE connection, message accumulation, status,
 * and form submission handling.
 */

import { useCallback, useRef, useState } from 'react';
import { useAuthStore } from '../../state/authStore';
import type { OttoFormField, OttoMessage, OttoStatus } from './types';

let _msgId = 0;
function nextId(): string {
  return `otto-${++_msgId}-${Date.now()}`;
}

export interface UseOttoReturn {
  status: OttoStatus;
  messages: OttoMessage[];
  error: string | null;
  send: (message: string, pageKey?: string | null) => void;
  reset: () => void;
  submitForm: (messageId: string, values: Record<string, unknown>) => void;
}

export function useOtto(): UseOttoReturn {
  const [status, setStatus] = useState<OttoStatus>('idle');
  const [messages, setMessages] = useState<OttoMessage[]>([]);
  const [error, setError] = useState<string | null>(null);
  const esRef = useRef<EventSource | null>(null);

  const reset = useCallback(() => {
    esRef.current?.close();
    esRef.current = null;
    setStatus('idle');
    setMessages([]);
    setError(null);
  }, []);

  /** Shared SSE message handler. */
  const handleSSEMessage = useCallback((
    data: Record<string, unknown>,
    es: EventSource,
    currentAssistantId: string | null,
    setCurrentAssistantId: (id: string | null) => void,
  ) => {
    if (data.role === 'form') {
      const formMsg: OttoMessage = {
        id: nextId(),
        role: 'form',
        content: (data.content as string) || 'Preencha os campos abaixo:',
        timestamp: Date.now(),
        formSchema: data.schema as OttoFormField[],
        formData: data.data as Record<string, unknown>,
      };
      setMessages((prev) => [...prev, formMsg]);
      setStatus('done');
      es.close();
      esRef.current = null;
      return;
    }

    if (data.role === 'tool') {
      const toolMsg: OttoMessage = {
        id: nextId(),
        role: 'tool',
        content: (data.content as string) || '',
        timestamp: Date.now(),
        toolName: data.tool_name as string,
        toolResult: data.tool_result,
      };
      setMessages((prev) => [...prev, toolMsg]);
      setCurrentAssistantId(null);
      return;
    }

    if (data.role === 'system') {
      const sysMsg: OttoMessage = {
        id: nextId(),
        role: 'system',
        content: (data.content as string) || '',
        timestamp: Date.now(),
      };
      setMessages((prev) => [...prev, sysMsg]);

      if (data.done) {
        const errorContent = (data.content as string) || '';
        setStatus(errorContent.includes('Erro') ? 'error' : 'done');
        setError(errorContent.includes('Erro') ? errorContent : null);
        es.close();
        esRef.current = null;
      }
      return;
    }

    // Assistant message
    if (data.done) {
      if (data.content) {
        if (currentAssistantId) {
          setMessages((prev) =>
            prev.map((m) =>
              m.id === currentAssistantId
                ? { ...m, content: data.content as string, streaming: false }
                : m
            )
          );
        } else {
          const finalMsg: OttoMessage = {
            id: nextId(),
            role: 'assistant',
            content: (data.content as string),
            timestamp: Date.now(),
          };
          setMessages((prev) => [...prev, finalMsg]);
        }
      }
      setStatus('done');
      es.close();
      esRef.current = null;
      setCurrentAssistantId(null);
      return;
    }

    if (data.content) {
      if (currentAssistantId) {
        setMessages((prev) =>
          prev.map((m) =>
            m.id === currentAssistantId
              ? { ...m, content: m.content + (data.content as string) }
              : m
          )
        );
      } else {
        const newId = nextId();
        setCurrentAssistantId(newId);
        const assistantMsg: OttoMessage = {
          id: newId,
          role: 'assistant',
          content: (data.content as string),
          timestamp: Date.now(),
          streaming: true,
        };
        setMessages((prev) => [...prev, assistantMsg]);
      }
    }
  }, []);

  const send = useCallback((message: string, pageKey?: string | null) => {
    esRef.current?.close();

    const userMsg: OttoMessage = {
      id: nextId(),
      role: 'user',
      content: message,
      timestamp: Date.now(),
    };

    setMessages((prev) => [...prev, userMsg]);
    setStatus('streaming');
    setError(null);

    const token = useAuthStore.getState().token;
    const params = new URLSearchParams({
      input: message,
      ...(pageKey ? { page_key: pageKey } : {}),
      ...(token ? { token } : {}),
    });

    const url = `/api/otto/stream?${params.toString()}`;
    const es = new EventSource(url);
    esRef.current = es;

    let currentAssistantId: string | null = null;

    es.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        handleSSEMessage(data, es, currentAssistantId, (id) => { currentAssistantId = id; });
      } catch {
        // ignore malformed events
      }
    };

    es.onerror = () => {
      setError('Conexão com o servidor perdida.');
      setStatus('error');
      es.close();
      esRef.current = null;
    };
  }, [handleSSEMessage]);

  const submitForm = useCallback((messageId: string, values: Record<string, unknown>) => {
    setMessages((prev) =>
      prev.map((m) =>
        m.id === messageId
          ? { ...m, formSubmitted: true, content: `Dados enviados: ${Object.keys(values).length} campos` }
          : m
      )
    );

    const summary = Object.entries(values)
      .filter(([, v]) => v !== '' && v !== null && v !== undefined)
      .map(([k, v]) => `${k}: ${v}`)
      .join('\n');

    const userMsg: OttoMessage = {
      id: nextId(),
      role: 'user',
      content: summary || '(formulário enviado)',
      timestamp: Date.now(),
    };
    setMessages((prev) => [...prev, userMsg]);

    const token = useAuthStore.getState().token;
    const formInput = `[FORM_RESPONSE] ${JSON.stringify(values)}`;
    const params = new URLSearchParams({
      input: formInput,
      ...(token ? { token } : {}),
    });

    const url = `/api/otto/stream?${params.toString()}`;
    const es = new EventSource(url);
    esRef.current = es;
    setStatus('streaming');

    let currentAssistantId: string | null = null;

    es.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        handleSSEMessage(data, es, currentAssistantId, (id) => { currentAssistantId = id; });
      } catch {
        // ignore malformed events
      }
    };

    es.onerror = () => {
      setError('Conexão com o servidor perdida.');
      setStatus('error');
      es.close();
      esRef.current = null;
    };
  }, [handleSSEMessage]);

  return { status, messages, error, send, reset, submitForm };
}
