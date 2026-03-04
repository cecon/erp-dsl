import Mention from "@tiptap/extension-mention";
import type { MentionOptions } from "@tiptap/extension-mention";

// ═══════════════════════════════════════════════════════════
// AGENT MENTION — trigger: @
// ═══════════════════════════════════════════════════════════

export const AgentMention = Mention.extend({
  name: "agentMention",
}).configure({
  HTMLAttributes: {
    class: "mention-chip mention-chip--agent",
    "data-mention-type": "agent",
  },
  suggestion: {
    char: "@",
    allowSpaces: false,
  },
  renderText({ node }) {
    return `@${node.attrs.label ?? node.attrs.id}`;
  },
} as Partial<MentionOptions>);

// ═══════════════════════════════════════════════════════════
// WORKFLOW COMMAND — trigger: /
// ═══════════════════════════════════════════════════════════

export const WorkflowCommand = Mention.extend({
  name: "workflowCommand",
}).configure({
  HTMLAttributes: {
    class: "mention-chip mention-chip--workflow",
    "data-mention-type": "workflow",
  },
  suggestion: {
    char: "/",
    allowSpaces: false,
  },
  renderText({ node }) {
    return `/${node.attrs.label ?? node.attrs.id}`;
  },
} as Partial<MentionOptions>);

// ═══════════════════════════════════════════════════════════
// SKILL REFERENCE — trigger: $
// ═══════════════════════════════════════════════════════════

export const SkillReference = Mention.extend({
  name: "skillReference",
}).configure({
  HTMLAttributes: {
    class: "mention-chip mention-chip--skill",
    "data-mention-type": "skill",
  },
  suggestion: {
    char: "$",
    allowSpaces: false,
  },
  renderText({ node }) {
    return `\${${node.attrs.label ?? node.attrs.id}}`;
  },
} as Partial<MentionOptions>);
