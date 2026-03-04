import { ScrollArea, Text } from '@mantine/core'
import { IconMessageChatbot } from '@tabler/icons-react'
import { useAutoScroll } from './hooks/useAutoScroll'
import { useChatStore } from './state/useChatStore'
import { MessageBubble } from './MessageBubble'

interface MessageListProps {
    onRegenerate?: (messageId: string) => void
}

export function MessageList({ onRegenerate }: MessageListProps) {
    const messages = useChatStore((s) => s.messages)
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
                        />
                    ))}
                </div>
            </ScrollArea>
        </div>
    )
}
