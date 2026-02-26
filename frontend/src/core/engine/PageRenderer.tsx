import { Alert, Button, Group, Loader, Modal, Stack, Text } from '@mantine/core';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { useCallback, useState } from 'react';
import { useParams } from 'react-router-dom';
import api from '../../services/api';
import { DynamicForm } from './DynamicForm';
import { EnterpriseGrid } from '../../components/grid/EnterpriseGrid';
import { DynamicMrtGrid } from '../../components/grid/DynamicMrtGrid';

/* eslint-disable @typescript-eslint/no-explicit-any */

interface SchemaAction {
  id: string;
  type: 'create' | 'edit' | 'delete';
  label: string;
}

interface DataSource {
  endpoint: string;
  method?: string;
  paginationParams?: { offset: string; limit: string };
}

interface PageSchema {
  id: string;
  page_key: string;
  scope: string;
  schema: {
    title?: string;
    description?: string;
    components?: any[];
    columns?: any[];
    actions?: SchemaAction[];
    dataSource?: DataSource;
  };
}

/**
 * Generic CRUD page renderer.
 *
 * Renders any entity page purely from the DSL schema.
 * The component has ZERO knowledge of specific entities —
 * endpoints, labels, and field definitions all come from the schema.
 */
export function PageRenderer() {
  const { pageKey } = useParams<{ pageKey: string }>();
  const queryClient = useQueryClient();
  const [page, setPage] = useState(1);
  const [formOpen, setFormOpen] = useState(false);
  const [editingItem, setEditingItem] = useState<any>(null);
  const pageSize = 20;

  /* ── Schema query ───────────────────────────────────────────── */

  const { data: pageData, isLoading: pageLoading } = useQuery<PageSchema>({
    queryKey: ['page', pageKey],
    queryFn: () => api.get(`/pages/${pageKey}`).then((r) => r.data),
    enabled: !!pageKey,
  });

  const schema = pageData?.schema;
  const dataSource = schema?.dataSource;
  const endpoint = dataSource?.endpoint ?? `/${pageKey}`;

  /* ── Action labels from schema ──────────────────────────────── */

  const findAction = (type: string): SchemaAction | undefined =>
    schema?.actions?.find((a) => a.type === type);

  const createAction = findAction('create');
  const editAction = findAction('edit');

  /* ── Data query (uses schema.dataSource.endpoint) ───────────── */

  const { data: gridData, isLoading: dataLoading } = useQuery({
    queryKey: [pageKey, page],
    queryFn: () =>
      api
        .get(endpoint, {
          params: { offset: (page - 1) * pageSize, limit: pageSize },
        })
        .then((r) => r.data),
    enabled: !!pageData && !!dataSource,
  });

  /* ── Mutations (all use the same dynamic endpoint) ──────────── */

  const createMutation = useMutation({
    mutationFn: (values: any) => api.post(endpoint, values),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: [pageKey] });
      setFormOpen(false);
    },
  });

  const updateMutation = useMutation({
    mutationFn: (values: any) =>
      api.put(`${endpoint}/${values.id}`, values),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: [pageKey] });
      setFormOpen(false);
      setEditingItem(null);
    },
  });

  const deleteMutation = useMutation({
    mutationFn: (id: string) => api.delete(`${endpoint}/${id}`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: [pageKey] });
    },
  });

  /* ── Handlers ───────────────────────────────────────────────── */

  const handleEdit = useCallback((row: any) => {
    setEditingItem(row);
    setFormOpen(true);
  }, []);

  const handleDelete = useCallback(
    (row: any) => {
      const label = row.name ?? row.id;
      if (confirm(`Delete "${label}"?`)) {
        deleteMutation.mutate(row.id);
      }
    },
    [deleteMutation]
  );

  const handleSubmit = useCallback(
    (values: any) => {
      if (editingItem) {
        updateMutation.mutate({ ...values, id: editingItem.id });
      } else {
        createMutation.mutate(values);
      }
    },
    [editingItem, createMutation, updateMutation]
  );

  /* ── Loading / error states ─────────────────────────────────── */

  if (pageLoading) {
    return (
      <Stack align="center" justify="center" h={400}>
        <Loader color="blue" size="lg" />
        <Text c="dimmed" size="sm">Loading page schema…</Text>
      </Stack>
    );
  }

  if (!pageData || !schema) {
    return (
      <Alert color="red" title="Page not found" radius="md">
        The page <strong>{pageKey}</strong> could not be found.
      </Alert>
    );
  }

  /* ── Form fields from schema components ─────────────────────── */

  const formFields =
    schema.components
      ?.find((c: any) => c.type === 'form')
      ?.components?.map((f: any) => ({
        id: f.id,
        type: f.type,
        label: f.label,
      })) ?? [];

  /* ── Modal title from schema actions ────────────────────────── */

  const modalTitle = editingItem
    ? (editAction?.label ?? 'Edit')
    : (createAction?.label ?? 'New');

  /* ── Render ─────────────────────────────────────────────────── */

  return (
    <Stack gap="lg">
      {/* Page Header */}
      <div className="page-header">
        <div>
          <div className="page-header-title">{schema.title || pageKey}</div>
          {schema.description && (
            <div className="page-header-subtitle">{schema.description}</div>
          )}
        </div>
        {createAction && (
          <Button
            onClick={() => {
              setEditingItem(null);
              setFormOpen(true);
            }}
          >
            + {createAction.label}
          </Button>
        )}
      </div>

      {/* Data Grid */}
      {schema.columns && pageKey === 'products' ? (
        <DynamicMrtGrid
          columns={schema.columns}
          data={gridData?.items ?? []}
          total={gridData?.total ?? 0}
          page={page}
          pageSize={pageSize}
          onPageChange={setPage}
          onEdit={handleEdit}
          onDelete={handleDelete}
        />
      ) : schema.columns ? (
        <EnterpriseGrid
          columns={schema.columns}
          data={gridData?.items ?? []}
          total={gridData?.total ?? 0}
          page={page}
          pageSize={pageSize}
          onPageChange={setPage}
          onEdit={handleEdit}
          onDelete={handleDelete}
        />
      ) : null}

      {/* Create/Edit Modal */}
      <Modal
        opened={formOpen}
        onClose={() => {
          setFormOpen(false);
          setEditingItem(null);
        }}
        title={modalTitle}
        centered
        size="md"
        overlayProps={{ backgroundOpacity: 0.6, blur: 3 }}
      >
        <DynamicForm
          fields={formFields}
          initialValues={editingItem ?? {}}
          onSubmit={handleSubmit}
          onCancel={() => {
            setFormOpen(false);
            setEditingItem(null);
          }}
          submitLabel={editingItem ? 'Update' : 'Create'}
        />
      </Modal>

      {dataLoading && (
        <Group justify="center">
          <Loader color="blue" size="sm" />
        </Group>
      )}
    </Stack>
  );
}
