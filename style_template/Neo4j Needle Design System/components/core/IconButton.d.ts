import * as React from 'react';

/** Square icon-only action. Always needs `ariaLabel` — an icon is never the sole label for an ambiguous action. */
export interface IconButtonProps {
  children?: React.ReactNode;
  /** Required. Sentence-case verb phrase, e.g. "Close panel". */
  ariaLabel: string;
  /** @default "medium" */
  size?: 'small' | 'medium' | 'large';
  /** @default "text" */
  fill?: 'text' | 'outlined';
  /** @default "neutral" */
  color?: 'neutral' | 'primary' | 'danger';
  isDisabled?: boolean;
  /** Renders in the pressed-overlay state, for toggles. */
  isActive?: boolean;
  onClick?: (e: React.MouseEvent<HTMLButtonElement>) => void;
}

export declare function IconButton(props: IconButtonProps): React.ReactElement;
