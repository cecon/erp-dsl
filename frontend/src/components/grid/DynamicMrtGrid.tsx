import { ActionIcon, Box, Group, Tooltip } from '@mantine/core';
import { IconEdit, IconTrash } from '@tabler/icons-react';
import {
  MantineReactTable,
  useMantineReactTable,
  type MRT_ColumnDef,
} from 'mantine-react-table';
import { useMemo } from 'react';

/* eslint-disable @typescript-eslint/no-explicit-any */

interface ColumnSchema {
  id: string;
  key: string;
  label: string;
}

interface DynamicMrtGridProps {
  columns: ColumnSchema[];
  data: any[];
  total: number;
  page: number; // 1-based from PageRenderer
  pageSize: number;
  onPageChange: (page: number) => void;
  onEdit?: (row: any) => void;
  onDelete?: (row: any) => void;
}

export function DynamicMrtGrid({
  columns: columnSchema,
  data,
  total,
  page,
  pageSize,
  onPageChange,
  onEdit,
  onDelete,
}: DynamicMrtGridProps) {
  // Convert generic column schema to MRT column definitions
  const mrtColumns = useMemo<MRT_ColumnDef<any>[]>(() => {
    return columnSchema.map((col) => ({
      id: col.id,
      accessorKey: col.key, // Ensure accessorKey exactly matches object keys
      header: col.label,
      Cell: ({ cell }) => {
        const val = cell.getValue();
        if (col.key === 'price' && val != null) {
          return `R$ ${Number(val).toFixed(2)}`;
        }
        return String(val ?? '—');
      },
    }));
  }, [columnSchema]);

  const table = useMantineReactTable({
    columns: mrtColumns,
    data: data,
    
    // Core features
    enableGrouping: true,
    enableGlobalFilter: true, // Prominent top search bar
    enableColumnResizing: true,
    
    // Pagination (Manual / Server-side)
    manualPagination: true,
    rowCount: total,
    onPaginationChange: (updater) => {
      // Updater can be a function or a new state object
      const newState =
        typeof updater === 'function'
          ? updater({ pageIndex: page - 1, pageSize })
          : updater;
      
      // PageRenderer uses 1-based page indexing
      onPageChange(newState.pageIndex + 1);
    },
    state: {
      pagination: {
        pageIndex: page - 1, // MRT uses 0-based page index
        pageSize,
      },
      isLoading: false, // Could be linked to React Query if passed
    },

    // Actions
    enableRowActions: !!(onEdit || onDelete),
    renderRowActions: ({ row }) => (
      <Group gap="xs" wrap="nowrap">
        {onEdit && (
          <Tooltip label="Edit">
            <ActionIcon
              variant="subtle"
              color="blue"
              onClick={() => onEdit(row.original)}
              size="sm"
            >
              <IconEdit size={16} />
            </ActionIcon>
          </Tooltip>
        )}
        {onDelete && (
          <Tooltip label="Delete">
            <ActionIcon
              variant="subtle"
              color="red"
              onClick={() => onDelete(row.original)}
              size="sm"
            >
              <IconTrash size={16} />
            </ActionIcon>
          </Tooltip>
        )}
      </Group>
    ),

    // Theming & UX
    mantineTableProps: {
      striped: true,
      highlightOnHover: true,
      withColumnBorders: true,
    },
    mantinePaperProps: {
      radius: 'md',
      withBorder: true,
      shadow: 'sm',
      style: { overflow: 'hidden' }, // Ensures inner table follows border radius
    },
  });

  return (
    <Box className="admin-card" style={{ padding: 0 }}>
      {/* 
        This is a Beta Rollout component.
        We embed MRT inside our standard admin-card pattern.
      */}
      <MantineReactTable table={table} />
    </Box>
  );
}
