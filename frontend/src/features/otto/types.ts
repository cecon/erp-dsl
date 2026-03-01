/* ── Otto shared types ────────────────────────────────────────────── */

export type OttoRole = 'user' | 'assistant' | 'tool' | 'system' | 'form' | 'component' | 'interactive';

/** Schema field definition — matches DynamicForm's field shape. */
export interface OttoFormField {
  id: string;
  type: string;
  label?: string;
  placeholder?: string;
  options?: { value: string; label: string }[];
}

/* ── Interactive message sub-types ────────────────────────────────── */

export type InteractiveType = 'confirm' | 'choice' | 'image-picker' | 'carousel';

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
  /* confirm */
  confirmLabel?: string;
  cancelLabel?: string;
  /* choice */
  options?: InteractiveOption[];
  /* image-picker */
  images?: InteractiveImage[];
  /* carousel */
  items?: InteractiveCarouselItem[];
}

/* ── Main message interface ──────────────────────────────────────── */

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
  /** Present when role === 'component' — registry key to look up. */
  componentName?: string;
  /** Present when role === 'component' — props to pass to the component. */
  componentProps?: Record<string, unknown>;
  /** Present when role === 'interactive' — interactive payload. */
  interactive?: InteractivePayload;
  /** Set to true after the user responds to the interactive. */
  interactiveAnswered?: boolean;
  /** The value the user selected in the interactive. */
  interactiveAnswer?: string;
}

export interface OttoContext {
  pageKey: string | null;
  pageTitle: string | null;
  entityEndpoint: string | null;
}

export type OttoStatus = 'idle' | 'streaming' | 'done' | 'error';
