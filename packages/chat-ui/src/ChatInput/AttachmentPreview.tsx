import { Text, ActionIcon, Tooltip, Image } from '@mantine/core'
import { IconX, IconFile, IconPhoto } from '@tabler/icons-react'

export interface AttachmentFile {
    id: string
    file: File
    previewUrl?: string
}

interface AttachmentPreviewProps {
    attachments: AttachmentFile[]
    onRemove: (id: string) => void
}

function formatFileSize(bytes: number): string {
    if (bytes < 1024) return `${bytes} B`
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
}

export function AttachmentPreview({ attachments, onRemove }: AttachmentPreviewProps) {
    if (attachments.length === 0) return null

    return (
        <div className="attachment-preview">
            {attachments.map((att) => {
                const isImage = att.file.type.startsWith('image/')

                return (
                    <div key={att.id} className="attachment-preview__item">
                        {isImage && att.previewUrl ? (
                            <Image
                                src={att.previewUrl}
                                alt={att.file.name}
                                w={64}
                                h={64}
                                radius="md"
                                fit="cover"
                            />
                        ) : (
                            <div className="attachment-preview__file-icon">
                                {isImage ? <IconPhoto size={20} /> : <IconFile size={20} />}
                            </div>
                        )}

                        <div className="attachment-preview__info">
                            <Text size="xs" fw={600} truncate style={{ maxWidth: 120 }}>
                                {att.file.name}
                            </Text>
                            <Text size="xs" c="dimmed">
                                {formatFileSize(att.file.size)}
                            </Text>
                        </div>

                        <Tooltip label="Remover" withArrow>
                            <ActionIcon
                                size="xs"
                                variant="subtle"
                                color="gray"
                                className="attachment-preview__remove"
                                onClick={() => onRemove(att.id)}
                            >
                                <IconX size={12} />
                            </ActionIcon>
                        </Tooltip>
                    </div>
                )
            })}
        </div>
    )
}

/**
 * Convert a File to base64 data URL.
 */
export function fileToBase64(file: File): Promise<string> {
    return new Promise((resolve, reject) => {
        const reader = new FileReader()
        reader.onload = () => resolve(reader.result as string)
        reader.onerror = reject
        reader.readAsDataURL(file)
    })
}

/**
 * Create an AttachmentFile with optional preview URL for images.
 */
export function createAttachmentFile(file: File): AttachmentFile {
    const id = `att_${Date.now()}_${Math.random().toString(36).substring(2, 7)}`
    const previewUrl = file.type.startsWith('image/')
        ? URL.createObjectURL(file)
        : undefined

    return { id, file, previewUrl }
}
