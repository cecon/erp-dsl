/**
 * CappyChat — bridge between useCappy (SSE streaming) and ChatPanel (shared UI).
 *
 * Cada mensagem do Cappy é um log de ação do agente autônomo.
 * Usa o mesmo ChatPanel do @erp-dsl/chat-ui que o Otto usa,
 * mapeando os eventos SSE do agente para o formato de mensagens do chat.
 *
 * O campo "task input" é o `onSendMessage`: o usuário digita a tarefa,
 * o Cappy executa e vai postando logs como mensagens do assistente.
 */

import { useCallback, useEffect, useRef } from 'react';
import { ChatPanel, useChatStore } from '@erp-dsl/chat-ui';
import type { Message } from '@erp-dsl/chat-ui';
import { useCappyContext } from './CappyProvider';
import type { CappyMessage } from './types';

/**
 * Converte uma CappyMessage (log do agente) para o formato Message do chat-ui.
 */
function cappyToMessage(msg: CappyMessage): Message {
  const isError = msg.type === 'error';
  const isDone = msg.type === 'done';

  let text = msg.message || '';

  // Mensagens de "done" com PR: adicionar texto especial
  if (isDone && msg.prUrl) {
    text = `✅ Tarefa concluída!\n\n📎 [Pull Request aberto](${msg.prUrl})`;
  } else if (isDone) {
    text = `✅ ${text || 'Tarefa concluída!'}`;
  } else if (isError) {
    text = `❌ ${text}`;
  }

  return {
    id: msg.id,
    // logs do agente aparecem como "assistant"; a tarefa enviada pelo user aparece como "user"
    role: 'assistant',
    content: [{ type: 'text', text }],
    timestamp: new Date(msg.timestamp),
    isStreaming: false,
  };
}

export function CappyChat() {
  const { close, messages, status, prUrl, send, reset } = useCappyContext();

  const { clearMessages } = useChatStore();
  const prevLenRef = useRef(0);
  const lastTaskRef = useRef<string>('');

  // Sync messages do useCappy → useChatStore
  useEffect(() => {
    const store = useChatStore.getState();

    // Reset completo se as mensagens diminuíram (nova tarefa)
    if (messages.length < prevLenRef.current) {
      store.clearMessages();
      messages.forEach((msg) => store.addMessage(cappyToMessage(msg)));
      prevLenRef.current = messages.length;
      return;
    }

    // Incremental: adiciona mensagens novas
    if (messages.length > prevLenRef.current) {
      const newMsgs = messages.slice(prevLenRef.current);
      newMsgs.forEach((msg) => store.addMessage(cappyToMessage(msg)));
    }

    // Atualiza mensagens existentes (ex: status de streaming)
    for (const msg of messages) {
      const existing = store.messages.find((m) => m.id === msg.id);
      if (existing) {
        store.updateMessage(msg.id, {
          content: cappyToMessage(msg).content,
          isStreaming: false,
        });
      }
    }

    prevLenRef.current = messages.length;
  }, [messages]);

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

  // Banner de PR no topo quando concluído
  useEffect(() => {
    if (prUrl) {
      const store = useChatStore.getState();
      // Encontra a mensagem de "done" e atualiza para mostrar o link
      const doneMsg = [...store.messages]
        .reverse()
        .find((m: Message) =>
          m.content.some((c) => c.type === 'text' && (c as { type: 'text'; text: string }).text.includes('Tarefa concluída'))
        );
      if (doneMsg && !doneMsg.content.some((c) => c.type === 'text' && (c as { type: 'text'; text: string }).text.includes(prUrl))) {
        store.updateMessage(doneMsg.id, {
          content: [
            { type: 'text', text: `✅ Tarefa concluída!\n\n📎 [Pull Request aberto](${prUrl})` },
          ],
        });
      }
    }
  }, [prUrl]);

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
    prevLenRef.current = 0;
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
