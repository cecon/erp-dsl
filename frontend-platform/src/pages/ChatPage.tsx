/**
 * Chat page wrapper for frontend-platform.
 * Imports chat components from the shared @erp-dsl/chat-ui package.
 */
import { ChatPanel } from '@erp-dsl/chat-ui'
import { useNavigate } from 'react-router-dom'

export function ChatPage() {
    const navigate = useNavigate()
    return <ChatPanel onNavigateBack={() => navigate('/')} />
}
