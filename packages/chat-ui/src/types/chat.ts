// ═══════════════════════════════════════════════════════════
// OTTO CHAT — TYPE DEFINITIONS
// ═══════════════════════════════════════════════════════════

export type MessageRole = "user" | "assistant" | "system";

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
