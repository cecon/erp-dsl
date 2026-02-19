import { Alert, Button, Group, Loader, Modal, Stack, Text } from '@mantine/core';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { useCallback, useState } from 'react';
import { useParams } from 'react-router-dom';
import api from '../../services/api';
import { DynamicForm } from './DynamicForm';
import { EnterpriseGrid } from '../../components/grid/EnterpriseGrid';

/* eslint-disable @typescript-eslint/no-explicit-any */

interface PageSchema {
  id: string;
  page_key: string;
  scope: string;
  schema: {
    title?: string;
    description?: string;
    components?: any[];
    columns?: any[];
    actions?: any[];
  };
}

export function PageRenderer() {
  const { pageKey } = useParams<{ pageKey: string }>();
  const queryClient = useQueryClient();
  const [page, setPage] = useState(1);
  const [formOpen, setFormOpen] = useState(false);
  const [editingItem, setEditingItem] = useState<any>(null);
  const pageSize = 20;

  const { data: pageData, isLoading: pageLoading } = useQuery<PageSchema>({
    queryKey: ['page', pageKey],
    queryFn: () => api.get(`/pages/${pageKey}`).then((r) => r.data),
    enabled: !!pageKey,
  });

  const { data: gridData, isLoading: dataLoading } = useQuery({
    queryKey: ['products', page],
    queryFn: () =>
      api
        .get('/products', {
          params: { offset: (page - 1) * pageSize, limit: pageSize },
        })
        .then((r) => r.data),
    enabled: pageKey === 'products',
  });

  const createMutation = useMutation({
    mutationFn: (values: any) => api.post('/products', values),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['products'] });
      setFormOpen(false);
    },
  });

  const updateMutation = useMutation({
    mutationFn: (values: any) =>
      api.put(`/products/${values.id}`, values),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['products'] });
      setFormOpen(false);
      setEditingItem(null);
    },
  });

  const deleteMutation = useMutation({
    mutationFn: (id: string) => api.delete(`/products/${id}`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['products'] });
    },
  });

  const handleEdit = useCallback((row: any) => {
    setEditingItem(row);
    setFormOpen(true);
  }, []);

  const handleDelete = useCallback(
    (row: any) => {
      if (confirm(`Delete "${row.name}"?`)) {
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

  if (pageLoading) {
    return (
      <Stack align="center" justify="center" h={400}>
        <Loader color="blue" size="lg" />
        <Text c="dimmed" size="sm">Loading page schema…</Text>
      </Stack>
    );
  }

  if (!pageData) {
    return (
      <Alert color="red" title="Page not found" radius="md">
        The page <strong>{pageKey}</strong> could not be found.
      </Alert>
    );
  }

  const schema = pageData.schema;
  const formFields =
    schema.components
      ?.find((c: any) => c.type === 'form')
      ?.components?.map((f: any) => ({
        id: f.id,
        type: f.type,
        label: f.label,
      })) ?? [];

  const hasCreateAction = schema.actions?.some(
    (a: any) => a.type === 'create'
  );

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
        {hasCreateAction && (
          <Button
            onClick={() => {
              setEditingItem(null);
              setFormOpen(true);
            }}
          >
            + New Product
          </Button>
        )}
      </div>

      {/* Data Grid */}
      {schema.columns && (
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
      )}

      {/* Create/Edit Modal */}
      <Modal
        opened={formOpen}
        onClose={() => {
          setFormOpen(false);
          setEditingItem(null);
        }}
        title={editingItem ? 'Edit Product' : 'New Product'}
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
