import { useCallback, useMemo } from 'react'
import { useEditor, EditorContent } from '@tiptap/react'
import StarterKit from '@tiptap/starter-kit'
import Mention from '@tiptap/extension-mention'
import { ActionIcon, Tooltip } from '@mantine/core'
import { IconSend, IconPlayerStop } from '@tabler/icons-react'
import { useChatStore } from '../state/useChatStore'
import type { Message, Agent, Workflow, Skill } from '../types/chat'
import type { SuggestionItem } from './SuggestionDropdown'
import { createSuggestionRenderer } from './suggestion-renderer'

interface ChatInputProps {
    onSend: (message: Message) => void
    onStop?: () => void
    availableAgents?: Agent[]
    availableWorkflows?: Workflow[]
    availableSkills?: Skill[]
}

function generateId(): string {
    return `msg_${Date.now()}_${Math.random().toString(36).substring(2, 9)}`
}

/**
 * Serialize TipTap editor JSON to plain text, preserving mention syntax.
 */
function serializeEditorContent(editor: ReturnType<typeof useEditor>): string {
    if (!editor) return ''

    const json = editor.getJSON()
    const parts: string[] = []

    function walk(node: Record<string, unknown>) {
        if (node.type === 'text') {
            parts.push(node.text as string)
        } else if (node.type === 'agentMention') {
            const attrs = node.attrs as { label?: string; id?: string }
            parts.push(`@${attrs.label ?? attrs.id}`)
        } else if (node.type === 'workflowCommand') {
            const attrs = node.attrs as { label?: string; id?: string }
            parts.push(`/${attrs.label ?? attrs.id}`)
        } else if (node.type === 'skillReference') {
            const attrs = node.attrs as { label?: string; id?: string }
            parts.push(`\${${attrs.label ?? attrs.id}}`)
        } else if (node.type === 'paragraph') {
            if (parts.length > 0 && parts[parts.length - 1] !== '\n') {
                parts.push('\n')
            }
        }

        if (Array.isArray(node.content)) {
            for (const child of node.content) {
                walk(child as Record<string, unknown>)
            }
        }
    }

    walk(json as Record<string, unknown>)

    return parts.join('').trim()
}

// Mock data for demo
const MOCK_AGENTS: SuggestionItem[] = [
    { id: 'otto', label: 'Otto', description: 'Assistente principal do AutoSystem' },
    { id: 'fiscal', label: 'Fiscal', description: 'Especialista em notas fiscais e tributos' },
    { id: 'financeiro', label: 'Financeiro', description: 'Gestão de contas e fluxo de caixa' },
    { id: 'estoque', label: 'Estoque', description: 'Controle de inventário e movimentações' },
]

const MOCK_WORKFLOWS: SuggestionItem[] = [
    { id: 'fechamento-caixa', label: 'fechamento-caixa', description: 'Fechar caixa do dia' },
    { id: 'importar-nfe', label: 'importar-nfe', description: 'Importar XML de NF-e' },
    { id: 'relatorio-vendas', label: 'relatorio-vendas', description: 'Gerar relatório de vendas' },
    { id: 'backup-dados', label: 'backup-dados', description: 'Backup do banco de dados' },
]

const MOCK_SKILLS: SuggestionItem[] = [
    { id: 'classificar-ncm', label: 'classificar-ncm', description: 'Classificar NCM de produto' },
    { id: 'calcular-icms', label: 'calcular-icms', description: 'Calcular ICMS interestadual' },
    { id: 'validar-cnpj', label: 'validar-cnpj', description: 'Validar CNPJ na Receita Federal' },
]

