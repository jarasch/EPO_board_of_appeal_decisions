import * as React from 'react';

/**
 * Surface container: white, 12px radius, 1px weak border, raised elevation.
 *
 * @startingPoint section="Core" subtitle="Card, badge and tag primitives" viewport="700x260"
 */
export interface CardProps {
  children?: React.ReactNode;
  header?: React.ReactNode;
  footer?: React.ReactNode;
  /** 16px small, 24px medium. @default "medium" */
  padding?: 'none' | 'small' | 'medium';
  /** Adds a hover border change and pointer cursor. */
  isInteractive?: boolean;
  onClick?: () => void;
  style?: React.CSSProperties;
}

export declare function Card(props: CardProps): React.ReactElement;
