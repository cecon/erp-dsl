/**
 * CappyChat — bridge between useCappy (SSE streaming) and ChatPanel (shared UI).
 *
 * Cada iteração do agente é agrupada em uma única mensagem do assistente.
 * Mensagens de status ("Iteração X") ficam como header,
 * e os detalhes (thinking, tool calls, resultados) ficam em <details> expandível.
 *
 * O campo "task input" é o `onSendMessage`: o usuário digita a tarefa,
 * o Cappy executa e vai postando logs como mensagens do assistente.
 */

import { useCallback, useEffect, useRef } from 'react';
import { ChatPanel, useChatStore } from '@erp-dsl/chat-ui';
import type { Message } from '@erp-dsl/chat-ui';
import { useCappyContext } from './CappyProvider';
import type { CappyCategory, CappyMessage } from './types';

/* ── Category formatters ─────────────────────────────────── */

const CATEGORY_EMOJI: Record<CappyCategory, string> = {
  thinking: '🧠',
  tool: '🔧',
  tool_result: '📋',
  git: '🌿',
  status: '🔄',
  warning: '⚠️',
  error: '❌',
  info: 'ℹ️',
};

function formatLogLine(msg: CappyMessage): string {
  return msg.message;
}

/* ── Iteration grouping ──────────────────────────────────── */

interface IterationGroup {
  label: string;
  messages: CappyMessage[];
}

/**
 * Group CappyMessages into:
 * - preMessages: messages before any iteration (clone, branch, task accepted, etc.)
 * - iterations: groups split on status messages containing 'Iteração'
 * - postMessages: final messages after last iteration (done, error, PR)
 */
function groupMessages(messages: CappyMessage[]): {
  preMessages: CappyMessage[];
  iterations: IterationGroup[];
  postMessages: CappyMessage[];
} {
  const preMessages: CappyMessage[] = [];
  const iterations: IterationGroup[] = [];
  const postMessages: CappyMessage[] = [];
  let current: IterationGroup | null = null;
  let foundDone = false;

  for (const msg of messages) {
    const isIterationStart = msg.category === 'status' && msg.message.includes('Iteração');
    const isDone = msg.category === 'status' && (
      msg.message.includes('finalizou') || msg.message.includes('Pull Request')
    );
    const isError = msg.type === 'error' || msg.category === 'error';

    if (isDone || isError) {
      foundDone = true;
    }

    if (isIterationStart) {
      current = { label: msg.message, messages: [] };
      iterations.push(current);
    } else if (foundDone) {
      postMessages.push(msg);
    } else if (current) {
      current.messages.push(msg);
    } else {
      preMessages.push(msg);
    }
  }
  return { preMessages, iterations, postMessages };
}

/**
 * Build a single markdown string for an iteration group.
 * Shows a summary line + expandable details.
 */
function iterationToMarkdown(group: IterationGroup, isLatest: boolean): string {
  // Summary: what tools were called
  const toolCalls = group.messages.filter(m => m.category === 'tool');
  const hasWarning = group.messages.some(m => m.category === 'warning');

  let summary = group.label;
  if (toolCalls.length > 0) {
    summary += ` — ${toolCalls.length} tool call${toolCalls.length > 1 ? 's' : ''}`;
  }
  if (hasWarning) {
    summary += ' ⚠️';
  }

  // Build detail lines
  const detailLines = group.messages.map(msg => {
    const emoji = CATEGORY_EMOJI[msg.category] || '';
    return `${emoji} ${formatLogLine(msg)}`;
  });

  const detailsContent = detailLines.join('\n\n');

  // Latest iteration is open by default; older ones are collapsed
  if (isLatest) {
    return `**${summary}**\n\n<details open>\n<summary>📝 Ver detalhes</summary>\n\n${detailsContent}\n\n</details>`;
  }
  return `**${summary}**\n\n<details>\n<summary>📝 Ver detalhes</summary>\n\n${detailsContent}\n\n</details>`;
}

/* ── Main Component ──────────────────────────────────────── */

