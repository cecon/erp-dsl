// ═══════════════════════════════════════════════════════════
// OTTO CHAT — TYPE DEFINITIONS
// ═══════════════════════════════════════════════════════════

export type MessageRole = "user" | "assistant" | "system" | "tool" | "form" | "component" | "interactive";

// ── Content Types ──────────────────────────────────────────

export interface TextContent {
  type: "text";
  text: string;
}

export interface ImageContent {
  type: "image";
  url: string;
  alt?: string;
  mimeType?: string;
}

export interface FileContent {
  type: "file";
  name: string;
  url: string;
  size: number;
  mimeType: string;
}

export type MessageContent = TextContent | ImageContent | FileContent;

// ── Form Field (matches DynamicForm schema) ────────────────

export interface FormField {
  id: string;
  type: string;
  label?: string;
  placeholder?: string;
  options?: { value: string; label: string }[];
  components?: FormField[];
  condition?: { field: string; value: string };
  readonly?: boolean;
  computed?: { formula: string; deps: string[] };
  dataSource?: string;
}

// ── Interactive Message Types ──────────────────────────────

export type InteractiveType = "confirm" | "choice" | "image-picker" | "carousel";

export interface InteractiveOption {
  label: string;
  value: string;
}

export interface InteractiveImage {
  url: string;
  label: string;
  value: string;
}

export interface InteractiveCarouselItem {
  title: string;
  subtitle: string;
  value: string;
}

export interface InteractivePayload {
  type: InteractiveType;
  sessionId: string;
  question: string;
  confirmLabel?: string;
  cancelLabel?: string;
  options?: InteractiveOption[];
  images?: InteractiveImage[];
  items?: InteractiveCarouselItem[];
}

// ── Message ────────────────────────────────────────────────

export interface MessageMetadata {
  agentId?: string;
  workflowId?: string;
  skillId?: string;
}

export interface Message {
  id: string;
  role: MessageRole;
  content: MessageContent[];
  timestamp: Date;
  isStreaming?: boolean;
  metadata?: MessageMetadata;

  // ── Tool call fields ──
  toolName?: string;
  toolResult?: unknown;

  // ── Form fields ──
  formSchema?: FormField[];
  formData?: Record<string, unknown>;
  formSubmitted?: boolean;

  // ── Component fields ──
  componentName?: string;
  componentProps?: Record<string, unknown>;

  // ── Interactive fields ──
  interactive?: InteractivePayload;
  interactiveAnswered?: boolean;
  interactiveAnswer?: string;
}

// ── Chat Session ───────────────────────────────────────────

export interface ChatSession {
  id: string;
  title: string;
  messages: Message[];
  createdAt: Date;
  updatedAt: Date;
  activeAgentId?: string;
}

// ── Entities (for mentions/commands) ───────────────────────

export interface Agent {
  id: string;
  name: string;
  description: string;
  avatarUrl?: string;
  skills?: string[];
}

export interface Workflow {
  id: string;
  name: string;
  description: string;
}

export interface Skill {
  id: string;
  name: string;
  description: string;
}
