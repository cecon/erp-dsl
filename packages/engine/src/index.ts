// Engine core
export { EngineProvider, useEngine } from './EngineProvider';
export type { EngineApiClient, EngineConfig, PageContext } from './EngineProvider';

// Component Registry
export { createRegistry, getComponent, listComponents } from './ComponentRegistry';
export type { FieldComponentProps } from './ComponentRegistry';

// Schema-driven renderers
export { DynamicForm } from './DynamicForm';
export type { SchemaField } from './DynamicForm';
export { PageRenderer } from './PageRenderer';
export { DashboardRenderer } from './DashboardRenderer';

// UX overlays
export { SchemaVersionBanner } from './SchemaVersionBanner';
export { RecordMetaBanner } from './RecordMetaBanner';
export { FormVersionSwitcher, getVersionPreference } from './FormVersionSwitcher';