export function CappyChat() {
  const { close, messages, status, prUrl, send, reset } = useCappyContext();
  void prUrl; // used implicitly via messages

  const { clearMessages } = useChatStore();
  const prevSnapshotRef = useRef<string>('');
  const lastTaskRef = useRef<string>('');

  // Sync messages using grouped display
  useEffect(() => {
    const store = useChatStore.getState();
    const { preMessages, iterations, postMessages } = groupMessages(messages);

    // Build the target message list
    const targetMessages: Message[] = [];

    // Pre-iteration messages as individual assistant messages
    for (const msg of preMessages) {
      const isError = msg.type === 'error' || msg.category === 'error';
      let text = msg.message || '';
      if (msg.type === 'done' && msg.prUrl) {
        text = `✅ Tarefa concluída!\n\n📎 [Pull Request aberto](${msg.prUrl})`;
      } else if (isError) {
        text = `❌ ${text}`;
      }

      targetMessages.push({
        id: msg.id,
        role: 'assistant',
        content: [{ type: 'text', text }],
        timestamp: new Date(msg.timestamp),
        isStreaming: false,
      });
    }

    // Each iteration as a single grouped assistant message
    for (let i = 0; i < iterations.length; i++) {
      const group = iterations[i];
      const isLatest = i === iterations.length - 1 && postMessages.length === 0;
      const md = iterationToMarkdown(group, isLatest);

      targetMessages.push({
        id: `cappy-iter-${i}`,
        role: 'assistant',
        content: [{ type: 'text', text: md }],
        timestamp: new Date(group.messages[0]?.timestamp || Date.now()),
        isStreaming: isLatest && status === 'streaming',
      });
    }

    // Post-messages (done, PR, error) as individual messages
    for (const msg of postMessages) {
      let text = msg.message || '';
      if (msg.prUrl) {
        text = `✅ Tarefa concluída!\n\n📎 [Pull Request aberto](${msg.prUrl})`;
      } else if (msg.type === 'done') {
        text = `✅ ${text || 'Tarefa concluída!'}`;
      } else if (msg.type === 'error' || msg.category === 'error') {
        text = `❌ ${text}`;
      }
      targetMessages.push({
        id: msg.id,
        role: 'assistant',
        content: [{ type: 'text', text }],
        timestamp: new Date(msg.timestamp),
        isStreaming: false,
      });
    }

    // Snapshot comparison to avoid unnecessary re-renders
    const snapshot = JSON.stringify(targetMessages.map(m => ({ id: m.id, content: m.content })));
    if (snapshot === prevSnapshotRef.current) return;
    prevSnapshotRef.current = snapshot;

    // Replace all messages in the store
    store.clearMessages();

    // Re-add the user task message if it existed
    if (lastTaskRef.current) {
      store.addMessage({
        id: `cappy-user-task`,
        role: 'user',
        content: [{ type: 'text', text: lastTaskRef.current }],
        timestamp: new Date(),
        isStreaming: false,
      });
    }

    targetMessages.forEach(m => store.addMessage(m));
  }, [messages, status]);

  // Sync streaming status
  useEffect(() => {
    useChatStore.getState().setStreaming(status === 'streaming');
  }, [status]);

  // Limpar store ao desmontar
  useEffect(() => {
    return () => {
      clearMessages();
    };
  }, [clearMessages]);

  const handleSendMessage = useCallback(
    (text: string, _history: Array<{ role: string; content: string }>, assistantId: string) => {
      // Remove mensagens que o ChatPanel pré-criou (user + assistant vazio)
      const store = useChatStore.getState();
      const allMsgs = store.messages;
      if (allMsgs.length >= 2) {
        const last = allMsgs[allMsgs.length - 1];
        const secondLast = allMsgs[allMsgs.length - 2];
        if (last.id === assistantId) {
          store.removeMessage(last.id);
        }
        if (secondLast.role === 'user') {
          store.removeMessage(secondLast.id);
        }
      }

      // Adiciona a tarefa do user ao store manualmente
      store.addMessage({
        id: `cappy-user-${Date.now()}`,
        role: 'user',
        content: [{ type: 'text', text }],
        timestamp: new Date(),
        isStreaming: false,
      });

      lastTaskRef.current = text;
      send(text);
    },
    [send]
  );

  const handleNewChat = useCallback(() => {
    reset();
    useChatStore.getState().clearMessages();
    prevSnapshotRef.current = '';
    lastTaskRef.current = '';
  }, [reset]);

  return (
    <ChatPanel
      title="Cappy"
      subtitle="Agente Autônomo"
      onClose={close}
      onNewChat={handleNewChat}
      onSendMessage={handleSendMessage}
    />
  );
}
