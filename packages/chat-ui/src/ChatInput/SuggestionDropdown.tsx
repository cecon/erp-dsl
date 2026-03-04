import {
    forwardRef,
    useEffect,
    useImperativeHandle,
    useState,
    useCallback,
    type KeyboardEvent,
} from 'react'
import { Paper, Text, Group, ThemeIcon, ScrollArea } from '@mantine/core'
import { IconRobot, IconRoute, IconBolt } from '@tabler/icons-react'

export interface SuggestionItem {
    id: string
    label: string
    description?: string
}

export type SuggestionType = 'agent' | 'workflow' | 'skill'

export interface SuggestionDropdownProps {
    items: SuggestionItem[]
    type: SuggestionType
    command: (item: SuggestionItem) => void
}

export interface SuggestionDropdownRef {
    onKeyDown: (event: KeyboardEvent) => boolean
}

const typeConfig: Record<SuggestionType, { icon: typeof IconRobot; color: string; label: string }> = {
    agent: { icon: IconRobot, color: 'blue', label: 'Agentes' },
    workflow: { icon: IconRoute, color: 'violet', label: 'Workflows' },
    skill: { icon: IconBolt, color: 'teal', label: 'Skills' },
}

export const SuggestionDropdown = forwardRef<SuggestionDropdownRef, SuggestionDropdownProps>(
    ({ items, type, command }, ref) => {
        const [selectedIndex, setSelectedIndex] = useState(0)
        const config = typeConfig[type]

        useEffect(() => {
            setSelectedIndex(0)
        }, [items])

        const selectItem = useCallback(
            (index: number) => {
                const item = items[index]
                if (item) {
                    command(item)
                }
            },
            [items, command]
        )

        useImperativeHandle(ref, () => ({
            onKeyDown: (event: KeyboardEvent) => {
                if (event.key === 'ArrowUp') {
                    setSelectedIndex((prev) => (prev + items.length - 1) % items.length)
                    return true
                }

                if (event.key === 'ArrowDown') {
                    setSelectedIndex((prev) => (prev + 1) % items.length)
                    return true
                }

                if (event.key === 'Enter') {
                    selectItem(selectedIndex)
                    return true
                }

                return false
            },
        }))

        if (items.length === 0) {
            return (
                <Paper
                    className="suggestion-dropdown"
                    shadow="lg"
                    radius="md"
                    p="sm"
                >
                    <Text size="xs" c="dimmed" ta="center">
                        Nenhum resultado encontrado
                    </Text>
                </Paper>
            )
        }

        return (
            <Paper
                className="suggestion-dropdown"
                shadow="lg"
                radius="md"
                p={4}
            >
                <Text size="xs" c="dimmed" fw={600} px={8} py={4} tt="uppercase">
                    {config.label}
                </Text>
                <ScrollArea.Autosize mah={200}>
                    {items.map((item, index) => (
                        <button
                            key={item.id}
                            className={`suggestion-dropdown__item ${index === selectedIndex ? 'suggestion-dropdown__item--active' : ''
                                }`}
                            onClick={() => selectItem(index)}
                            onMouseEnter={() => setSelectedIndex(index)}
                            type="button"
                        >
                            <Group gap={10} wrap="nowrap">
                                <ThemeIcon
                                    size={28}
                                    radius="md"
                                    variant="light"
                                    color={config.color}
                                >
                                    <config.icon size={14} />
                                </ThemeIcon>
                                <div style={{ minWidth: 0, flex: 1 }}>
                                    <Text size="sm" fw={600} truncate>
                                        {item.label}
                                    </Text>
                                    {item.description && (
                                        <Text size="xs" c="dimmed" truncate>
                                            {item.description}
                                        </Text>
                                    )}
                                </div>
                            </Group>
                        </button>
                    ))}
                </ScrollArea.Autosize>
            </Paper>
        )
    }
)

SuggestionDropdown.displayName = 'SuggestionDropdown'
