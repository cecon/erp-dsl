/**
 * OttoPanel — integrated side panel for the Otto universal chat.
 *
 * Renders INSIDE AppShell.Aside (pushes main content).
 * Uses ChatInput from @erp-dsl/chat-ui for rich TipTap editing.
 */

import { ActionIcon, Loader, Text, Group } from '@mantine/core';
import { useCallback, useEffect, useRef } from 'react';
import { ChatInput } from '@erp-dsl/chat-ui';
import { OttoMessage } from './OttoMessage';
import { useOttoContext } from './OttoProvider';
import type { Message } from '@erp-dsl/chat-ui';

export function OttoPanel() {
  const { close, context, messages, status, send, reset, submitForm, respondInteractive } = useOttoContext();
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages]);

  const handleSend = useCallback((msg: Message) => {
    // Extract text from the Message content array
    const text = msg.content
      .filter((c): c is { type: 'text'; text: string } => c.type === 'text')
      .map((c) => c.text)
      .join('\n')
      .trim();

    if (!text || status === 'streaming') return;
    send(text, context.pageKey);
  }, [status, send, context.pageKey]);

  const handleStop = useCallback(() => {
    // No-op for now — SSE abort is handled in useOtto
  }, []);

  const subtitle = context.pageTitle ? ` · ${context.pageTitle}` : '';

  return (
    <div className="otto-panel">
      {/* Header */}
      <div className="otto-header">
        <div className="otto-header-left">
          <span className="otto-header-icon">🐾</span>
          <span className="otto-header-title">Otto</span>
          {subtitle && (
            <span className="otto-header-context">{subtitle}</span>
          )}
        </div>
        <Group gap="xs">
          {messages.length > 0 && (
            <ActionIcon
              variant="subtle"
              color="gray"
              size="sm"
              onClick={reset}
              title="Limpar conversa"
            >
              🗑️
            </ActionIcon>
          )}
          <ActionIcon
            variant="subtle"
            color="gray"
            size="sm"
            onClick={close}
          >
            ✕
          </ActionIcon>
        </Group>
      </div>

      {/* Messages */}
      <div className="otto-messages" ref={scrollRef}>
        {messages.length === 0 ? (
          <div className="otto-empty">
            <div className="otto-empty-icon">🐾</div>
            <Text size="sm" c="dimmed" ta="center">
              Olá! Sou o <strong>Otto</strong>, seu assistente IA.
              <br />
              Como posso ajudar?
            </Text>
          </div>
        ) : (
          messages.map((msg) => (
            <OttoMessage
              key={msg.id}
              message={msg}
              onFormSubmit={submitForm}
              onInteractiveRespond={respondInteractive}
            />
          ))
        )}
        {status === 'streaming' && messages[messages.length - 1]?.role !== 'assistant' && (
          <div className="otto-typing">
            <Loader size="xs" type="dots" />
          </div>
        )}
      </div>

      {/* Input — TipTap rich editor */}
      <div className="otto-input-area">
        <ChatInput onSend={handleSend} onStop={handleStop} />
      </div>
    </div>
  );
}
