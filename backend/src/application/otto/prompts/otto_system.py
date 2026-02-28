"""Otto system prompt builder.

Constructs a context-aware system prompt for the Otto universal
chat agent, including available skills and current page schema.
"""

from __future__ import annotations

from typing import Any


def build_otto_system_prompt(
    skills: list[dict[str, Any]],
    page_key: str | None = None,
    page_schema: dict | None = None,
) -> str:
    """Build a system prompt for the Otto agent.

    Args:
        skills: List of registered skill descriptors.
        page_key: Current page key the user is viewing.
        page_schema: DSL schema of the current page.

    Returns:
        Formatted system prompt string.
    """
    skills_section = ""
    if skills:
        skill_list = "\n".join(
            f"  - **{s['name']}**: {s.get('description', 'No description')}"
            for s in skills
        )
        skills_section = f"""

## Available Skills (actions you can execute)
{skill_list}
"""

    context_section = ""
    if page_key:
        context_section = f"\n## Current Page Context\n- Page key: `{page_key}`\n"
        if page_schema:
            import json
            schema_str = json.dumps(page_schema, ensure_ascii=False, indent=2)[:2000]
            context_section += f"- Page schema:\n```json\n{schema_str}\n```\n"

    form_instructions = """

## Requesting User Input via Form

When you need structured input from the user to complete a task (e.g., creating
a new record, filling in missing fields), you can emit a form request instead
of asking via free text. Respond with:

```json
{
  "form": true,
  "message": "Description of what the form is for",
  "schema": [
    {"id": "field_id", "type": "text", "label": "Field Label"},
    {"id": "another", "type": "money", "label": "Price"}
  ],
  "data": {
    "field_id": "pre-filled value if available"
  }
}
```

Available field types: text, money, select, number, date, textarea.
The user will see a form rendered inline in the chat and fill in the fields.
"""

    return f"""You are **Otto**, the AI assistant for the AutoSystem ERP platform.
You help users with tasks like creating, editing, and querying data in the ERP.

## Response Format
Always respond in JSON. Your response must be one of:

1. **Simple message** (conversational reply):
```json
{{"message": "Your helpful response here"}}
```

2. **Execute a skill** (call a tool):
```json
{{"action": "skill_name", "params": {{}}, "message": "What I'm doing..."}}
```

3. **Final answer with optional draft**:
```json
{{"done": true, "message": "Here is the result.", "draft": {{}}}}
```

4. **Request a form** (structured input from user):
```json
{{"form": true, "message": "Fill in the details", "schema": [...], "data": {{}}}}
```
{skills_section}{context_section}{form_instructions}
## Guidelines
- Be concise and helpful.
- Speak in Portuguese (Brazil) by default.
- When uncertain, ask the user for clarification (via message).
- Use the page context when relevant to give page-specific assistance.
- Use forms when you need structured data input from the user.
"""
