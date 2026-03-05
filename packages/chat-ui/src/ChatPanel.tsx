import { useCallback, useRef, useState } from 'react'
import { Badge, Group, ActionIcon, Tooltip, Text, rem } from '@mantine/core'
import { Dropzone, type FileWithPath } from '@mantine/dropzone'
import {
    IconRobot,
    IconHistory,
    IconPlus,
    IconUpload,
    IconX,
} from '@tabler/icons-react'

import { MessageList } from './MessageList'
import { ChatInput } from './ChatInput/ChatInput'
import { ChatToolbar } from './ChatToolbar'
import { ContextPanel } from './ContextPanel'
import { SessionSidebar } from './SessionSidebar'
import {
    AttachmentPreview,
    createAttachmentFile,
    fileToBase64,
    type AttachmentFile,
} from './ChatInput/AttachmentPreview'
import { useChatStore } from './state/useChatStore'
import type { Message, ImageContent, FileContent, FormField } from './types/chat'

import './chat.css'

function generateId(): string {
    return `msg_${Date.now()}_${Math.random().toString(36).substring(2, 9)}`
}

/**
 * Mock assistant response — used only when no `onSendMessage` callback is provided.
 */
function mockStreamResponse(
    messageId: string,
    appendStreamToken: (id: string, token: string) => void,
    updateMessage: (id: string, updates: Partial<Message>) => void,
    setStreaming: (v: boolean) => void
) {
    const response = `Olá! Sou o **Otto**, seu assistente IA do AutoSystem. 👋

Posso ajudar você com diversas tarefas do ERP:

### O que posso fazer:

1. **Consultar dados** — Buscar informações de clientes, produtos, financeiro
2. **Executar workflows** — Rodar processos automatizados como fechamento de caixa
3. **Gerar relatórios** — Criar análises e dashboards personalizados

> 💡 **Dica:** Use \`@\` para mencionar agentes, \`/\` para workflows e \`\${}\` para skills.

Como posso ajudar? 🚀`

    const tokens = response.split('')
    let index = 0

    const interval = setInterval(() => {
        if (index < tokens.length) {
            appendStreamToken(messageId, tokens[index])
            index++
        } else {
            clearInterval(interval)
            updateMessage(messageId, { isStreaming: false })
            setStreaming(false)
        }
    }, 12)

    return () => clearInterval(interval)
}

// Accepted file types
const ACCEPTED_TYPES = [
    'image/png',
    'image/jpeg',
    'image/gif',
    'image/webp',
    'application/pdf',
    'text/plain',
    'text/csv',
    'application/json',
]

/**
 * Callback invoked when the user sends a message.
 * The consumer should handle streaming and populate useChatStore directly.
 */
export type OnSendMessageFn = (
    text: string,
    history: Array<{ role: string; content: string }>,
    assistantMessageId: string,
) => void

interface ChatPanelProps {
    /** Close the chat panel */
    onClose?: () => void
    /** Start new chat (reset) */
    onNewChat?: () => void
    showContextPanel?: boolean
    /** Title displayed in the header */
    title?: string
    /** Subtitle / context info */
    subtitle?: string
    /**
     * When provided, the ChatPanel delegates message sending to this callback.
     * The consumer is responsible for streaming tokens into useChatStore.
     */
    onSendMessage?: OnSendMessageFn
    /** Enable demo mode with mock responses */
    demo?: boolean
    /** Callback for form submissions inside messages */
    onFormSubmit?: (messageId: string, values: Record<string, unknown>) => void
    /** Callback for interactive message responses */
    onInteractiveRespond?: (messageId: string, value: string) => void
    /** Render prop for custom components (e.g. ComponentRegistry) */
    renderComponent?: (name: string, props: Record<string, unknown>) => React.ReactNode
    /** Render prop for inline forms (e.g. DynamicForm) */
    renderForm?: (
        fields: FormField[],
        initialValues: Record<string, unknown>,
        onSubmit: (values: Record<string, unknown>) => void,
    ) => React.ReactNode
}

