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
    positionActionsColumn: 'last',
    displayColumnDefOptions: {
      'mrt-row-actions': {
        header: 'Ações',
        mantineTableHeadCellProps: {
          align: 'right',
        },
        mantineTableBodyCellProps: {
          align: 'right',
        },
      },
    },
    renderRowActions: ({ row }) => (
      <Group gap="xs" wrap="nowrap" justify="flex-end">
        {onEdit && (
          <Tooltip label="Edit">
            <ActionIcon
              variant="light"
              color="blue"
              onClick={() => onEdit(row.original)}
              size="md"
              radius="md"
            >
              <IconEdit size={16} />
            </ActionIcon>
          </Tooltip>
        )}
        {onDelete && (
          <Tooltip label="Delete">
            <ActionIcon
              variant="light"
              color="red"
              onClick={() => onDelete(row.original)}
              size="md"
              radius="md"
            >
              <IconTrash size={16} />
            </ActionIcon>
          </Tooltip>
        )}
      </Group>
    ),

    // Theming & UX
    mantineTableProps: {
      highlightOnHover: true,
      withColumnBorders: false,
      withRowBorders: true,
      horizontalSpacing: 'md',
      verticalSpacing: 'md',
    },
    mantinePaperProps: {
      radius: 'md',
      withBorder: false,
      shadow: 'none',
      style: { background: 'transparent' },
    },
    mantineTableHeadCellProps: {
      style: {
        color: 'var(--text-muted)',
        fontWeight: 600,
        fontSize: '11px',
        textTransform: 'uppercase',
        letterSpacing: '0.06em',
      },
    },
    mantineTableBodyCellProps: {
      style: {
        fontSize: '13px',
      },
    },
    mantineTopToolbarProps: {
      style: {
        background: 'transparent',
        padding: '16px 20px',
        borderBottom: '1px solid var(--border-default)',
      },
    },
    mantineBottomToolbarProps: {
      style: {
        background: 'transparent',
        padding: '16px 20px',
        borderTop: '1px solid var(--border-default)',
      },
    },
  });

  return (
    <Box className="admin-card mrt-premium-grid" style={{ padding: 0, overflow: 'hidden' }}>
      {/* 
        This is a Beta Rollout component.
        We embed MRT inside our standard admin-card pattern.
      */}
      <MantineReactTable table={table} />
    </Box>
  );
}
