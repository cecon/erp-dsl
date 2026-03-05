import { useState } from 'react'
import { Button, Card, Collapse, CopyButton, Group, ActionIcon, Image, ScrollArea, SimpleGrid, Stack, Text, Tooltip } from '@mantine/core'
import {
    IconCopy,
    IconCheck,
    IconRefresh,
    IconThumbUp,
    IconThumbDown,
    IconTrash,
    IconChevronDown,
    IconSettings,
} from '@tabler/icons-react'
import type { Message, FormField } from './types/chat'
import { MarkdownRenderer } from './MarkdownRenderer'
import { useChatStore } from './state/useChatStore'

/* eslint-disable @typescript-eslint/no-explicit-any */

interface MessageBubbleProps {
    message: Message
    onRegenerate?: (messageId: string) => void
    onFormSubmit?: (messageId: string, values: Record<string, unknown>) => void
    onInteractiveRespond?: (messageId: string, value: string) => void
    /**
     * Render prop for custom components (e.g. ComponentRegistry).
     * Consumer returns a React element given the component name and props.
     */
    renderComponent?: (name: string, props: Record<string, unknown>) => React.ReactNode
    /**
     * Render prop for inline forms (e.g. DynamicForm).
     * Consumer returns a React element given the form schema, data, and onSubmit callback.
     */
    renderForm?: (
        fields: FormField[],
        initialValues: Record<string, unknown>,
        onSubmit: (values: Record<string, unknown>) => void,
    ) => React.ReactNode
}

function formatTime(date: Date): string {
    return new Date(date).toLocaleTimeString('pt-BR', {
        hour: '2-digit',
        minute: '2-digit',
    })
}

function getTextContent(message: Message): string {
    return message.content
        .filter((c) => c.type === 'text')
        .map((c) => (c as { text: string }).text)
        .join('')
}

/* ── Tool Call Bubble ────────────────────────────────────────── */

/** Maps technical tool/skill names to friendly Portuguese labels */
const FRIENDLY_TOOL_LABELS: Record<string, string> = {
    get_entity_schema: 'Consultando estrutura de dados…',
    get_page_schema: 'Carregando formulário…',
    alter_page_schema: 'Atualizando formulário…',
    publish_page_version: 'Publicando alterações…',
    create_record: 'Criando registro…',
    update_record: 'Atualizando registro…',
    delete_record: 'Removendo registro…',
    list_records: 'Buscando registros…',
    get_record: 'Consultando registro…',
    classify_ncm: 'Classificando NCM…',
    search_products: 'Buscando produtos…',
    enrich_product: 'Enriquecendo produto…',
    execute_query: 'Executando consulta…',
    run_report: 'Gerando relatório…',
}

function getFriendlyToolLabel(toolName?: string): string {
    if (!toolName) return 'Processando…'
    return FRIENDLY_TOOL_LABELS[toolName] || `Executando ${toolName.replace(/_/g, ' ')}…`
}

function ToolCallBubble({ toolName, content }: { toolName?: string; content?: string }) {
    const [expanded, setExpanded] = useState(false)
    const label = getFriendlyToolLabel(toolName)
    const hasDetails = !!(content && content.trim())

    return (
        <div className="chat-tool-bubble">
            <button
                className="chat-tool-bubble__header"
                onClick={() => hasDetails && setExpanded((v) => !v)}
                style={{ cursor: hasDetails ? 'pointer' : 'default' }}
            >
                <span className="chat-tool-bubble__icon">
                    <IconSettings size={14} />
                </span>
                <Text size="xs" c="dimmed" className="chat-tool-bubble__label">
                    {label}
                </Text>
                {hasDetails && (
                    <span className={`chat-tool-bubble__chevron ${expanded ? 'chat-tool-bubble__chevron--open' : ''}`}>
                        <IconChevronDown size={14} />
                    </span>
                )}
            </button>
            {hasDetails && (
                <Collapse in={expanded}>
                    <div className="chat-tool-bubble__details">
                        <Text size="xs" c="dimmed" style={{ fontFamily: 'monospace', whiteSpace: 'pre-wrap', wordBreak: 'break-all' }}>
                            {content!.length > 500 ? content!.substring(0, 500) + '…' : content}
                        </Text>
                    </div>
                </Collapse>
            )}
        </div>
    )
}

