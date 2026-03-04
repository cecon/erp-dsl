import { useState, useMemo } from 'react'
import {
    Text,
    Group,
    ActionIcon,
    Tooltip,
    TextInput,
    ScrollArea,
    Stack,
} from '@mantine/core'
import {
    IconPlus,
    IconSearch,
    IconTrash,
    IconMessageChatbot,
    IconChevronLeft,
    IconChevronRight,
} from '@tabler/icons-react'
import { useChatStore } from './state/useChatStore'
import type { ChatSession } from './types/chat'

interface SessionSidebarProps {
    onNewSession?: () => void
}

// Mock sessions for demo
const MOCK_SESSIONS: ChatSession[] = [
    {
        id: 'session-1',
        title: 'Consulta de faturamento mensal',
        messages: [],
        createdAt: new Date('2026-03-04T15:00:00'),
        updatedAt: new Date('2026-03-04T15:30:00'),
    },
    {
        id: 'session-2',
        title: 'Importação de notas fiscais',
        messages: [],
        createdAt: new Date('2026-03-03T10:00:00'),
        updatedAt: new Date('2026-03-03T11:00:00'),
    },
    {
        id: 'session-3',
        title: 'Classificação NCM de produtos',
        messages: [],
        createdAt: new Date('2026-03-02T14:00:00'),
        updatedAt: new Date('2026-03-02T16:00:00'),
    },
]

function formatRelativeDate(date: Date): string {
    const now = new Date()
    const diffMs = now.getTime() - date.getTime()
    const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24))

    if (diffDays === 0) return 'Hoje'
    if (diffDays === 1) return 'Ontem'
    if (diffDays < 7) return `${diffDays} dias atrás`
    return date.toLocaleDateString('pt-BR', { day: '2-digit', month: 'short' })
}

export function SessionSidebar({ onNewSession }: SessionSidebarProps) {
    const [isOpen, setIsOpen] = useState(false)
    const [search, setSearch] = useState('')
    const clearMessages = useChatStore((s) => s.clearMessages)

    // In production, sessions would come from the store/backend
    const sessions = MOCK_SESSIONS

    const filtered = useMemo(() => {
        if (!search) return sessions
        return sessions.filter((s) =>
            s.title.toLowerCase().includes(search.toLowerCase())
        )
    }, [sessions, search])

    if (!isOpen) {
        return (
            <div className="session-sidebar session-sidebar--collapsed">
                <Tooltip label="Histórico" position="right" withArrow>
                    <ActionIcon
                        variant="subtle"
                        color="gray"
                        size="md"
                        onClick={() => setIsOpen(true)}
                    >
                        <IconChevronRight size={16} />
                    </ActionIcon>
                </Tooltip>
            </div>
        )
    }

    return (
        <div className="session-sidebar session-sidebar--open">
            {/* Header */}
            <div className="session-sidebar__header">
                <Group gap={8}>
                    <IconMessageChatbot size={16} />
                    <Text size="sm" fw={700}>Conversas</Text>
                </Group>
                <Group gap={2}>
                    <Tooltip label="Nova conversa" withArrow>
                        <ActionIcon
                            variant="subtle"
                            color="gray"
                            size="sm"
                            onClick={() => {
                                clearMessages()
                                onNewSession?.()
                            }}
                        >
                            <IconPlus size={14} />
                        </ActionIcon>
                    </Tooltip>
                    <ActionIcon
                        variant="subtle"
                        color="gray"
                        size="sm"
                        onClick={() => setIsOpen(false)}
                    >
                        <IconChevronLeft size={14} />
                    </ActionIcon>
                </Group>
            </div>

            {/* Search */}
            <div className="session-sidebar__search">
                <TextInput
                    placeholder="Buscar conversas..."
                    size="xs"
                    leftSection={<IconSearch size={14} />}
                    value={search}
                    onChange={(e) => setSearch(e.currentTarget.value)}
                    variant="filled"
                    styles={{
                        input: {
                            background: 'rgba(255,255,255,0.04)',
                            border: '1px solid var(--border-default)',
                            fontSize: '12px',
                        },
                    }}
                />
            </div>

            {/* Session list */}
            <ScrollArea flex={1} scrollbarSize={4}>
                <Stack gap={2} p={8}>
                    {filtered.map((session) => (
                        <button
                            key={session.id}
                            className="session-sidebar__item"
                            type="button"
                        >
                            <Text size="xs" fw={600} truncate>
                                {session.title}
                            </Text>
                            <Group gap={8} justify="space-between">
                                <Text size="xs" c="dimmed">
                                    {formatRelativeDate(session.updatedAt)}
                                </Text>
                                <Tooltip label="Excluir" withArrow>
                                    <ActionIcon
                                        size="xs"
                                        variant="subtle"
                                        color="gray"
                                        className="session-sidebar__item-delete"
                                        onClick={(e) => {
                                            e.stopPropagation()
                                            // In production: delete session
                                        }}
                                    >
                                        <IconTrash size={10} />
                                    </ActionIcon>
                                </Tooltip>
                            </Group>
                        </button>
                    ))}

                    {filtered.length === 0 && (
                        <Text size="xs" c="dimmed" ta="center" py="md">
                            Nenhuma conversa encontrada
                        </Text>
                    )}
                </Stack>
            </ScrollArea>
        </div>
    )
}
