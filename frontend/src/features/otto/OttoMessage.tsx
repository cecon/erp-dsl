/**
 * OttoMessage — individual chat bubble component.
 *
 * Renders user, assistant, tool, system, and FORM messages.
 * When role === 'form', renders DynamicForm inline.
 */

import { Text } from '@mantine/core';
import { DynamicForm } from '../../core/engine/DynamicForm';
import type { OttoMessage as OttoMessageType } from './types';

interface OttoMessageProps {
  message: OttoMessageType;
  onFormSubmit?: (messageId: string, values: Record<string, unknown>) => void;
}

export function OttoMessage({ message, onFormSubmit }: OttoMessageProps) {
  const { role, content, toolName, streaming, formSchema, formData, formSubmitted } = message;

  if (role === 'user') {
    return (
      <div className="otto-msg otto-msg--user">
        <Text size="sm">{content}</Text>
      </div>
    );
  }

  if (role === 'form') {
    if (formSubmitted) {
      return (
        <div className="otto-msg otto-msg--form-submitted">
          <div className="otto-msg-tool-header">
            <span className="otto-msg-tool-icon">📋</span>
            <Text size="xs" fw={600}>Formulário enviado</Text>
          </div>
          {content && <Text size="xs" c="dimmed" mt={4}>{content}</Text>}
        </div>
      );
    }

    if (formSchema && formSchema.length > 0) {
      return (
        <div className="otto-msg otto-msg--form">
          {content && <Text size="sm" mb="sm" fw={500}>{content}</Text>}
          <DynamicForm
            fields={formSchema}
            initialValues={(formData ?? {}) as Record<string, string>}
            onSubmit={(values) => onFormSubmit?.(message.id, values)}
            submitLabel="Enviar"
          />
        </div>
      );
    }
  }

  if (role === 'tool') {
    return (
      <div className="otto-msg otto-msg--tool">
        <div className="otto-msg-tool-header">
          <span className="otto-msg-tool-icon">⚙️</span>
          <Text size="xs" fw={600}>{toolName ?? 'Tool'}</Text>
        </div>
        {content && (
          <Text size="xs" c="dimmed" lineClamp={3} mt={4}>
            {content.length > 200 ? content.substring(0, 200) + '…' : content}
          </Text>
        )}
      </div>
    );
  }

  if (role === 'system') {
    return (
      <div className="otto-msg otto-msg--system">
        <Text size="xs" c="dimmed" ta="center">{content}</Text>
      </div>
    );
  }

  // Assistant
  return (
    <div className="otto-msg otto-msg--assistant">
      <Text size="sm" style={{ whiteSpace: 'pre-wrap' }}>
        {content}
        {streaming && <span className="otto-msg-cursor">▊</span>}
      </Text>
    </div>
  );
}