export function ChatInput({
    onSend,
    onStop,
    availableAgents,
    availableWorkflows,
    availableSkills,
}: ChatInputProps) {
    const isStreaming = useChatStore((s) => s.isStreaming)

    // Convert entities to suggestion items
    const agentItems = useMemo<SuggestionItem[]>(
        () =>
            availableAgents?.map((a) => ({
                id: a.id,
                label: a.name,
                description: a.description,
            })) ?? MOCK_AGENTS,
        [availableAgents]
    )

    const workflowItems = useMemo<SuggestionItem[]>(
        () =>
            availableWorkflows?.map((w) => ({
                id: w.id,
                label: w.name,
                description: w.description,
            })) ?? MOCK_WORKFLOWS,
        [availableWorkflows]
    )

    const skillItems = useMemo<SuggestionItem[]>(
        () =>
            availableSkills?.map((s) => ({
                id: s.id,
                label: s.name,
                description: s.description,
            })) ?? MOCK_SKILLS,
        [availableSkills]
    )

    const agentRenderer = useMemo(() => createSuggestionRenderer('agent'), [])
    const workflowRenderer = useMemo(() => createSuggestionRenderer('workflow'), [])
    const skillRenderer = useMemo(() => createSuggestionRenderer('skill'), [])

    const editor = useEditor({
        extensions: [
            StarterKit.configure({
                heading: false,
                codeBlock: false,
                blockquote: false,
                bulletList: false,
                orderedList: false,
                horizontalRule: false,
            }),
            Mention.extend({ name: 'agentMention' }).configure({
                HTMLAttributes: {
                    class: 'mention-chip mention-chip--agent',
                    'data-mention-type': 'agent',
                },
                renderText({ node }) {
                    return `@${node.attrs.label ?? node.attrs.id}`
                },
                suggestion: {
                    char: '@',
                    items: ({ query }: { query: string }) =>
                        agentItems.filter((item) =>
                            item.label.toLowerCase().includes(query.toLowerCase())
                        ),
                    render: agentRenderer,
                },
            }),
            Mention.extend({ name: 'workflowCommand' }).configure({
                HTMLAttributes: {
                    class: 'mention-chip mention-chip--workflow',
                    'data-mention-type': 'workflow',
                },
                renderText({ node }) {
                    return `/${node.attrs.label ?? node.attrs.id}`
                },
                suggestion: {
                    char: '/',
                    items: ({ query }: { query: string }) =>
                        workflowItems.filter((item) =>
                            item.label.toLowerCase().includes(query.toLowerCase())
                        ),
                    render: workflowRenderer,
                },
            }),
            Mention.extend({ name: 'skillReference' }).configure({
                HTMLAttributes: {
                    class: 'mention-chip mention-chip--skill',
                    'data-mention-type': 'skill',
                },
                renderText({ node }) {
                    return `\${${node.attrs.label ?? node.attrs.id}}`
                },
                suggestion: {
                    char: '$',
                    items: ({ query }: { query: string }) =>
                        skillItems.filter((item) =>
                            item.label.toLowerCase().includes(query.toLowerCase())
                        ),
                    render: skillRenderer,
                },
            }),
        ],
        editorProps: {
            attributes: {
                class: 'chat-tiptap-editor',
                'data-placeholder': 'Pergunte algo ao Otto...',
            },
            handleKeyDown: (_view, event) => {
                // Submit with Enter (not Shift+Enter)
                if (event.key === 'Enter' && !event.shiftKey) {
                    // Don't submit if a suggestion dropdown is open
                    const hasSuggestion = document.querySelector('.suggestion-dropdown-container')
                    if (hasSuggestion) return false

                    event.preventDefault()
                    handleSend()
                    return true
                }
                return false
            },
        },
    })

    const handleSend = useCallback(() => {
        if (!editor || isStreaming) return

        const text = serializeEditorContent(editor)
        if (!text) return

        const message: Message = {
            id: generateId(),
            role: 'user',
            content: [{ type: 'text', text }],
            timestamp: new Date(),
        }

        onSend(message)
        editor.commands.clearContent()

        // Re-focus editor after sending
        requestAnimationFrame(() => {
            editor.commands.focus()
        })
    }, [editor, isStreaming, onSend])

    return (
        <div className="chat-input-area">
            <div className="chat-input-wrapper">
                <div className="chat-tiptap-wrapper">
                    <EditorContent editor={editor} />
                </div>

                <div className="chat-input__actions">
                    {isStreaming ? (
                        <Tooltip label="Parar geração" withArrow>
                            <ActionIcon
                                size="md"
                                variant="subtle"
                                color="red"
                                onClick={onStop}
                            >
                                <IconPlayerStop size={16} />
                            </ActionIcon>
                        </Tooltip>
                    ) : (
                        <Tooltip label="Enviar (Enter)" withArrow>
                            <ActionIcon
                                size="md"
                                variant="subtle"
                                color="gray"
                                onClick={handleSend}
                            >
                                <IconSend size={16} />
                            </ActionIcon>
                        </Tooltip>
                    )}
                </div>
            </div>

            <div className="chat-input__hint">
                <kbd>Enter</kbd> enviar · <kbd>Shift+Enter</kbd> nova linha ·
                <kbd>@</kbd> agentes · <kbd>/</kbd> workflows · <kbd>$</kbd> skills
            </div>
        </div>
    )
}
