import { useCallback, useRef, useState } from 'react'
import { Badge, Group, ActionIcon, Tooltip, Text, rem } from '@mantine/core'
import { Dropzone, type FileWithPath } from '@mantine/dropzone'
import {
    IconRobot,
    IconArrowLeft,
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
import type { Message, ImageContent, FileContent } from './types/chat'

import './chat.css'

function generateId(): string {
    return `msg_${Date.now()}_${Math.random().toString(36).substring(2, 9)}`
}

/**
 * Mock assistant response — used only when no `onSendMessage` callback is provided.
 * Useful for demos, previews, Storybook, etc.
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
 *
 * @param text - Plain text of the user message
 * @param history - Conversation history (role + content pairs)
 * @param assistantMessageId - Pre-created assistant message ID to stream into
 */
export type OnSendMessageFn = (
    text: string,
    history: Array<{ role: string; content: string }>,
    assistantMessageId: string,
) => void

interface ChatPanelProps {
    onNavigateBack?: () => void
    showContextPanel?: boolean
    /**
     * When provided, the ChatPanel delegates message sending to this callback
     * instead of using the built-in mock response.
     * The consumer is responsible for streaming tokens into useChatStore.
     */
    onSendMessage?: OnSendMessageFn
    /**
     * Enable demo/preview mode with mock responses.
     * When false (default) and onSendMessage is not provided,
     * an error message is shown instead of a mock response.
     */
    demo?: boolean
}

export function ChatPanel({ onNavigateBack, showContextPanel = false, onSendMessage, demo = false }: ChatPanelProps) {
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

    /**
     * Extract plain text from Message content array.
     */
    const extractText = useCallback((message: Message): string => {
        return message.content
            .filter((c): c is { type: 'text'; text: string } => c.type === 'text')
            .map((c) => c.text)
            .join('\n')
            .trim()
    }, [])

    /**
     * Build conversation history from current store messages.
     */
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

                // Clean up preview URLs
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
                // Delegate to consumer — they handle streaming via useChatStore
                const text = extractText(userMessage)
                const history = buildHistory()
                onSendMessage(text, history, assistantId)
            } else if (demo) {
                // Demo mode: mock response
                mockStreamResponse(assistantId, appendStreamToken, updateMessage, setStreaming)
            } else {
                // Production: show error — onSendMessage is required
                console.error('[ChatPanel] onSendMessage não foi fornecido. O chat não está conectado ao backend.')
                updateMessage(assistantId, {
                    content: [{ type: 'text', text: '⚠️ **Erro:** O chat não está conectado ao servidor. Verifique a configuração do componente.' }],
                    isStreaming: false,
                })
                setStreaming(false)
            }
        },
        [addMessage, appendStreamToken, updateMessage, setStreaming, attachments, onSendMessage, extractText, buildHistory]
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
                // Find the last user message to regenerate from
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
                console.error('[ChatPanel] onSendMessage não foi fornecido. O chat não está conectado ao backend.')
                updateMessage(newAssistantId, {
                    content: [{ type: 'text', text: '⚠️ **Erro:** O chat não está conectado ao servidor. Verifique a configuração do componente.' }],
                    isStreaming: false,
                })
                setStreaming(false)
            }
        },
        [addMessage, appendStreamToken, updateMessage, setStreaming, onSendMessage, buildHistory]
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
                        <Tooltip label="Voltar" withArrow>
                            <ActionIcon
                                variant="subtle"
                                color="gray"
                                size="md"
                                onClick={onNavigateBack}
                            >
                                <IconArrowLeft size={18} />
                            </ActionIcon>
                        </Tooltip>
                        <div className="chat-header__avatar">
                            <IconRobot size={18} />
                        </div>
                        <div className="chat-header__info">
                            <span className="chat-header__title">Otto AI</span>
                            <span className="chat-header__status">
                                {isStreaming ? (
                                    <>
                                        <span className="chat-header__status-dot" />
                                        Gerando resposta...
                                    </>
                                ) : (
                                    'Pronto para ajudar'
                                )}
                            </span>
                        </div>
                    </div>
                    <Group gap={4}>
                        <Badge variant="dot" color="green" size="sm">
                            Gemini
                        </Badge>
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
                <MessageList onRegenerate={handleRegenerate} />

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
