---
description: Architectural rules for Frontend State Management and Data Fetching
---

# Frontend State Management Skill

This skill defines the mandatory patterns for handling state in the React Frontend using React Query and Zustand.

## 1. Core Rule: Server State vs. Client State
We strictly separate Server State (data that lives in the backend) from Client State (UI state that lives in the browser).

### Server State: React Query (`@tanstack/react-query`)
**ALL API calls** (GET, POST, PUT, DELETE) must be managed by React Query.
- **Queries (`useQuery`)**: Use for fetching data (e.g., loading the Grid, loading the Schemas, Dashboard stats).
  - **Rule**: Never fetch data inside `useEffect` and save it to `useState`.
  - **Caching**: React Query handles caching. Leverage `staleTime` and `queryKey` consistently.
- **Mutations (`useMutation`)**: Use for creating, updating, or deleting data.
  - **Invalidation**: After a successful mutation, you **MUST** invalidate the relevant queries to automatically refresh the data in the UI (e.g., Grid).
  
```tsx
// Correct Invalidation Example
const queryClient = useQueryClient();
const updateMutation = useMutation({
  mutationFn: (values) => api.put(`/endpoint/${id}`, values),
  onSuccess: () => {
    // This tells React Query to refetch the grid/list data automatically!
    queryClient.invalidateQueries({ queryKey: ['pageKey'] });
  },
});
```

### Client State: Zustand (`zustand`)
Use Zustand for global, ephemeral UI state that needs to be accessed by multiple unrelated components.
- **Use Cases**: Dark mode toggle, Sidebar open/collapsed state, currently logged-in user profile, global notification toasts.
- **Rule**: Do not put form field data, grid pagination state, or selected rows into Zustand unless they specifically modify application-wide behavior. Focus state as close to the relevant component as possible (Local `useState`).

## 2. Forms and Local State
- For complex forms, use `@mantine/form` to manage form state, validation, and submission. Avoid deep trees of `useState` for individual form inputs.
- Pass the initial values directly into the form hook when opening a modal.

## 3. The "Smart Container, Dumb Component" Pattern
- **PageRenderer (Smart)**: Fetches the schema, fetches the data via React Query, holds the mutation logic, and manages the modal open/close state.
- **DynamicMrtGrid / DynamicForm (Dumb)**: Purely presentational. They receive data as props and emit events (`onEdit`, `onSubmit`, `onPageChange`) back to the smart container. They should not contain their own `useQuery` or `useMutation` hooks if possible.
