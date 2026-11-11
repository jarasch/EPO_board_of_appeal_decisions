import * as React from 'react';

/** Compact status marker. Square-ish (4px radius) so it reads differently from a Tag. */
export interface BadgeProps {
  children?: React.ReactNode;
  /** @default "neutral" */
  color?: 'neutral' | 'primary' | 'success' | 'warning' | 'danger' | 'discovery';
  /** Leading status dot. @default false */
  hasDot?: boolean;
}

export declare function Badge(props: BadgeProps): React.ReactElement;