export function ChatPanel({
    onClose,
    onNewChat,
    showContextPanel = false,
    title = 'Otto AI',
    subtitle,
    onSendMessage,
    demo = false,
    onFormSubmit,
    onInteractiveRespond,
    renderComponent,
    renderForm,
}: ChatPanelProps) {
    const dropzoneRef = useRef<() => void>(null)
    const [attachments, setAttachments] = useState<AttachmentFile[]>([])
    const [isDragging, setIsDragging] = useState(false)

    const {
        addMessage,
        appendStreamToken,
        updateMessage,
        setStreaming,
        isStreaming,
    } = useChatStore()

    // Handle files dropped or selected
    const handleFilesAdded = useCallback((files: FileWithPath[]) => {
        const newAttachments = files.map(createAttachmentFile)
        setAttachments((prev) => [...prev, ...newAttachments])
        setIsDragging(false)
    }, [])

    const handleRemoveAttachment = useCallback((id: string) => {
        setAttachments((prev) => {
            const att = prev.find((a) => a.id === id)
            if (att?.previewUrl) URL.revokeObjectURL(att.previewUrl)
            return prev.filter((a) => a.id !== id)
        })
    }, [])

    const extractText = useCallback((message: Message): string => {
        return message.content
            .filter((c): c is { type: 'text'; text: string } => c.type === 'text')
            .map((c) => c.text)
            .join('\n')
            .trim()
    }, [])

    const buildHistory = useCallback((): Array<{ role: string; content: string }> => {
        return useChatStore.getState().messages
            .filter((m) => m.role === 'user' || m.role === 'assistant')
            .map((m) => ({
                role: m.role,
                content: m.content
                    .filter((c): c is { type: 'text'; text: string } => c.type === 'text')
                    .map((c) => c.text)
                    .join('\n'),
            }))
            .filter((m) => m.content.trim().length > 0)
    }, [])

    const handleSend = useCallback(
        async (userMessage: Message) => {
            // Add attachments to message content
            if (attachments.length > 0) {
                const extraContent: (ImageContent | FileContent)[] = []

                for (const att of attachments) {
                    if (att.file.type.startsWith('image/')) {
                        const base64 = await fileToBase64(att.file)
                        extraContent.push({
                            type: 'image',
                            url: base64,
                            alt: att.file.name,
                            mimeType: att.file.type,
                        })
                    } else {
                        extraContent.push({
                            type: 'file',
                            name: att.file.name,
                            url: att.previewUrl || '',
                            size: att.file.size,
                            mimeType: att.file.type,
                        })
                    }
                }

                userMessage = {
                    ...userMessage,
                    content: [...userMessage.content, ...extraContent],
                }

                attachments.forEach((att) => {
                    if (att.previewUrl) URL.revokeObjectURL(att.previewUrl)
                })
                setAttachments([])
            }

            // Add the user message
            addMessage(userMessage)

            // Create assistant streaming message
            const assistantId = generateId()
            const assistantMsg: Message = {
                id: assistantId,
                role: 'assistant',
                content: [{ type: 'text', text: '' }],
                timestamp: new Date(),
                isStreaming: true,
            }

            addMessage(assistantMsg)
            setStreaming(true)

            if (onSendMessage) {
                const text = extractText(userMessage)
                const history = buildHistory()
                onSendMessage(text, history, assistantId)
            } else if (demo) {
                mockStreamResponse(assistantId, appendStreamToken, updateMessage, setStreaming)
            } else {
                console.error('[ChatPanel] onSendMessage não foi fornecido.')
                updateMessage(assistantId, {
                    content: [{ type: 'text', text: '⚠️ **Erro:** O chat não está conectado ao servidor.' }],
                    isStreaming: false,
                })
                setStreaming(false)
            }
        },
        [addMessage, appendStreamToken, updateMessage, setStreaming, attachments, onSendMessage, extractText, buildHistory, demo]
    )

    const handleStop = useCallback(() => {
        setStreaming(false)
        const messages = useChatStore.getState().messages
        messages.forEach((msg) => {
            if (msg.isStreaming) {
                updateMessage(msg.id, { isStreaming: false })
            }
        })
    }, [setStreaming, updateMessage])

    const handleRegenerate = useCallback(
        (messageId: string) => {
            const messages = useChatStore.getState().messages
            const msgIndex = messages.findIndex((m) => m.id === messageId)
            if (msgIndex === -1) return

            useChatStore.getState().removeMessage(messageId)

            const newAssistantId = generateId()
            const newAssistantMsg: Message = {
                id: newAssistantId,
                role: 'assistant',
                content: [{ type: 'text', text: '' }],
                timestamp: new Date(),
                isStreaming: true,
            }

            addMessage(newAssistantMsg)
            setStreaming(true)

            if (onSendMessage) {
                const lastUserMsg = messages
                    .slice(0, msgIndex)
                    .reverse()
                    .find((m) => m.role === 'user')
                const text = lastUserMsg ? lastUserMsg.content
                    .filter((c): c is { type: 'text'; text: string } => c.type === 'text')
                    .map((c) => c.text)
                    .join('\n')
                    .trim() : ''
                const history = buildHistory()
                onSendMessage(text, history, newAssistantId)
            } else if (demo) {
                mockStreamResponse(newAssistantId, appendStreamToken, updateMessage, setStreaming)
            } else {
                updateMessage(newAssistantId, {
                    content: [{ type: 'text', text: '⚠️ **Erro:** O chat não está conectado ao servidor.' }],
                    isStreaming: false,
                })
                setStreaming(false)
            }
        },
        [addMessage, appendStreamToken, updateMessage, setStreaming, onSendMessage, buildHistory, demo]
    )

    const handleAttachClick = useCallback(() => {
        dropzoneRef.current?.()
    }, [])

    return (
        <div className="chat-layout">
            {/* Session Sidebar */}
            <SessionSidebar />

            {/* Main Chat Panel */}
            <div className="chat-panel">
                {/* Header */}
                <div className="chat-header">
                    <div className="chat-header__left">
                        <div className="chat-header__avatar">
                            <IconRobot size={18} />
                        </div>
                        <div className="chat-header__info">
                            <span className="chat-header__title">{title}</span>
                            <span className="chat-header__status">
                                {isStreaming ? (
                                    <>
                                        <span className="chat-header__status-dot" />
                                        Gerando resposta...
                                    </>
                                ) : (
                                    subtitle || 'Pronto para ajudar'
                                )}
                            </span>
                        </div>
                    </div>
                    <Group gap={4}>
                        <Badge variant="dot" color="green" size="sm">
                            Gemini
                        </Badge>
                        <Tooltip label="Histórico" withArrow position="bottom">
                            <ActionIcon variant="subtle" color="gray" size="sm">
                                <IconHistory size={16} />
                            </ActionIcon>
                        </Tooltip>
                        {onNewChat && (
                            <Tooltip label="Nova conversa" withArrow position="bottom">
                                <ActionIcon variant="subtle" color="gray" size="sm" onClick={onNewChat}>
                                    <IconPlus size={16} />
                                </ActionIcon>
                            </Tooltip>
                        )}
                        {onClose && (
                            <Tooltip label="Fechar" withArrow position="bottom">
                                <ActionIcon variant="subtle" color="gray" size="sm" onClick={onClose}>
                                    <IconX size={16} />
                                </ActionIcon>
                            </Tooltip>
                        )}
                    </Group>
                </div>

                {/* Dropzone overlay */}
                <Dropzone.FullScreen
                    active={isDragging}
                    accept={ACCEPTED_TYPES}
                    onDrop={handleFilesAdded}
                    onDragEnter={() => setIsDragging(true)}
                    onDragLeave={() => setIsDragging(false)}
                >
                    <Group
                        justify="center"
                        gap="xl"
                        mih={220}
                        style={{ pointerEvents: 'none' }}
                    >
                        <Dropzone.Accept>
                            <IconUpload
                                style={{ width: rem(52), height: rem(52), color: 'var(--accent)' }}
                                stroke={1.5}
                            />
                        </Dropzone.Accept>
                        <Dropzone.Reject>
                            <IconX
                                style={{ width: rem(52), height: rem(52), color: 'var(--danger)' }}
                                stroke={1.5}
                            />
                        </Dropzone.Reject>
                        <Dropzone.Idle>
                            <IconUpload
                                style={{ width: rem(52), height: rem(52), color: 'var(--text-muted)' }}
                                stroke={1.5}
                            />
                        </Dropzone.Idle>
                        <div>
                            <Text size="xl" inline>
                                Solte arquivos aqui
                            </Text>
                            <Text size="sm" c="dimmed" inline mt={7}>
                                Imagens, PDFs, CSVs, JSONs e texto
                            </Text>
                        </div>
                    </Group>
                </Dropzone.FullScreen>

                {/* Messages */}
                <MessageList
                    onRegenerate={handleRegenerate}
                    onFormSubmit={onFormSubmit}
                    onInteractiveRespond={onInteractiveRespond}
                    renderComponent={renderComponent}
                    renderForm={renderForm}
                />

                {/* Input area */}
                <div>
                    <AttachmentPreview
                        attachments={attachments}
                        onRemove={handleRemoveAttachment}
                    />
                    <ChatToolbar onAttach={handleAttachClick} />
                    <Dropzone
                        openRef={dropzoneRef}
                        onDrop={handleFilesAdded}
                        accept={ACCEPTED_TYPES}
                        style={{ display: 'none' }}
                    >
                        {null}
                    </Dropzone>
                    <ChatInput onSend={handleSend} onStop={handleStop} />
                </div>
            </div>

            {/* Context Panel */}
            {showContextPanel && <ContextPanel />}
        </div>
    )
}
