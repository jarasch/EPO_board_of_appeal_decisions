import * as React from 'react';

/** Full-radius pill for labels, node labels, filters and removable selections. */
export interface TagProps {
  children?: React.ReactNode;
  /** @default "neutral" */
  color?: 'neutral' | 'primary' | 'success' | 'warning' | 'danger' | 'discovery';
  /** @default "medium" */
  size?: 'small' | 'medium';
  /** Renders a remove affordance. */
  onRemove?: () => void;
}

export declare function Tag(props: TagProps): React.ReactElement;
