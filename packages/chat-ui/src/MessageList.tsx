import { ScrollArea, Text } from '@mantine/core'
import { IconMessageChatbot } from '@tabler/icons-react'
import { useAutoScroll } from './hooks/useAutoScroll'
import { useChatStore } from './state/useChatStore'
import { MessageBubble } from './MessageBubble'
import type { FormField } from './types/chat'

interface MessageListProps {
    onRegenerate?: (messageId: string) => void
    onFormSubmit?: (messageId: string, values: Record<string, unknown>) => void
    onInteractiveRespond?: (messageId: string, value: string) => void
    renderComponent?: (name: string, props: Record<string, unknown>) => React.ReactNode
    renderForm?: (
        fields: FormField[],
        initialValues: Record<string, unknown>,
        onSubmit: (values: Record<string, unknown>) => void,
    ) => React.ReactNode
}

export function MessageList({
    onRegenerate,
    onFormSubmit,
    onInteractiveRespond,
    renderComponent,
    renderForm,
}: MessageListProps) {
    const messages = useChatStore((s) => s.messages)
    const isStreaming = useChatStore((s) => s.isStreaming)
    const { viewportRef, handleScroll } = useAutoScroll([messages])

    if (messages.length === 0) {
        return (
            <div className="chat-messages">
                <div className="chat-messages__empty">
                    <div className="chat-messages__empty-icon">
                        <IconMessageChatbot size={32} />
                    </div>
                    <div className="chat-messages__empty-title">
                        Olá! Sou o Otto
                    </div>
                    <Text className="chat-messages__empty-desc">
                        Seu assistente IA para o AutoSystem. Pergunte qualquer coisa sobre
                        seus dados, workflows, ou peça ajuda com tarefas do ERP.
                    </Text>
                </div>
            </div>
        )
    }

    return (
        <div className="chat-messages">
            <ScrollArea
                h="100%"
                viewportRef={viewportRef}
                onScrollPositionChange={handleScroll}
                scrollbarSize={6}
                type="scroll"
            >
                <div className="chat-messages__list">
                    {messages.map((message) => (
                        <MessageBubble
                            key={message.id}
                            message={message}
                            onRegenerate={onRegenerate}
                            onFormSubmit={onFormSubmit}
                            onInteractiveRespond={onInteractiveRespond}
                            renderComponent={renderComponent}
                            renderForm={renderForm}
                        />
                    ))}
                    {/* Typing indicator */}
                    {isStreaming && (
                        <div className="chat-typing">
                            <div className="chat-typing__dots">
                                <span className="chat-typing__dot" />
                                <span className="chat-typing__dot" />
                                <span className="chat-typing__dot" />
                            </div>
                            <span className="chat-typing__label">Otto está pensando…</span>
                        </div>
                    )}
                </div>
            </ScrollArea>
        </div>
    )
}