/* ── Interactive sub-components ──────────────────────────────── */

function InteractiveConfirm({ message, onRespond }: { message: Message; onRespond: (v: string) => void }) {
    const i = message.interactive!
    const answered = message.interactiveAnswered
    const answer = message.interactiveAnswer

    return (
        <div className={`chat-interactive-confirm ${answered ? 'chat-interactive--answered' : ''}`}>
            <Text size="sm" fw={500} mb="sm">{i.question}</Text>
            <Group gap="sm">
                <Button
                    variant={answered && answer === 'yes' ? 'filled' : 'light'}
                    color="teal" size="sm" disabled={answered}
                    onClick={() => onRespond('yes')}
                    className={answered && answer !== 'yes' ? 'chat-interactive-dim' : ''}
                >
                    {answered && answer === 'yes' && '✓ '}{i.confirmLabel || 'Confirmar'}
                </Button>
                <Button
                    variant={answered && answer === 'no' ? 'filled' : 'light'}
                    color="red" size="sm" disabled={answered}
                    onClick={() => onRespond('no')}
                    className={answered && answer !== 'no' ? 'chat-interactive-dim' : ''}
                >
                    {answered && answer === 'no' && '✕ '}{i.cancelLabel || 'Cancelar'}
                </Button>
            </Group>
        </div>
    )
}

function InteractiveChoice({ message, onRespond }: { message: Message; onRespond: (v: string) => void }) {
    const i = message.interactive!
    const answered = message.interactiveAnswered
    const answer = message.interactiveAnswer
    const options = i.options || []

    return (
        <div className={`chat-interactive-choice ${answered ? 'chat-interactive--answered' : ''}`}>
            <Text size="sm" fw={500} mb="sm">{i.question}</Text>
            <div className="chat-interactive-choice-grid">
                {options.map((opt) => (
                    <Button key={opt.value}
                        variant={answered && answer === opt.value ? 'filled' : 'light'}
                        color="blue" size="sm" disabled={answered}
                        onClick={() => onRespond(opt.value)}
                        className={answered && answer !== opt.value ? 'chat-interactive-dim' : ''}
                    >
                        {answered && answer === opt.value && '✓ '}{opt.label}
                    </Button>
                ))}
            </div>
        </div>
    )
}

function InteractiveImagePicker({ message, onRespond }: { message: Message; onRespond: (v: string) => void }) {
    const i = message.interactive!
    const answered = message.interactiveAnswered
    const answer = message.interactiveAnswer
    const images = i.images || []

    return (
        <div className={`chat-interactive-images ${answered ? 'chat-interactive--answered' : ''}`}>
            <Text size="sm" fw={500} mb="sm">{i.question}</Text>
            <SimpleGrid cols={3} spacing="sm">
                {images.map((img) => {
                    const selected = answered && answer === img.value
                    const dimmed = answered && answer !== img.value
                    return (
                        <Card key={img.value} padding="xs" radius="md"
                            className={`chat-interactive-image-card ${selected ? 'chat-interactive-image--selected' : ''} ${dimmed ? 'chat-interactive-dim' : ''}`}
                            onClick={() => !answered && onRespond(img.value)}
                            style={{ cursor: answered ? 'default' : 'pointer' }}
                        >
                            <Image src={img.url} alt={img.label} height={80} radius="sm" fit="cover" />
                            <Text size="xs" ta="center" mt={4} fw={selected ? 600 : 400}>
                                {selected && '✓ '}{img.label}
                            </Text>
                        </Card>
                    )
                })}
            </SimpleGrid>
        </div>
    )
}

