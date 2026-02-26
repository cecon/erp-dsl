---
description: Architectural rules and standard components for UI development in the ERP
---

# UI Framework Skill

This skill defines the mandatory tools, components, and architectural patterns for creating and refactoring User Interfaces in this ERP project. Wait until you read this document carefully before making UI changes.

## Core Stack
- **React 18** and **Vite**
- **Mantine v7** (CSS Modules based, NO Emotion/CSS-in-JS)
- **Zustand** (Global State)
- **React Query v5** (Server State / API Caching)

## Data Grids
Whenever you need to implement or modify a Data Grid, Table, or CRUD list, **you MUST use `MantineReactTable`** (`mantine-react-table`).

### Mandatory Grid Patterns:
1. **Server-side operations**: Pagination, Sorting, and Filtering must be handled by the backend. Use React Query to fetch data.
2. **Global Search**: Enable `enableGlobalFilter` to provide a top-level intelligent search bar.
3. **Row Grouping**: Enable `enableGrouping: true` for entities that have hierarchical structures (like Products with Categories/Groups).
4. **Consistency**: Use the pre-configured Mantine Theme. Do not override table colors manually unless absolutely necessary for the Dark Theme standard.

### ⚠️ Critical Gotchas & Rules for MRT:
- **Global CSS Import**: You **MUST** ensure `import 'mantine-react-table/styles.css';` is present in the `main.tsx` file. If this is missing, the table will render without styles and look completely broken.
- **Dependency Installation**: Use `pnpm` for installing packages to avoid workspace protocol errors. For Mantine v7, ensure you are using the V2 Beta of MRT (e.g., `pnpm add mantine-react-table@beta`).
- **Docker Hot Reload**: Vite's hot reload does not automatically sync new `node_modules`. If you add a new library like MRT, you **MUST** rebuild the frontend container (`docker compose up -d --build frontend`).

### Example Basic MRT Setup:
```tsx
import { MantineReactTable, useMantineReactTable } from 'mantine-react-table';

export function StandardGrid({ columns, data }) {
  const table = useMantineReactTable({
    columns,
    data,
    enableGrouping: true,
    enableGlobalFilter: true,
    enableColumnResizing: true,
    enableRowActions: true,
    renderRowActions: ({ row }) => (
      // Add edit/delete action icons here
    ),
  });

  return <MantineReactTable table={table} />;
}
```

## Styling & Theming
- **Dark Mode First**: The system is designed with a premium, enterprise dark mode aesthetic.
- **Micro-animations**: Use subtle transitions and hover effects on interactable elements.
- **CSS Modules**: For custom styles beyond Mantine's `style` or `classNames` props, use `.module.css` files. Do not add new Emotion/styled-components dependencies.
