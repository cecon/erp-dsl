import { useState } from 'react'
import {
    Text,
    Badge,
    Group,
    Stack,
    ThemeIcon,
    ActionIcon,
    Tooltip,
    Divider,
    ScrollArea,
} from '@mantine/core'
import {
    IconRobot,
    IconBolt,
    IconRoute,
    IconPaperclip,
    IconChevronRight,
    IconChevronLeft,
    IconInfoCircle,
} from '@tabler/icons-react'
import { useChatStore } from './state/useChatStore'
import type { Agent, Skill, Workflow } from './types/chat'

interface ContextPanelProps {
    agents?: Agent[]
    skills?: Skill[]
    workflows?: Workflow[]
}

// Mock data
const MOCK_AGENTS: Agent[] = [
    { id: 'otto', name: 'Otto', description: 'Assistente principal do AutoSystem', skills: ['classificar-ncm', 'calcular-icms'] },
    { id: 'fiscal', name: 'Fiscal', description: 'Especialista em notas fiscais e tributos', skills: ['validar-cnpj'] },
]

const MOCK_SKILLS: Skill[] = [
    { id: 'classificar-ncm', name: 'Classificar NCM', description: 'Classificar NCM de produto usando IA' },
    { id: 'calcular-icms', name: 'Calcular ICMS', description: 'Cálculo interestadual de ICMS' },
    { id: 'validar-cnpj', name: 'Validar CNPJ', description: 'Validar CNPJ na Receita Federal' },
]

const MOCK_WORKFLOWS: Workflow[] = [
    { id: 'fechamento-caixa', name: 'Fechamento de Caixa', description: 'Fechar caixa do dia' },
    { id: 'importar-nfe', name: 'Importar NF-e', description: 'Importar XML de nota fiscal' },
]

export function ContextPanel({ agents, skills, workflows }: ContextPanelProps) {
    const [isOpen, setIsOpen] = useState(false)
    const activeAgentId = useChatStore((s) => s.activeAgentId)
    const messages = useChatStore((s) => s.messages)

    const allAgents = agents ?? MOCK_AGENTS
    const allSkills = skills ?? MOCK_SKILLS
    const allWorkflows = workflows ?? MOCK_WORKFLOWS
    const activeAgent = allAgents.find((a) => a.id === activeAgentId) ?? allAgents[0]

    // Count attachments in messages
    const attachmentCount = messages.reduce((acc, msg) => {
        return acc + msg.content.filter((c) => c.type === 'image' || c.type === 'file').length
    }, 0)

    if (!isOpen) {
        return (
            <div className="context-panel context-panel--collapsed">
                <Tooltip label="Abrir contexto" position="left" withArrow>
                    <ActionIcon
                        variant="subtle"
                        color="gray"
                        size="md"
                        onClick={() => setIsOpen(true)}
                    >
                        <IconChevronLeft size={16} />
                    </ActionIcon>
                </Tooltip>
            </div>
        )
    }

    return (
        <div className="context-panel context-panel--open">
            {/* Header */}
            <div className="context-panel__header">
                <Group gap={8}>
                    <IconInfoCircle size={16} />
                    <Text size="sm" fw={700}>Contexto</Text>
                </Group>
                <ActionIcon
                    variant="subtle"
                    color="gray"
                    size="sm"
                    onClick={() => setIsOpen(false)}
                >
                    <IconChevronRight size={14} />
                </ActionIcon>
            </div>

            <ScrollArea flex={1} scrollbarSize={4}>
                <Stack gap={0} p="sm">
                    {/* Active Agent */}
                    <div className="context-panel__section">
                        <Text size="xs" fw={700} c="dimmed" tt="uppercase" mb={8}>
                            Agente Ativo
                        </Text>
                        <div className="context-panel__agent-card">
                            <Group gap={10}>
                                <ThemeIcon size={36} radius="md" variant="light" color="indigo">
                                    <IconRobot size={18} />
                                </ThemeIcon>
                                <div style={{ flex: 1, minWidth: 0 }}>
                                    <Text size="sm" fw={700}>{activeAgent?.name ?? 'Otto'}</Text>
                                    <Text size="xs" c="dimmed" truncate>
                                        {activeAgent?.description ?? 'Assistente principal'}
                                    </Text>
                                </div>
                            </Group>

                            {activeAgent?.skills && activeAgent.skills.length > 0 && (
                                <Group gap={4} mt={8}>
                                    {activeAgent.skills.map((skillId) => (
                                        <Badge key={skillId} size="xs" variant="light" color="teal">
                                            {skillId}
                                        </Badge>
                                    ))}
                                </Group>
                            )}
                        </div>
                    </div>

                    <Divider my="sm" color="var(--border-default)" />

                    {/* Available Skills */}
                    <div className="context-panel__section">
                        <Text size="xs" fw={700} c="dimmed" tt="uppercase" mb={8}>
                            Skills Disponíveis
                        </Text>
                        <Stack gap={4}>
                            {allSkills.map((skill) => (
                                <div key={skill.id} className="context-panel__list-item">
                                    <Group gap={8}>
                                        <ThemeIcon size={24} radius="md" variant="light" color="teal">
                                            <IconBolt size={12} />
                                        </ThemeIcon>
                                        <div style={{ flex: 1, minWidth: 0 }}>
                                            <Text size="xs" fw={600} truncate>{skill.name}</Text>
                                            <Text size="xs" c="dimmed" truncate>{skill.description}</Text>
                                        </div>
                                    </Group>
                                </div>
                            ))}
                        </Stack>
                    </div>

                    <Divider my="sm" color="var(--border-default)" />

                    {/* Workflows */}
                    <div className="context-panel__section">
                        <Text size="xs" fw={700} c="dimmed" tt="uppercase" mb={8}>
                            Workflows
                        </Text>
                        <Stack gap={4}>
                            {allWorkflows.map((wf) => (
                                <div key={wf.id} className="context-panel__list-item">
                                    <Group gap={8}>
                                        <ThemeIcon size={24} radius="md" variant="light" color="violet">
                                            <IconRoute size={12} />
                                        </ThemeIcon>
                                        <div style={{ flex: 1, minWidth: 0 }}>
                                            <Text size="xs" fw={600} truncate>{wf.name}</Text>
                                            <Text size="xs" c="dimmed" truncate>{wf.description}</Text>
                                        </div>
                                    </Group>
                                </div>
                            ))}
                        </Stack>
                    </div>

                    {/* Session Attachments */}
                    {attachmentCount > 0 && (
                        <>
                            <Divider my="sm" color="var(--border-default)" />
                            <div className="context-panel__section">
                                <Text size="xs" fw={700} c="dimmed" tt="uppercase" mb={8}>
                                    Anexos da Sessão
                                </Text>
                                <Group gap={8}>
                                    <IconPaperclip size={14} />
                                    <Text size="xs">{attachmentCount} arquivo(s)</Text>
                                </Group>
                            </div>
                        </>
                    )}
                </Stack>
            </ScrollArea>
        </div>
    )
}
