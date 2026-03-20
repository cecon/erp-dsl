/**
 * ForgePanel — Side panel for the Cappy autonomous coding agent.
 *
 * Displays a task input and a live log stream of the agent's actions.
 * Logs are grouped by iteration and expandable via accordion.
 */

import { ActionIcon, Badge, Loader, ScrollArea, Text, TextInput, Tooltip, Anchor, Collapse } from '@mantine/core';
import { useCallback, useEffect, useRef, useState } from 'react';
import {
  IconTools,
  IconPlus,
  IconX,
  IconBrandGithub,
  IconSend,
  IconChevronRight,
  IconBrain,
  IconTerminal2,
  IconGitBranch,
  IconAlertTriangle,
  IconCircleCheck,
  IconInfoCircle,
  IconClipboardList,
} from '@tabler/icons-react';
import { useForgeContext } from './ForgeProvider';
import type { ForgeCategory, ForgeMessage } from './types';
import './forge.css';

/* ── Helpers ─────────────────────────────────────────────── */

const CATEGORY_CONFIG: Record<ForgeCategory, {
  icon: typeof IconInfoCircle;
  colorClass: string;
  label: string;
}> = {
  thinking:    { icon: IconBrain,          colorClass: 'forge-cat--thinking',    label: 'Pensando' },
  tool:        { icon: IconTerminal2,      colorClass: 'forge-cat--tool',        label: 'Tool' },
  tool_result: { icon: IconClipboardList,  colorClass: 'forge-cat--tool-result', label: 'Resultado' },
  git:         { icon: IconGitBranch,      colorClass: 'forge-cat--git',         label: 'Git' },
  status:      { icon: IconCircleCheck,    colorClass: 'forge-cat--status',      label: 'Status' },
  warning:     { icon: IconAlertTriangle,  colorClass: 'forge-cat--warning',     label: 'Aviso' },
  error:       { icon: IconAlertTriangle,  colorClass: 'forge-cat--error',       label: 'Erro' },
  info:        { icon: IconInfoCircle,     colorClass: 'forge-cat--info',        label: 'Info' },
};

/** Group messages into iterations (split on category === 'status' + message contains 'Iteração') */
interface IterationGroup {
  label: string;
  messages: ForgeMessage[];
}

function groupByIteration(messages: ForgeMessage[]): { preMessages: ForgeMessage[]; iterations: IterationGroup[] } {
  const preMessages: ForgeMessage[] = [];
  const iterations: IterationGroup[] = [];
  let current: IterationGroup | null = null;

  for (const msg of messages) {
    const isIterationStart = msg.category === 'status' && msg.message.includes('Iteração');

    if (isIterationStart) {
      current = { label: msg.message, messages: [] };
      iterations.push(current);
    } else if (current) {
      current.messages.push(msg);
    } else {
      preMessages.push(msg);
    }
  }
  return { preMessages, iterations };
}

/* ── Components ──────────────────────────────────────────── */

function CategoryIcon({ category }: { category: ForgeCategory }) {
  const config = CATEGORY_CONFIG[category] || CATEGORY_CONFIG.info;
  const Icon = config.icon;
  return <Icon size={13} className={`forge-cat-icon ${config.colorClass}`} />;
}

function ForgeLogLine({ msg }: { msg: ForgeMessage }) {
  const isError = msg.type === 'error' || msg.category === 'error';
  const isDone = msg.type === 'done';
  const config = CATEGORY_CONFIG[msg.category] || CATEGORY_CONFIG.info;

  return (
    <div className={`forge-log-line ${config.colorClass} ${isError ? 'forge-log-error' : ''} ${isDone ? 'forge-log-done' : ''}`}>
      <div className="forge-log-line__content">
        <CategoryIcon category={msg.category} />
        {msg.prUrl ? (
          <Anchor href={msg.prUrl} target="_blank" size="xs" className="forge-pr-link">
            <IconBrandGithub size={12} />
            {' '}Pull Request aberto →
          </Anchor>
        ) : (
          <Text size="xs" ff="monospace" className="forge-log-text">
            {msg.message}
          </Text>
        )}
      </div>
      <Text size="10px" c="dimmed" className="forge-log-time">
        {new Date(msg.timestamp).toLocaleTimeString()}
      </Text>
    </div>
  );
}

function IterationAccordion({ group, index, isLast }: { group: IterationGroup; index: number; isLast: boolean }) {
  const [opened, setOpened] = useState(isLast);

  // Auto-expand the latest iteration
  useEffect(() => {
    if (isLast) setOpened(true);
  }, [isLast]);

  const hasThinking = group.messages.some(m => m.category === 'thinking');
  const hasTools = group.messages.some(m => m.category === 'tool');
  const hasDone = group.messages.some(m => m.message.includes('finalizou'));

  return (
    <div className={`forge-iteration ${opened ? 'forge-iteration--open' : ''}`}>
      <button
        className="forge-iteration__header"
        onClick={() => setOpened(v => !v)}
        type="button"
      >
        <IconChevronRight
          size={14}
          className={`forge-iteration__chevron ${opened ? 'forge-iteration__chevron--open' : ''}`}
        />
        <span className="forge-iteration__label">{group.label}</span>
        <div className="forge-iteration__badges">
          {hasThinking && <span className="forge-iter-badge forge-iter-badge--thinking">🧠</span>}
          {hasTools && <span className="forge-iter-badge forge-iter-badge--tool">🔧</span>}
          {hasDone && <span className="forge-iter-badge forge-iter-badge--done">✅</span>}
        </div>
      </button>
      <Collapse in={opened}>
        <div className="forge-iteration__body">
          {group.messages.map(msg => (
            <ForgeLogLine key={msg.id} msg={msg} />
          ))}
        </div>
      </Collapse>
    </div>
  );
}

/* ── Main Panel ──────────────────────────────────────────── */

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

  const { preMessages, iterations } = groupByIteration(messages);

  return (
    <div className="forge-panel">
      {/* ── Header ─ */}
      <div className="forge-header">
        <div className="forge-header__left">
          <div className="forge-header__avatar">
            <IconTools size={16} />
          </div>
          <div className="forge-header__info">
            <span className="forge-header__title">Cappy</span>
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
          <Text size="xs" c="dimmed">Cappy trabalhando…</Text>
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
            <Text size="sm" fw={600}>Cappy Agent</Text>
            <Text size="xs" c="dimmed" ta="center" maw={260}>
              Descreva uma tarefa de desenvolvimento. O Cappy vai clonar o repositório,
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
            {/* Pre-iteration messages (clone, branch, etc) */}
            {preMessages.map(msg => (
              <ForgeLogLine key={msg.id} msg={msg} />
            ))}

            {/* Iteration accordions */}
            {iterations.map((group, i) => (
              <IterationAccordion
                key={`iter-${i}`}
                group={group}
                index={i}
                isLast={i === iterations.length - 1}
              />
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
