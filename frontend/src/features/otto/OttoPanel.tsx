/**
 * OttoPanel — Sleek side panel chat, inspired by VS Code Copilot.
 *
 * Single column, ~400px wide, renders in AppShell.Aside.
 * Uses ChatInput (TipTap) and MarkdownRenderer from @erp-dsl/chat-ui.
 */

import { ActionIcon, Badge, Loader, ScrollArea, Text, Tooltip } from '@mantine/core';
import { useCallback, useEffect, useRef } from 'react';
import { ChatInput } from '@erp-dsl/chat-ui';
import {
  IconRobot,
  IconPlus,
  IconHistory,
  IconX,
} from '@tabler/icons-react';
import { OttoMessage } from './OttoMessage';
import { useOttoContext } from './OttoProvider';
import type { Message } from '@erp-dsl/chat-ui';

import './otto-panel.css';

export function OttoPanel() {
  const { close, context, messages, status, send, reset, submitForm, respondInteractive } = useOttoContext();
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (scrollRef.current) {
      const viewport = scrollRef.current.querySelector('[data-radix-scroll-area-viewport]') ||
        scrollRef.current.querySelector('.mantine-ScrollArea-viewport');
      if (viewport) {
        viewport.scrollTop = viewport.scrollHeight;
      }
    }
  }, [messages]);

  const handleSend = useCallback((msg: Message) => {
    const text = msg.content
      .filter((c): c is { type: 'text'; text: string } => c.type === 'text')
      .map((c) => c.text)
      .join('\n')
      .trim();

    if (!text || status === 'streaming') return;
    send(text, context.pageKey);
  }, [status, send, context.pageKey]);

  const handleStop = useCallback(() => {
    // SSE abort handled in useOtto
  }, []);

  const subtitle = context.pageTitle ? ` · ${context.pageTitle}` : '';

  return (
    <div className="copilot-panel">
      {/* ── Header ─ */}
      <div className="copilot-header">
        <div className="copilot-header__left">
          <div className="copilot-header__avatar">
            <IconRobot size={16} />
          </div>
          <div className="copilot-header__info">
            <span className="copilot-header__title">Otto</span>
            {subtitle && <span className="copilot-header__ctx">{subtitle}</span>}
          </div>
        </div>
        <div className="copilot-header__right">
          <Badge variant="dot" color="green" size="xs">Gemini</Badge>
          <Tooltip label="Histórico" withArrow position="bottom">
            <ActionIcon variant="subtle" color="gray" size="xs">
              <IconHistory size={14} />
            </ActionIcon>
          </Tooltip>
          <Tooltip label="Nova conversa" withArrow position="bottom">
            <ActionIcon variant="subtle" color="gray" size="xs" onClick={reset}>
              <IconPlus size={14} />
            </ActionIcon>
          </Tooltip>
          <Tooltip label="Fechar" withArrow position="bottom">
            <ActionIcon variant="subtle" color="gray" size="xs" onClick={close}>
              <IconX size={14} />
            </ActionIcon>
          </Tooltip>
        </div>
      </div>

      {/* ── Status bar ─ */}
      {status === 'streaming' && (
        <div className="copilot-status">
          <Loader size={10} type="dots" color="var(--accent)" />
          <Text size="xs" c="dimmed">Gerando resposta…</Text>
        </div>
      )}

      {/* ── Messages ─ */}
      <ScrollArea className="copilot-messages" ref={scrollRef} type="auto" scrollbarSize={4}>
        {messages.length === 0 ? (
          <div className="copilot-empty">
            <div className="copilot-empty__icon">
              <IconRobot size={32} stroke={1.2} />
            </div>
            <Text size="sm" fw={600}>Olá! Sou o Otto</Text>
            <Text size="xs" c="dimmed" ta="center" maw={260}>
              Seu assistente IA. Pergunte qualquer coisa, use{' '}
              <code>@</code> agentes, <code>/</code> workflows.
            </Text>
          </div>
        ) : (
          <div className="copilot-message-list">
            {messages.map((msg) => (
              <OttoMessage
                key={msg.id}
                message={msg}
                onFormSubmit={submitForm}
                onInteractiveRespond={respondInteractive}
              />
            ))}
            {status === 'streaming' && (
              <div className="copilot-typing">
                <div className="copilot-typing__dots">
                  <span className="copilot-typing__dot" />
                  <span className="copilot-typing__dot" />
                  <span className="copilot-typing__dot" />
                </div>
                <span className="copilot-typing__label">Otto está pensando…</span>
              </div>
            )}
          </div>
        )}
      </ScrollArea>

      {/* ── Input ─ */}
      <div className="copilot-input">
        <ChatInput onSend={handleSend} onStop={handleStop} />
      </div>
    </div>
  );
}
