"use client";

import React, { useEffect, useMemo, useState } from "react";
import { ChevronDown, ChevronUp, ChevronsUpDown } from "lucide-react";

export type SortDirection = "asc" | "desc";

export type DataTableColumn<T> = {
  id: string;
  header: string;
  cell: (row: T) => React.ReactNode;
  sortValue?: (row: T) => string | number | null | undefined;
  className?: string;
  headerClassName?: string;
};

export type DataTableProps<T> = {
  rows: T[];
  columns: Array<DataTableColumn<T>>;
  getRowKey: (row: T) => string | number;
  initialSort?: { columnId: string; direction: SortDirection };
  pageSize?: number;
  pageSizeOptions?: number[];
  emptyState?: React.ReactNode;
};

function compareValues(a: string | number, b: string | number): number {
  if (typeof a === "number" && typeof b === "number") return a - b;
  return String(a).localeCompare(String(b));
}

export function DataTable<T>({
  rows,
  columns,
  getRowKey,
  initialSort,
  pageSize: pageSizeProp = 25,
  pageSizeOptions = [10, 25, 50],
  emptyState,
}: DataTableProps<T>) {
  const [sort, setSort] = useState<
    { columnId: string; direction: SortDirection } | undefined
  >(initialSort);

  const [pageSize, setPageSize] = useState<number>(pageSizeProp);
  const [page, setPage] = useState<number>(1);

  const sortedRows = useMemo(() => {
    if (!sort) return rows;

    const col = columns.find((c) => c.id === sort.columnId);
    if (!col?.sortValue) return rows;

    const directionMultiplier = sort.direction === "asc" ? 1 : -1;

    return [...rows].sort((ra, rb) => {
      const va = col.sortValue?.(ra);
      const vb = col.sortValue?.(rb);

      if (va == null && vb == null) return 0;
      if (va == null) return 1;
      if (vb == null) return -1;

      return compareValues(va, vb) * directionMultiplier;
    });
  }, [rows, sort, columns]);

  const totalRows = sortedRows.length;
  const totalPages = Math.max(1, Math.ceil(totalRows / pageSize));

  useEffect(() => {
    setPage((p) => Math.min(Math.max(1, p), totalPages));
  }, [totalPages]);

  const pagedRows = useMemo(() => {
    const start = (page - 1) * pageSize;
    const end = start + pageSize;
    return sortedRows.slice(start, end);
  }, [sortedRows, page, pageSize]);

  const rangeStart = totalRows === 0 ? 0 : (page - 1) * pageSize + 1;
  const rangeEnd = Math.min(page * pageSize, totalRows);

  function toggleSort(columnId: string) {
    setPage(1);
    setSort((prev) => {
      if (!prev || prev.columnId !== columnId) {
        return { columnId, direction: "desc" };
      }
      return {
        columnId,
        direction: prev.direction === "desc" ? "asc" : "desc",
      };
    });
  }

  if (totalRows === 0) {
    return emptyState ? (
      <>{emptyState}</>
    ) : (
      <div className="rounded-lg border border-border bg-card p-6 text-sm text-muted-foreground">
        No data.
      </div>
    );
  }

  return (
    <div className="rounded-lg border border-border bg-card overflow-hidden">
      <div className="overflow-x-auto">
        <table className="min-w-full divide-y divide-border">
          <thead className="bg-muted">
            <tr>
              {columns.map((col) => {
                const isSortable = Boolean(col.sortValue);
                const isActive = sort?.columnId === col.id;

                return (
                  <th
                    key={col.id}
                    scope="col"
                    className={
                      col.headerClassName ??
                      "px-4 py-3 text-left text-xs font-semibold uppercase tracking-wider text-muted-foreground"
                    }
                  >
                    {isSortable ? (
                      <button
                        type="button"
                        className="inline-flex items-center gap-1 hover:text-card-foreground"
                        onClick={() => toggleSort(col.id)}
                      >
                        <span>{col.header}</span>
                        {isActive ? (
                          sort?.direction === "asc" ? (
                            <ChevronUp className="h-3.5 w-3.5" />
                          ) : (
                            <ChevronDown className="h-3.5 w-3.5" />
                          )
                        ) : (
                          <ChevronsUpDown className="h-3.5 w-3.5" />
                        )}
                      </button>
                    ) : (
                      col.header
                    )}
                  </th>
                );
              })}
            </tr>
          </thead>
          <tbody className="divide-y divide-border">
            {pagedRows.map((row) => (
              <tr key={getRowKey(row)} className="hover:bg-muted">
                {columns.map((col) => (
                  <td
                    key={col.id}
                    className={
                      col.className ??
                      "px-4 py-3 text-sm text-card-foreground whitespace-nowrap"
                    }
                  >
                    {col.cell(row)}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div className="flex flex-col gap-3 border-t border-border bg-card px-4 py-3 sm:flex-row sm:items-center sm:justify-between">
        <div className="text-xs text-muted-foreground">
          Showing <span className="text-card-foreground">{rangeStart}</span>–
          <span className="text-card-foreground">{rangeEnd}</span> of{" "}
          <span className="text-card-foreground">{totalRows}</span>
        </div>

        <div className="flex items-center gap-3">
          {pageSizeOptions.length > 1 ? (
            <label className="flex items-center gap-2 text-xs text-muted-foreground">
              Rows
              <select
                value={pageSize}
                onChange={(e) => {
                  setPage(1);
                  setPageSize(Number(e.target.value));
                }}
                className="h-8 rounded-md border border-border bg-card px-2 text-xs text-card-foreground focus:outline-none focus-visible:ring-2 focus-visible:ring-primary"
              >
                {pageSizeOptions.map((opt) => (
                  <option key={opt} value={opt}>
                    {opt}
                  </option>
                ))}
              </select>
            </label>
          ) : null}

          <div className="flex items-center gap-2">
            <button
              type="button"
              onClick={() => setPage((p) => Math.max(1, p - 1))}
              disabled={page <= 1}
              className="h-8 rounded-md border border-border bg-card px-3 text-xs text-card-foreground disabled:opacity-50"
            >
              Prev
            </button>
            <div className="text-xs text-muted-foreground">
              Page <span className="text-card-foreground">{page}</span> of{" "}
              <span className="text-card-foreground">{totalPages}</span>
            </div>
            <button
              type="button"
              onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
              disabled={page >= totalPages}
              className="h-8 rounded-md border border-border bg-card px-3 text-xs text-card-foreground disabled:opacity-50"
            >
              Next
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
