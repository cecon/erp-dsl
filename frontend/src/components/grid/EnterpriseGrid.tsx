import { ActionIcon, Group, Text, Pagination } from '@mantine/core';
import {
  useReactTable,
  getCoreRowModel,
  flexRender,
  type ColumnDef,
  type HeaderGroup,
  type Header,
  type Row,
  type Cell,
} from '@tanstack/react-table';
import { useMemo } from 'react';

/* eslint-disable @typescript-eslint/no-explicit-any */

interface ColumnSchema {
  id: string;
  key: string;
  label: string;
}

interface EnterpriseGridProps {
  columns: ColumnSchema[];
  data: any[];
  total: number;
  page: number;
  pageSize: number;
  onPageChange: (page: number) => void;
  onEdit?: (row: any) => void;
  onDelete?: (row: any) => void;
}

export function EnterpriseGrid({
  columns: columnSchema,
  data,
  total,
  page,
  pageSize,
  onPageChange,
  onEdit,
  onDelete,
}: EnterpriseGridProps) {
  const columns = useMemo<ColumnDef<any>[]>(() => {
    const cols: ColumnDef<any>[] = columnSchema.map((col) => ({
      id: col.id,
      accessorKey: col.key,
      header: col.label,
      cell: (info: any) => {
        const val = info.getValue();
        if (col.key === 'price' && val != null) {
          return `R$ ${Number(val).toFixed(2)}`;
        }
        return String(val ?? '—');
      },
    }));

    if (onEdit || onDelete) {
      cols.push({
        id: 'actions',
        header: 'Actions',
        cell: ({ row }: any) => (
          <Group gap={4}>
            {onEdit && (
              <ActionIcon
                variant="subtle"
                color="blue"
                onClick={() => onEdit(row.original)}
                size="sm"
                radius="md"
              >
                ✏️
              </ActionIcon>
            )}
            {onDelete && (
              <ActionIcon
                variant="subtle"
                color="red"
                onClick={() => onDelete(row.original)}
                size="sm"
                radius="md"
              >
                🗑️
              </ActionIcon>
            )}
          </Group>
        ),
      });
    }

    return cols;
  }, [columnSchema, onEdit, onDelete]);

  const table = useReactTable({
    data,
    columns,
    getCoreRowModel: getCoreRowModel(),
  });

  const totalPages = Math.ceil(total / pageSize);

  return (
    <div className="admin-card" style={{ padding: 0, overflow: 'hidden' }}>
      <table className="enterprise-table">
        <thead>
          {table.getHeaderGroups().map((headerGroup: HeaderGroup<any>) => (
            <tr key={headerGroup.id}>
              {headerGroup.headers.map((header: Header<any, any>) => (
                <th key={header.id}>
                  {flexRender(
                    header.column.columnDef.header,
                    header.getContext()
                  )}
                </th>
              ))}
            </tr>
          ))}
        </thead>
        <tbody>
          {table.getRowModel().rows.length === 0 ? (
            <tr>
              <td
                colSpan={columns.length}
                style={{ textAlign: 'center', padding: 48 }}
              >
                <Text c="dimmed" size="sm">
                  No records found
                </Text>
              </td>
            </tr>
          ) : (
            table.getRowModel().rows.map((row: Row<any>) => (
              <tr key={row.id}>
                {row.getVisibleCells().map((cell: Cell<any, any>) => (
                  <td key={cell.id}>
                    {flexRender(cell.column.columnDef.cell, cell.getContext())}
                  </td>
                ))}
              </tr>
            ))
          )}
        </tbody>
      </table>

      {totalPages > 1 && (
        <Group justify="center" p="md" style={{ borderTop: '1px solid var(--border-default)' }}>
          <Pagination
            value={page}
            onChange={onPageChange}
            total={totalPages}
            size="sm"
          />
        </Group>
      )}
    </div>
  );
}
