/* ── Otto shared types ────────────────────────────────────────────── */

export type OttoRole = 'user' | 'assistant' | 'tool' | 'system' | 'form';

/** Schema field definition — matches DynamicForm's field shape. */
export interface OttoFormField {
  id: string;
  type: string;
  label?: string;
  placeholder?: string;
  options?: { value: string; label: string }[];
}

export interface OttoMessage {
  id: string;
  role: OttoRole;
  content: string;
  timestamp: number;
  toolName?: string;
  toolResult?: unknown;
  streaming?: boolean;
  /** Present when role === 'form' — DSL field definitions to render. */
  formSchema?: OttoFormField[];
  /** Present when role === 'form' — pre-filled values from the agent. */
  formData?: Record<string, unknown>;
  /** Set to true after the user submits the form. */
  formSubmitted?: boolean;
}

export interface OttoContext {
  pageKey: string | null;
  pageTitle: string | null;
  entityEndpoint: string | null;
}

export type OttoStatus = 'idle' | 'streaming' | 'done' | 'error';
