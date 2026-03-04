import { Avatar, Group, ActionIcon, Tooltip, CopyButton } from '@mantine/core'
import {
    IconCopy,
    IconCheck,
    IconRefresh,
    IconThumbUp,
    IconThumbDown,
    IconTrash,
    IconRobot,
    IconUser,
} from '@tabler/icons-react'
import type { Message } from './types/chat'
import { MarkdownRenderer } from './MarkdownRenderer'
import { useChatStore } from './state/useChatStore'

interface MessageBubbleProps {
    message: Message
    onRegenerate?: (messageId: string) => void
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

export function MessageBubble({ message, onRegenerate }: MessageBubbleProps) {
    const removeMessage = useChatStore((s) => s.removeMessage)
    const isUser = message.role === 'user'
    const isAssistant = message.role === 'assistant'
    const textContent = getTextContent(message)

    return (
        <div className={`chat-bubble chat-bubble--${message.role}`}>
            {/* Avatar */}
            <div className="chat-bubble__avatar">
                <Avatar
                    size={32}
                    radius="xl"
                    color={isUser ? 'indigo' : 'violet'}
                    variant="filled"
                >
                    {isUser ? (
                        <IconUser size={16} />
                    ) : (
                        <IconRobot size={16} />
                    )}
                </Avatar>
            </div>

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
                                    size="sm"
                                    variant="subtle"
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
                            <ActionIcon
                                size="sm"
                                variant="subtle"
                                color="gray"
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
                        <ActionIcon
                            size="sm"
                            variant="subtle"
                            color="gray"
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
