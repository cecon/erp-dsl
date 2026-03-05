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
 * Mock assistant response for demo purposes.
 * In production, this would be replaced by the SSE streaming hook.
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

#### Exemplo de código:

\`\`\`typescript
const response = await otto.ask({
  question: "Qual o faturamento de hoje?",
  context: { tenant: "loja-01" }
});
\`\`\`

> 💡 **Dica:** Use \`@\` para mencionar agentes, \`/\` para workflows e \`\${}\` para skills.

| Recurso | Status |
|---------|--------|
| Chat | ✅ Ativo |
| Streaming | ✅ Ativo |
| Workflows | 🔜 Em breve |

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

interface ChatPanelProps {
    onNavigateBack?: () => void
    showContextPanel?: boolean
}

export function ChatPanel({ onNavigateBack, showContextPanel = false }: ChatPanelProps) {
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

            // Mock streaming (replace with useOttoStream in production)
            mockStreamResponse(assistantId, appendStreamToken, updateMessage, setStreaming)
        },
        [addMessage, appendStreamToken, updateMessage, setStreaming, attachments]
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
            mockStreamResponse(newAssistantId, appendStreamToken, updateMessage, setStreaming)
        },
        [addMessage, appendStreamToken, updateMessage, setStreaming]
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
