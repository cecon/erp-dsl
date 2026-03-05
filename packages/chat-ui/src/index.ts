// Components
export { ChatPanel } from "./ChatPanel";
export type { OnSendMessageFn } from "./ChatPanel";
export { ChatToolbar } from "./ChatToolbar";
export { ContextPanel } from "./ContextPanel";
export { SessionSidebar } from "./SessionSidebar";
export { MessageList } from "./MessageList";
export { MessageBubble } from "./MessageBubble";
export { MarkdownRenderer } from "./MarkdownRenderer";
export { ChatInput } from "./ChatInput/ChatInput";
export {
  AttachmentPreview,
  createAttachmentFile,
  fileToBase64,
} from "./ChatInput/AttachmentPreview";
export { SuggestionDropdown } from "./ChatInput/SuggestionDropdown";

// State
export { useChatStore } from "./state/useChatStore";

// Hooks
export { useAutoScroll } from "./hooks/useAutoScroll";
export { useOttoStream } from "./hooks/useOttoStream";

export type {
  Message,
  MessageRole,
  MessageContent,
  TextContent,
  ImageContent,
  FileContent,
  FormField,
  InteractivePayload,
  InteractiveType,
  InteractiveOption,
  InteractiveCarouselItem,
  InteractiveImage,
  Agent,
  Workflow,
  Skill,
  ChatSession,
} from "./types/chat";

export type { AttachmentFile } from "./ChatInput/AttachmentPreview";
