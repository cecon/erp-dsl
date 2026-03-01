/**
 * OttoPanel — integrated side panel for the Otto universal chat.
 *
 * Renders INSIDE AppShell.Aside (pushes main content).
 */

import { TextInput, ActionIcon, Loader, Text, Group } from '@mantine/core';
import { useCallback, useEffect, useRef, useState } from 'react';
import { OttoMessage } from './OttoMessage';
import { useOttoContext } from './OttoProvider';

export function OttoPanel() {
  const { close, context, messages, status, send, reset, submitForm, respondInteractive } = useOttoContext();
  const [input, setInput] = useState('');
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages]);

  const handleSend = useCallback(() => {
    const trimmed = input.trim();
    if (!trimmed || status === 'streaming') return;
    send(trimmed, context.pageKey);
    setInput('');
  }, [input, status, send, context.pageKey]);

  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent) => {
      if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        handleSend();
      }
    },
    [handleSend]
  );

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

      {/* Input */}
      <div className="otto-input-area">
        <TextInput
          placeholder="Digite sua mensagem…"
          value={input}
          onChange={(e) => setInput(e.currentTarget.value)}
          onKeyDown={handleKeyDown}
          disabled={status === 'streaming'}
          size="sm"
          className="otto-input"
          styles={{
            input: {
              background: 'var(--input-bg)',
              border: '1px solid var(--input-border)',
            },
          }}
          rightSection={
            <ActionIcon
              variant="filled"
              color="blue"
              size="sm"
              onClick={handleSend}
              disabled={!input.trim() || status === 'streaming'}
              radius="xl"
            >
              ↑
            </ActionIcon>
          }
        />
      </div>
    </div>
  );
}