function InteractiveCarousel({ message, onRespond }: { message: Message; onRespond: (v: string) => void }) {
    const i = message.interactive!
    const answered = message.interactiveAnswered
    const answer = message.interactiveAnswer
    const items = i.items || []

    return (
        <div className={`chat-interactive-carousel ${answered ? 'chat-interactive--answered' : ''}`}>
            <Text size="sm" fw={500} mb="sm">{i.question}</Text>
            <ScrollArea type="auto" scrollbarSize={6}>
                <div className="chat-interactive-carousel-track">
                    {items.map((item) => {
                        const selected = answered && answer === item.value
                        const dimmed = answered && answer !== item.value
                        return (
                            <Card key={item.value} padding="sm" radius="md"
                                className={`chat-interactive-carousel-card ${selected ? 'chat-interactive-carousel--selected' : ''} ${dimmed ? 'chat-interactive-dim' : ''}`}
                                onClick={() => !answered && onRespond(item.value)}
                                style={{ cursor: answered ? 'default' : 'pointer' }}
                            >
                                <Stack gap={2}>
                                    <Text size="sm" fw={700} lineClamp={1}>
                                        {selected && '✓ '}{item.title}
                                    </Text>
                                    <Text size="xs" c="dimmed" lineClamp={2}>{item.subtitle}</Text>
                                </Stack>
                            </Card>
                        )
                    })}
                </div>
            </ScrollArea>
        </div>
    )
}

/* ── Main component ──────────────────────────────────────────── */

