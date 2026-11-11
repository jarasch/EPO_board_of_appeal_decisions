import * as React from 'react';

export interface GraphLegendLabel { label: string; count?: number; color?: string }

/** Node-label legend for a graph visualisation. Colours come from the graph node palette, assigned in order. */
export interface GraphLegendProps {
  labels?: Array<string | GraphLegendLabel>;
  /** When provided, labels not in this list render muted. */
  activeLabels?: string[];
  onToggle?: (label: string) => void;
  /** @default "Node labels" */
  title?: string;
}

export declare function GraphLegend(props: GraphLegendProps): React.ReactElement;
