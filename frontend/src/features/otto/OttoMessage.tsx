/**
 * OttoMessage — individual chat bubble component.
 *
 * Renders user, assistant, tool, system, form, component,
 * and INTERACTIVE messages (confirm, choice, image-picker, carousel).
 *
 * When role === 'form', renders DynamicForm inline.
 * When role === 'component', resolves from ComponentRegistry by name.
 * When role === 'interactive', renders the appropriate interactive widget.
 * After the user interacts, the component is disabled showing the choice made.
 */

import {
  Button,
  Card,
  Group,
  Image,
  ScrollArea,
  SimpleGrid,
  Stack,
  Text,
} from '@mantine/core';
import { DynamicForm } from '../../core/engine/DynamicForm';
import { getComponent } from '../../core/engine/ComponentRegistry';
import { MarkdownRenderer } from '@erp-dsl/chat-ui';
import type { OttoMessage as OttoMessageType } from './types';

/* eslint-disable @typescript-eslint/no-explicit-any */

interface OttoMessageProps {
  message: OttoMessageType;
  onFormSubmit?: (messageId: string, values: Record<string, unknown>) => void;
  onInteractiveRespond?: (messageId: string, value: string) => void;
}

/* ── Interactive sub-components ─────────────────────────────────── */

function InteractiveConfirm({
  message,
  onRespond,
}: {
  message: OttoMessageType;
  onRespond: (value: string) => void;
}) {
  const i = message.interactive!;
  const answered = message.interactiveAnswered;
  const answer = message.interactiveAnswer;

  return (
    <div className={`otto-interactive-confirm ${answered ? 'otto-interactive--answered' : ''}`}>
      <Text size="sm" fw={500} mb="sm">
        {i.question}
      </Text>
      <Group gap="sm">
        <Button
          variant={answered && answer === 'yes' ? 'filled' : 'light'}
          color="teal"
          size="sm"
          disabled={answered}
          onClick={() => onRespond('yes')}
          className={answered && answer !== 'yes' ? 'otto-interactive-dim' : ''}
        >
          {answered && answer === 'yes' && '✓ '}{i.confirmLabel || 'Confirmar'}
        </Button>
        <Button
          variant={answered && answer === 'no' ? 'filled' : 'light'}
          color="red"
          size="sm"
          disabled={answered}
          onClick={() => onRespond('no')}
          className={answered && answer !== 'no' ? 'otto-interactive-dim' : ''}
        >
          {answered && answer === 'no' && '✕ '}{i.cancelLabel || 'Cancelar'}
        </Button>
      </Group>
    </div>
  );
}

function InteractiveChoice({
  message,
  onRespond,
}: {
  message: OttoMessageType;
  onRespond: (value: string) => void;
}) {
  const i = message.interactive!;
  const answered = message.interactiveAnswered;
  const answer = message.interactiveAnswer;
  const options = i.options || [];

  return (
    <div className={`otto-interactive-choice ${answered ? 'otto-interactive--answered' : ''}`}>
      <Text size="sm" fw={500} mb="sm">
        {i.question}
      </Text>
      <div className="otto-interactive-choice-grid">
        {options.map((opt) => (
          <Button
            key={opt.value}
            variant={answered && answer === opt.value ? 'filled' : 'light'}
            color="blue"
            size="sm"
            disabled={answered}
            onClick={() => onRespond(opt.value)}
            className={answered && answer !== opt.value ? 'otto-interactive-dim' : ''}
          >
            {answered && answer === opt.value && '✓ '}{opt.label}
          </Button>
        ))}
      </div>
    </div>
  );
}

function InteractiveImagePicker({
  message,
  onRespond,
}: {
  message: OttoMessageType;
  onRespond: (value: string) => void;
}) {
  const i = message.interactive!;
  const answered = message.interactiveAnswered;
  const answer = message.interactiveAnswer;
  const images = i.images || [];

  return (
    <div className={`otto-interactive-images ${answered ? 'otto-interactive--answered' : ''}`}>
      <Text size="sm" fw={500} mb="sm">
        {i.question}
      </Text>
      <SimpleGrid cols={3} spacing="sm">
        {images.map((img) => {
          const selected = answered && answer === img.value;
          const dimmed = answered && answer !== img.value;
          return (
            <Card
              key={img.value}
              padding="xs"
              radius="md"
              className={`otto-interactive-image-card ${selected ? 'otto-interactive-image--selected' : ''} ${dimmed ? 'otto-interactive-dim' : ''}`}
              onClick={() => !answered && onRespond(img.value)}
              style={{ cursor: answered ? 'default' : 'pointer' }}
            >
              <Image
                src={img.url}
                alt={img.label}
                height={80}
                radius="sm"
                fit="cover"
              />
              <Text size="xs" ta="center" mt={4} fw={selected ? 600 : 400}>
                {selected && '✓ '}{img.label}
              </Text>
            </Card>
          );
        })}
      </SimpleGrid>
    </div>
  );
}

