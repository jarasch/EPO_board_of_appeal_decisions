import * as React from 'react';

export interface DataTableColumn {
  key: string;
  header: React.ReactNode;
  width?: number | string;
  align?: 'left' | 'right' | 'center';
  /** Renders the cell in Fira Code — for ids, types and query values. */
  isCode?: boolean;
  render?: (row: any) => React.ReactNode;
}

/**
 * Tabular results and management lists. Header on the canvas tint, weak borders between rows.
 *
 * @startingPoint section="Data" subtitle="Table, code block and graph legend" viewport="700x340"
 */
export interface DataTableProps {
  columns?: DataTableColumn[];
  rows?: any[];
  /** Tighter rows for query results. */
  isDense?: boolean;
  emptyText?: string;
  onRowClick?: (row: any) => void;
}

export declare function DataTable(props: DataTableProps): React.ReactElement;
