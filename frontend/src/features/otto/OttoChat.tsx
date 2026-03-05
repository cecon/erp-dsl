/**
 * OttoChat — bridge between useOtto (SSE streaming) and ChatPanel (shared UI).
 *
 * Syncs useOtto messages into useChatStore so ChatPanel can render them.
 * Connects ChatPanel callbacks (onSendMessage, onFormSubmit, etc.) to useOtto.
 */

import { useCallback, useEffect, useRef } from 'react';
import { ChatPanel, useChatStore } from '@erp-dsl/chat-ui';
import type { Message, FormField } from '@erp-dsl/chat-ui';
import { useOttoContext } from './OttoProvider';
import { DynamicForm } from '../../core/engine/DynamicForm';
import { getComponent } from '../../core/engine/ComponentRegistry';
import type { OttoMessage } from './types';

/**
 * Convert an OttoMessage (from useOtto) to a chat-ui Message (for useChatStore).
 */
function ottoToMessage(msg: OttoMessage): Message {
  return {
    id: msg.id,
    role: msg.role,
    content: [{ type: 'text', text: msg.content || '' }],
    timestamp: new Date(msg.timestamp),
    isStreaming: msg.streaming,
    toolName: msg.toolName,
    toolResult: msg.toolResult,
    formSchema: msg.formSchema as FormField[] | undefined,
    formData: msg.formData,
    formSubmitted: msg.formSubmitted,
    componentName: msg.componentName,
    componentProps: msg.componentProps,
    interactive: msg.interactive,
    interactiveAnswered: msg.interactiveAnswered,
    interactiveAnswer: msg.interactiveAnswer,
  };
}

export function OttoChat() {
  const {
    close, context, messages, status, send, reset,
    submitForm, respondInteractive,
  } = useOttoContext();

  const { clearMessages } = useChatStore();
  const prevLenRef = useRef(0);

  // Sync useOtto messages → useChatStore
  useEffect(() => {
    const store = useChatStore.getState();

    // Full reset if messages went down (new chat)
    if (messages.length < prevLenRef.current) {
      store.clearMessages();
      messages.forEach((msg) => store.addMessage(ottoToMessage(msg)));
      prevLenRef.current = messages.length;
      return;
    }

    // Incremental: add new messages
    if (messages.length > prevLenRef.current) {
      const newMsgs = messages.slice(prevLenRef.current);
      newMsgs.forEach((msg) => store.addMessage(ottoToMessage(msg)));
    }

    // Update all existing messages (streaming status, content, etc.)
    for (const msg of messages) {
      const existing = store.messages.find((m) => m.id === msg.id);
      if (existing) {
        const converted = ottoToMessage(msg);
        store.updateMessage(msg.id, {
          content: converted.content,
          isStreaming: converted.isStreaming,
          formSubmitted: converted.formSubmitted,
          interactiveAnswered: converted.interactiveAnswered,
          interactiveAnswer: converted.interactiveAnswer,
        });
      }
    }

    prevLenRef.current = messages.length;
  }, [messages]);

  // Sync streaming status
  useEffect(() => {
    useChatStore.getState().setStreaming(status === 'streaming');
  }, [status]);

  // Clear store on unmount / reset
  useEffect(() => {
    return () => {
      clearMessages();
    };
  }, [clearMessages]);

  const handleSendMessage = useCallback(
    (_text: string, _history: Array<{ role: string; content: string }>, _assistantId: string) => {
      // ChatPanel already added user + assistant messages to useChatStore,
      // but useOtto manages its own. Remove the ChatPanel-added ones
      // and let useOtto drive.
      // Actually, we bypass ChatPanel's message management:
      // send() via useOtto will add messages and we'll sync them.

      // Remove the pre-created messages from ChatPanel
      const store = useChatStore.getState();
      // Find and remove the last 2 messages (user + empty assistant) that ChatPanel added
      const allMsgs = store.messages;
      if (allMsgs.length >= 2) {
        const last = allMsgs[allMsgs.length - 1];
        const secondLast = allMsgs[allMsgs.length - 2];
        if (last.id === _assistantId) {
          store.removeMessage(last.id);
        }
        if (secondLast.role === 'user') {
          store.removeMessage(secondLast.id);
        }
      }

      send(_text, context.pageKey);
    },
    [send, context.pageKey]
  );

  const handleNewChat = useCallback(() => {
    reset();
    useChatStore.getState().clearMessages();
    prevLenRef.current = 0;
  }, [reset]);

  const handleFormSubmit = useCallback(
    (messageId: string, values: Record<string, unknown>) => {
      submitForm(messageId, values);
    },
    [submitForm]
  );

  const handleInteractiveRespond = useCallback(
    (messageId: string, value: string) => {
      respondInteractive(messageId, value);
    },
    [respondInteractive]
  );

  const handleRenderComponent = useCallback(
    (name: string, props: Record<string, unknown>): React.ReactNode => {
      const Component = getComponent(name);
      if (!Component) {
        console.warn(`[OttoChat] Component "${name}" not found in ComponentRegistry`);
        return null;
      }
      return <Component {...props} />;
    },
    []
  );

  const handleRenderForm = useCallback(
    (
      fields: FormField[],
      initialValues: Record<string, unknown>,
      onSubmit: (values: Record<string, unknown>) => void,
    ): React.ReactNode => {
      return (
        <DynamicForm
          fields={fields}
          initialValues={initialValues as Record<string, string>}
          onSubmit={onSubmit}
          submitLabel="Enviar"
        />
      );
    },
    []
  );

  const subtitle = context.pageTitle ? `· ${context.pageTitle}` : undefined;

  return (
    <ChatPanel
      title="Otto"
      subtitle={subtitle}
      onClose={close}
      onNewChat={handleNewChat}
      onSendMessage={handleSendMessage}
      onFormSubmit={handleFormSubmit}
      onInteractiveRespond={handleInteractiveRespond}
      renderComponent={handleRenderComponent}
      renderForm={handleRenderForm}
    />
  );
}
