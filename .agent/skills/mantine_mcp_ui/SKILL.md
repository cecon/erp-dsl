---
description: How to use the Mantine MCP server tools for UI component documentation, generation, and theming
---

# Mantine MCP UI Skill

This skill instructs how to leverage the **Mantine MCP server** when building or modifying UI components. The MCP provides direct access to Mantine v7 documentation and component scaffolding without leaving the editor.

## Available MCP Tools

### 1. `get_component_docs` ✅ (Primary Tool)

Fetches live documentation for any Mantine component. This is the **most reliable and valuable tool**.

**When to use:**

- Before using any Mantine component you're not 100% sure about
- To check available props, variants, and API surface
- To verify correct import paths

**Usage:**

```
mcp_mantine_get_component_docs
  component: "Button"       # Component name (PascalCase)
  section: "all"            # "props" | "examples" | "api" | "all"
  format: "markdown"        # "markdown" | "json"
```

**Returns:** Description, props, examples, import statement, package name, version, URL to official docs, and related components.

**Common components to query:**

- Layout: `AppShell`, `Grid`, `SimpleGrid`, `Stack`, `Group`, `Flex`, `Container`, `Space`
- Inputs: `TextInput`, `NumberInput`, `Select`, `MultiSelect`, `Textarea`, `Checkbox`, `Switch`, `DateInput`
- Feedback: `Notification`, `Alert`, `Modal`, `Drawer`, `LoadingOverlay`, `Skeleton`
- Navigation: `Tabs`, `NavLink`, `Breadcrumbs`, `Stepper`, `Pagination`
- Data Display: `Table`, `Card`, `Badge`, `Avatar`, `Accordion`, `Timeline`
- Overlay: `Menu`, `Popover`, `Tooltip`, `HoverCard`
- Typography: `Title`, `Text`, `Highlight`, `Code`, `Blockquote`
- Buttons: `Button`, `ActionIcon`, `CopyButton`, `FileButton`

### 2. `generate_component` ✅ (Scaffolding)

Generates a boilerplate component wrapper around a Mantine component.

**When to use:**

- Creating a new reusable wrapper component around a Mantine primitive
- Scaffolding a new UI component quickly

**Usage:**

```
mcp_mantine_generate_component
  name: "PrimaryButton"        # Your component name
  mantineComponent: "Button"   # Mantine base component
  props: { ... }               # Optional custom props config
  variants: [ ... ]            # Optional component variants
```

**Returns:** A `.tsx` component file and an `index.ts` barrel export.

> [!IMPORTANT]
> The generated code is a starting point. Always adapt it to match the project's conventions (CSS Modules, Dark Mode first, no Emotion).

### 3. `search_components` ⚠️ (Unreliable)

Searches for Mantine components by keyword.

**Status:** Currently returns empty results. **Workaround:** Use `get_component_docs` directly with the component name, or consult the list above.

### 4. `list_components` ⚠️ (Unreliable)

Lists all available Mantine components.

**Status:** Currently returns empty results. **Workaround:** Refer to the component list in section 1 above.

### 5. `create_component_theme` / `create_theme_config` ⚠️ (Buggy)

Generates theme configuration for components or global theming.

**Status:** Returns minimal or broken output (e.g., `NaN` values in color generation). **Workaround:** Write theme config manually following Mantine v7 theming docs.

## Workflow: Using MCP When Building UI

### Step 1: Consult Documentation

Before coding any Mantine component, query the docs:

```
mcp_mantine_get_component_docs(component="Select", section="props")
```

### Step 2: Scaffold if Needed

If creating a reusable wrapper:

```
mcp_mantine_generate_component(name="StatusBadge", mantineComponent="Badge")
```

### Step 3: Adapt to Project Standards

Always apply these project rules to any generated or documented code:

- **CSS Modules**: Use `.module.css` files, NOT Emotion/styled-components
- **Dark Mode First**: Ensure all components render correctly in dark mode
- **Tabler Icons**: Use `@tabler/icons-react` for all icons
- **No inline styles**: Use Mantine's `classNames`, `styles`, or CSS Modules

## Project-Specific Mantine Versions

| Project               | Mantine Version | React Version |
| --------------------- | --------------- | ------------- |
| `frontend/` (ERP DSL) | `^7.15.3`       | React 18      |
| `frontend-platform/`  | `^7.17.8`       | React 19      |

> [!WARNING]
> Be aware of version differences between the two frontends. Some Mantine props may exist in 7.17 but not in 7.15. When in doubt, check the MCP docs which reports the component version.