function InteractiveCarousel({
  message,
  onRespond,
}: {
  message: OttoMessageType;
  onRespond: (value: string) => void;
}) {
  const i = message.interactive!;
  const answered = message.interactiveAnswered;
  const answer = message.interactiveAnswer;
  const items = i.items || [];

  return (
    <div className={`otto-interactive-carousel ${answered ? 'otto-interactive--answered' : ''}`}>
      <Text size="sm" fw={500} mb="sm">
        {i.question}
      </Text>
      <ScrollArea type="auto" scrollbarSize={6}>
        <div className="otto-interactive-carousel-track">
          {items.map((item) => {
            const selected = answered && answer === item.value;
            const dimmed = answered && answer !== item.value;
            return (
              <Card
                key={item.value}
                padding="sm"
                radius="md"
                className={`otto-interactive-carousel-card ${selected ? 'otto-interactive-carousel--selected' : ''} ${dimmed ? 'otto-interactive-dim' : ''}`}
                onClick={() => !answered && onRespond(item.value)}
                style={{ cursor: answered ? 'default' : 'pointer' }}
              >
                <Stack gap={2}>
                  <Text size="sm" fw={700} lineClamp={1}>
                    {selected && '✓ '}{item.title}
                  </Text>
                  <Text size="xs" c="dimmed" lineClamp={2}>
                    {item.subtitle}
                  </Text>
                </Stack>
              </Card>
            );
          })}
        </div>
      </ScrollArea>
    </div>
  );
}

/* ── Main component ─────────────────────────────────────────────── */

export function OttoMessage({ message, onFormSubmit, onInteractiveRespond }: OttoMessageProps) {
  const {
    role, content, toolName, streaming,
    formSchema, formData, formSubmitted,
    componentName, componentProps,
    interactive,
  } = message;

  if (role === 'user') {
    return (
      <div className="otto-msg otto-msg--user">
        <Text size="sm">{content}</Text>
      </div>
    );
  }

  /* ── Interactive ─────────────────────────────────────────────── */
  if (role === 'interactive' && interactive) {
    const handleRespond = (value: string) => {
      onInteractiveRespond?.(message.id, value);
    };

    return (
      <div className="otto-msg otto-msg--interactive">
        {interactive.type === 'confirm' && (
          <InteractiveConfirm message={message} onRespond={handleRespond} />
        )}
        {interactive.type === 'choice' && (
          <InteractiveChoice message={message} onRespond={handleRespond} />
        )}
        {interactive.type === 'image-picker' && (
          <InteractiveImagePicker message={message} onRespond={handleRespond} />
        )}
        {interactive.type === 'carousel' && (
          <InteractiveCarousel message={message} onRespond={handleRespond} />
        )}
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

  if (role === 'component') {
    if (!componentName) {
      return (
        <div className="otto-msg otto-msg--system">
          <Text size="xs" c="dimmed" ta="center">Componente sem nome especificado</Text>
        </div>
      );
    }

    const Component = getComponent(componentName);
    if (!Component) {
      console.warn(`[Otto] Component "${componentName}" not found in ComponentRegistry`);
      return (
        <div className="otto-msg otto-msg--assistant">
          <Text size="sm" style={{ whiteSpace: 'pre-wrap' }}>
            {content || `Componente "${componentName}" não está disponível no momento.`}
          </Text>
        </div>
      );
    }

    return (
      <div className="otto-msg otto-msg--component">
        {content && <Text size="sm" mb="sm" fw={500}>{content}</Text>}
        <Component {...(componentProps || {})} />
      </div>
    );
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
      <MarkdownRenderer content={content || ''} isStreaming={streaming} />
    </div>
  );
}
