import Markdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import { Blockquote, Code, Table } from '@mantine/core'
import { CodeHighlight } from '@mantine/code-highlight'
import type { Components } from 'react-markdown'
import type { ReactNode } from 'react'

interface MarkdownRendererProps {
    content: string
    isStreaming?: boolean
}

/**
 * Sanitize incomplete code fences during streaming.
 * If we detect an unclosed ``` block, we close it so markdown renders properly.
 */
function sanitizeStreamingMarkdown(text: string): string {
    const fenceCount = (text.match(/```/g) || []).length
    if (fenceCount % 2 !== 0) {
        return text + '\n```'
    }
    return text
}

const markdownComponents: Components = {
    code: ({ children, className, ...props }) => {
        const match = /language-(\w+)/.exec(className || '')

        // Block code (inside <pre>)
        if (match) {
            return (
                <CodeHighlight
                    code={String(children).replace(/\n$/, '')}
                    language={match[1]}
                    withCopyButton
                    copyLabel="Copiar"
                    copiedLabel="Copiado!"
                />
            )
        }

        // Check if this is a block code without language
        const isBlock = String(children).includes('\n')
        if (isBlock) {
            return (
                <CodeHighlight
                    code={String(children).replace(/\n$/, '')}
                    language="text"
                    withCopyButton
                    copyLabel="Copiar"
                    copiedLabel="Copiado!"
                />
            )
        }

        // Inline code
        return (
            <Code {...props} style={{ fontSize: '0.9em' }}>
                {children as ReactNode}
            </Code>
        )
    },

    table: ({ children }) => (
        <Table
            striped
            highlightOnHover
            withTableBorder
            withColumnBorders
            style={{ marginBlock: 8, fontSize: '13px' }}
        >
            {children as ReactNode}
        </Table>
    ),

    blockquote: ({ children }) => (
        <Blockquote
            color="indigo"
            style={{ marginBlock: 8 }}
        >
            {children as ReactNode}
        </Blockquote>
    ),

    a: ({ href, children }) => (
        <a href={href} target="_blank" rel="noopener noreferrer">
            {children as ReactNode}
        </a>
    ),
}

export function MarkdownRenderer({ content, isStreaming }: MarkdownRendererProps) {
    const processedContent = isStreaming
        ? sanitizeStreamingMarkdown(content)
        : content

    return (
        <div className="chat-markdown">
            <Markdown remarkPlugins={[remarkGfm]} components={markdownComponents}>
                {processedContent}
            </Markdown>
            {isStreaming && <span className="streaming-cursor" />}
        </div>
    )
}
