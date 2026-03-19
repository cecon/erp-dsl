/**
 * ForgePanel — Side panel for the Forge autonomous coding agent.
 *
 * Displays a task input and a live log stream of the agent's actions.
 * The agent works autonomously: clone → code → commit → PR.
 */

import { ActionIcon, Badge, Loader, ScrollArea, Text, TextInput, Tooltip, Anchor } from '@mantine/core';
import { useCallback, useEffect, useRef, useState } from 'react';
import {
  IconTools,
  IconPlus,
  IconX,
  IconBrandGithub,
  IconSend,
} from '@tabler/icons-react';
import { useForgeContext } from './ForgeProvider';
import type { ForgeMessage } from './types';
import './forge.css';

function ForgeLogLine({ msg }: { msg: ForgeMessage }) {
  const isError = msg.type === 'error';
  const isDone = msg.type === 'done';

  return (
    <div className={`forge-log-line ${isError ? 'forge-log-error' : ''} ${isDone ? 'forge-log-done' : ''}`}>
      {msg.prUrl ? (
        <Anchor href={msg.prUrl} target="_blank" size="xs" className="forge-pr-link">
          <IconBrandGithub size={12} />
          {' '}Pull Request aberto →
        </Anchor>
      ) : (
        <Text size="xs" ff="monospace" style={{ whiteSpace: 'pre-wrap', wordBreak: 'break-all' }}>
          {msg.message}
        </Text>
      )}
      <Text size="10px" c="dimmed" className="forge-log-time">
        {new Date(msg.timestamp).toLocaleTimeString()}
      </Text>
    </div>
  );
}

export function ForgePanel() {
  const { close, messages, status, prUrl, error, send, reset } = useForgeContext();
  const scrollRef = useRef<HTMLDivElement>(null);
  const [taskInput, setTaskInput] = useState('');

  // Auto-scroll on new messages
  useEffect(() => {
    if (scrollRef.current) {
      const viewport =
        scrollRef.current.querySelector('[data-radix-scroll-area-viewport]') ||
        scrollRef.current.querySelector('.mantine-ScrollArea-viewport');
      if (viewport) {
        viewport.scrollTop = viewport.scrollHeight;
      }
    }
  }, [messages]);

  const handleSend = useCallback(() => {
    const task = taskInput.trim();
    if (!task || status === 'streaming') return;
    setTaskInput('');
    send(task);
  }, [taskInput, status, send]);

  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent<HTMLInputElement>) => {
      if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        handleSend();
      }
    },
    [handleSend]
  );

  return (
    <div className="forge-panel">
      {/* ── Header ─ */}
      <div className="forge-header">
        <div className="forge-header__left">
          <div className="forge-header__avatar">
            <IconTools size={16} />
          </div>
          <div className="forge-header__info">
            <span className="forge-header__title">Forge</span>
            <span className="forge-header__subtitle">Agente de Programação Autônomo</span>
          </div>
        </div>
        <div className="forge-header__right">
          <Badge variant="dot" color="orange" size="xs">Git + Gemini</Badge>
          <Tooltip label="Nova tarefa" withArrow position="bottom">
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
        <div className="forge-status">
          <Loader size={10} type="dots" color="var(--accent)" />
          <Text size="xs" c="dimmed">Agente trabalhando…</Text>
        </div>
      )}

      {/* ── PR Success Banner ─ */}
      {prUrl && (
        <div className="forge-pr-banner">
          <IconBrandGithub size={14} />
          <Text size="xs">Pull Request aberto com sucesso!</Text>
          <Anchor href={prUrl} target="_blank" size="xs" fw={600}>Ver PR →</Anchor>
        </div>
      )}

      {/* ── Error Banner ─ */}
      {error && status === 'error' && (
        <div className="forge-error-banner">
          <Text size="xs" c="red">{error}</Text>
        </div>
      )}

      {/* ── Log stream ─ */}
      <ScrollArea className="forge-logs" ref={scrollRef} type="auto" scrollbarSize={4}>
        {messages.length === 0 ? (
          <div className="forge-empty">
            <div className="forge-empty__icon">
              <IconTools size={32} stroke={1.2} />
            </div>
            <Text size="sm" fw={600}>Forge Agent</Text>
            <Text size="xs" c="dimmed" ta="center" maw={260}>
              Descreva uma tarefa de desenvolvimento. O Forge vai clonar o repositório,
              fazer as alterações e abrir um Pull Request automaticamente.
            </Text>
            <div className="forge-examples">
              <Text size="xs" c="dimmed" fw={500} mb={4}>Exemplos:</Text>
              <Text size="xs" c="dimmed">• "Adicione um campo 'observacoes' no schema de produto"</Text>
              <Text size="xs" c="dimmed">• "Crie um endpoint REST para exportar dados em CSV"</Text>
              <Text size="xs" c="dimmed">• "Refatore o módulo fiscal para usar dataclasses"</Text>
            </div>
          </div>
        ) : (
          <div className="forge-log-list">
            {messages.map((msg) => (
              <ForgeLogLine key={msg.id} msg={msg} />
            ))}
            {status === 'streaming' && (
              <div className="forge-typing">
                <div className="forge-typing__dots">
                  <span className="forge-typing__dot" />
                  <span className="forge-typing__dot" />
                  <span className="forge-typing__dot" />
                </div>
                <span className="forge-typing__label">Executando…</span>
              </div>
            )}
          </div>
        )}
      </ScrollArea>

      {/* ── Task Input ─ */}
      <div className="forge-input">
        <TextInput
          placeholder="Descreva a tarefa de desenvolvimento…"
          value={taskInput}
          onChange={(e) => setTaskInput(e.currentTarget.value)}
          onKeyDown={handleKeyDown}
          disabled={status === 'streaming'}
          size="sm"
          radius="md"
          rightSection={
            <ActionIcon
              variant="filled"
              color="orange"
              size="sm"
              onClick={handleSend}
              disabled={!taskInput.trim() || status === 'streaming'}
            >
              <IconSend size={14} />
            </ActionIcon>
          }
          styles={{
            input: {
              background: 'var(--input-bg, rgba(255,255,255,0.05))',
              border: '1px solid var(--border-default, rgba(255,255,255,0.1))',
              color: 'var(--text-primary, #fff)',
              fontSize: '13px',
            },
          }}
        />
      </div>
    </div>
  );
}
