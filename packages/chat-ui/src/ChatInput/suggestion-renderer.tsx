import { createRoot } from 'react-dom/client'
import { createRef, type KeyboardEvent as ReactKeyboardEvent } from 'react'
import {
    SuggestionDropdown,
    type SuggestionDropdownRef,
    type SuggestionItem,
    type SuggestionType,
} from './SuggestionDropdown'

interface SuggestionProps {
    items: SuggestionItem[]
    command: (item: { id: string; label: string }) => void
    clientRect?: (() => DOMRect | null) | null
}

/**
 * Creates a TipTap suggestion render function that shows
 * the SuggestionDropdown component.
 */
export function createSuggestionRenderer(type: SuggestionType) {
    return () => {
        let container: HTMLDivElement | null = null
        let root: ReturnType<typeof createRoot> | null = null
        const dropdownRef = createRef<SuggestionDropdownRef>()

        return {
            onStart(props: SuggestionProps) {
                container = document.createElement('div')
                container.classList.add('suggestion-dropdown-container')

                // Position the dropdown near the cursor
                if (props.clientRect) {
                    const rect = props.clientRect()
                    if (rect) {
                        container.style.position = 'fixed'
                        container.style.left = `${rect.left}px`
                        container.style.bottom = `${window.innerHeight - rect.top + 8}px`
                        container.style.zIndex = '1000'
                    }
                }

                document.body.appendChild(container)
                root = createRoot(container)

                root.render(
                    <SuggestionDropdown
                        ref={dropdownRef}
                        items={props.items}
                        type={type}
                        command={(item) =>
                            props.command({ id: item.id, label: item.label })
                        }
                    />
                )
            },

            onUpdate(props: SuggestionProps) {
                if (!root || !container) return

                // Update position
                if (props.clientRect) {
                    const rect = props.clientRect()
                    if (rect) {
                        container.style.left = `${rect.left}px`
                        container.style.bottom = `${window.innerHeight - rect.top + 8}px`
                    }
                }

                root.render(
                    <SuggestionDropdown
                        ref={dropdownRef}
                        items={props.items}
                        type={type}
                        command={(item) =>
                            props.command({ id: item.id, label: item.label })
                        }
                    />
                )
            },

            onKeyDown(props: { event: KeyboardEvent }) {
                if (props.event.key === 'Escape') {
                    if (container) {
                        container.remove()
                        container = null
                    }
                    root?.unmount()
                    root = null
                    return true
                }

                return dropdownRef.current?.onKeyDown(props.event as unknown as ReactKeyboardEvent) ?? false
            },

            onExit() {
                if (container) {
                    container.remove()
                    container = null
                }
                root?.unmount()
                root = null
            },
        }
    }
}