export function MessageBubble({
    message,
    onRegenerate,
    onFormSubmit,
    onInteractiveRespond,
    renderComponent,
    renderForm,
}: MessageBubbleProps) {
    const removeMessage = useChatStore((s) => s.removeMessage)
    const { role } = message
    const textContent = getTextContent(message)
    const isUser = role === 'user'
    const isAssistant = role === 'assistant'

    /* ── Tool ──────────────────────────────────────────────────── */
    if (role === 'tool') {
        return (
            <ToolCallBubble
                toolName={message.toolName}
                content={textContent}
            />
        )
    }

    /* ── System ────────────────────────────────────────────────── */
    if (role === 'system') {
        return (
            <div className="chat-bubble chat-bubble--system">
                <Text size="xs" c="dimmed" ta="center">{textContent}</Text>
            </div>
        )
    }

    /* ── Interactive ───────────────────────────────────────────── */
    if (role === 'interactive' && message.interactive) {
        const handleRespond = (value: string) => {
            onInteractiveRespond?.(message.id, value)
        }

        return (
            <div className="chat-bubble chat-bubble--interactive">
                {message.interactive.type === 'confirm' && (
                    <InteractiveConfirm message={message} onRespond={handleRespond} />
                )}
                {message.interactive.type === 'choice' && (
                    <InteractiveChoice message={message} onRespond={handleRespond} />
                )}
                {message.interactive.type === 'image-picker' && (
                    <InteractiveImagePicker message={message} onRespond={handleRespond} />
                )}
                {message.interactive.type === 'carousel' && (
                    <InteractiveCarousel message={message} onRespond={handleRespond} />
                )}
            </div>
        )
    }

    /* ── Form ──────────────────────────────────────────────────── */
    if (role === 'form') {
        if (message.formSubmitted) {
            return (
                <div className="chat-bubble chat-bubble--form-submitted">
                    <div className="chat-bubble__tool-header">
                        <span className="chat-bubble__tool-icon">📋</span>
                        <Text size="xs" fw={600}>Formulário enviado</Text>
                    </div>
                    {textContent && <Text size="xs" c="dimmed" mt={4}>{textContent}</Text>}
                </div>
            )
        }

        if (message.formSchema && message.formSchema.length > 0 && renderForm) {
            return (
                <div className="chat-bubble chat-bubble--form">
                    {textContent && <Text size="sm" mb="sm" fw={500}>{textContent}</Text>}
                    {renderForm(
                        message.formSchema,
                        (message.formData ?? {}) as Record<string, unknown>,
                        (values) => onFormSubmit?.(message.id, values),
                    )}
                </div>
            )
        }
    }

    /* ── Component ────────────────────────────────────────────── */
    if (role === 'component') {
        if (!message.componentName) {
            return (
                <div className="chat-bubble chat-bubble--system">
                    <Text size="xs" c="dimmed" ta="center">Componente sem nome especificado</Text>
                </div>
            )
        }

        if (renderComponent) {
            const rendered = renderComponent(message.componentName, message.componentProps || {})
            if (rendered) {
                return (
                    <div className="chat-bubble chat-bubble--component">
                        {textContent && <Text size="sm" mb="sm" fw={500}>{textContent}</Text>}
                        {rendered}
                    </div>
                )
            }
        }

        // Fallback if no renderComponent or component not found
        return (
            <div className="chat-bubble chat-bubble--component">
                <Text size="sm" c="dimmed">{textContent || `Componente "${message.componentName}" não disponível.`}</Text>
            </div>
        )
    }

    /* ── User / Assistant (default) ───────────────────────────── */
    return (
        <div className={`chat-bubble chat-bubble--${role}`}>

            {/* Body */}
            <div className="chat-bubble__body">
                <div className="chat-bubble__header">
                    <span className="chat-bubble__name">
                        {isUser ? 'Você' : 'Otto'}
                    </span>
                    <span className="chat-bubble__time">
                        {formatTime(message.timestamp)}
                    </span>
                </div>

                <div className="chat-bubble__content">
                    {isUser ? (
                        textContent
                    ) : message.isStreaming && !textContent ? (
                        <div className="streaming-dots">
                            <div className="streaming-dots__dot" />
                            <div className="streaming-dots__dot" />
                            <div className="streaming-dots__dot" />
                        </div>
                    ) : (
                        <MarkdownRenderer
                            content={textContent}
                            isStreaming={message.isStreaming}
                        />
                    )}
                </div>
            </div>

            {/* Hover Toolbar */}
            {!message.isStreaming && (
                <div className="chat-bubble__toolbar">
                    <CopyButton value={textContent}>
                        {({ copied, copy }) => (
                            <Tooltip label={copied ? 'Copiado!' : 'Copiar'} withArrow>
                                <ActionIcon
                                    size="sm" variant="subtle"
                                    color={copied ? 'teal' : 'gray'}
                                    onClick={copy}
                                >
                                    {copied ? <IconCheck size={14} /> : <IconCopy size={14} />}
                                </ActionIcon>
                            </Tooltip>
                        )}
                    </CopyButton>

                    {isAssistant && onRegenerate && (
                        <Tooltip label="Regenerar" withArrow>
                            <ActionIcon size="sm" variant="subtle" color="gray"
                                onClick={() => onRegenerate(message.id)}
                            >
                                <IconRefresh size={14} />
                            </ActionIcon>
                        </Tooltip>
                    )}

                    {isAssistant && (
                        <Group gap={0}>
                            <Tooltip label="Útil" withArrow>
                                <ActionIcon size="sm" variant="subtle" color="gray">
                                    <IconThumbUp size={14} />
                                </ActionIcon>
                            </Tooltip>
                            <Tooltip label="Não útil" withArrow>
                                <ActionIcon size="sm" variant="subtle" color="gray">
                                    <IconThumbDown size={14} />
                                </ActionIcon>
                            </Tooltip>
                        </Group>
                    )}

                    <Tooltip label="Remover" withArrow>
                        <ActionIcon size="sm" variant="subtle" color="gray"
                            onClick={() => removeMessage(message.id)}
                        >
                            <IconTrash size={14} />
                        </ActionIcon>
                    </Tooltip>
                </div>
            )}
        </div>
    )
}
