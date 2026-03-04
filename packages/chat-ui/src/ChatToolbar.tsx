import { Group, ActionIcon, Tooltip, Menu, Text, ThemeIcon } from '@mantine/core'
import {
    IconPaperclip,
    IconRobot,
    IconTrash,
    IconChevronDown,
} from '@tabler/icons-react'
import { useChatStore } from './state/useChatStore'
import type { Agent } from './types/chat'

interface ChatToolbarProps {
    onAttach: () => void
    availableAgents?: Agent[]
    disabled?: boolean
}

// Mock agents for demo
const MOCK_AGENTS: Agent[] = [
    { id: 'otto', name: 'Otto', description: 'Assistente principal' },
    { id: 'fiscal', name: 'Fiscal', description: 'Notas fiscais e tributos' },
    { id: 'financeiro', name: 'Financeiro', description: 'Contas e fluxo de caixa' },
    { id: 'estoque', name: 'Estoque', description: 'Inventário e movimentações' },
]

export function ChatToolbar({ onAttach, availableAgents, disabled }: ChatToolbarProps) {
    const { activeAgentId, setActiveAgent, clearMessages, isStreaming } = useChatStore()
    const agents = availableAgents ?? MOCK_AGENTS
    const activeAgent = agents.find((a) => a.id === activeAgentId) ?? agents[0]

    return (
        <div className="chat-toolbar">
            <Group gap={4}>
                {/* Attach button */}
                <Tooltip label="Anexar arquivo" withArrow>
                    <ActionIcon
                        size="sm"
                        variant="subtle"
                        color="gray"
                        onClick={onAttach}
                        disabled={disabled || isStreaming}
                    >
                        <IconPaperclip size={16} />
                    </ActionIcon>
                </Tooltip>

                {/* Agent selector */}
                <Menu shadow="md" width={220} position="top-start">
                    <Menu.Target>
                        <Tooltip label="Agente ativo" withArrow>
                            <ActionIcon
                                size="sm"
                                variant="subtle"
                                color="gray"
                                disabled={disabled || isStreaming}
                            >
                                <Group gap={2}>
                                    <IconRobot size={14} />
                                    <IconChevronDown size={10} />
                                </Group>
                            </ActionIcon>
                        </Tooltip>
                    </Menu.Target>
                    <Menu.Dropdown>
                        <Menu.Label>Selecionar agente</Menu.Label>
                        {agents.map((agent) => (
                            <Menu.Item
                                key={agent.id}
                                leftSection={
                                    <ThemeIcon size={24} radius="md" variant="light" color="indigo">
                                        <IconRobot size={12} />
                                    </ThemeIcon>
                                }
                                onClick={() => setActiveAgent(agent.id)}
                                style={{
                                    background:
                                        agent.id === activeAgent?.id
                                            ? 'rgba(99, 102, 241, 0.1)'
                                            : undefined,
                                }}
                            >
                                <Text size="sm" fw={600}>
                                    {agent.name}
                                </Text>
                                <Text size="xs" c="dimmed">
                                    {agent.description}
                                </Text>
                            </Menu.Item>
                        ))}
                    </Menu.Dropdown>
                </Menu>
            </Group>

            <Group gap={4}>
                {/* Clear conversation */}
                <Tooltip label="Limpar conversa" withArrow>
                    <ActionIcon
                        size="sm"
                        variant="subtle"
                        color="gray"
                        onClick={clearMessages}
                        disabled={disabled || isStreaming}
                    >
                        <IconTrash size={14} />
                    </ActionIcon>
                </Tooltip>
            </Group>
        </div>
    )
}
