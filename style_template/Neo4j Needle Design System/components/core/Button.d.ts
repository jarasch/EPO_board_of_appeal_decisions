import * as React from 'react';

/**
 * Primary action control. Filled for the single main action on a surface,
 * outlined for secondary, text for tertiary and inline actions.
 *
 * @startingPoint section="Core" subtitle="Button variants, sizes and states" viewport="700x220"
 */
export interface ButtonProps {
  children?: React.ReactNode;
  /** Visual weight. One filled button per surface. @default "filled" */
  fill?: 'filled' | 'outlined' | 'text';
  /** Intent. Never use brand teal for buttons. @default "primary" */
  color?: 'primary' | 'neutral' | 'danger';
  /** @default "medium" */
  size?: 'small' | 'medium' | 'large';
  isDisabled?: boolean;
  isLoading?: boolean;
  isFullWidth?: boolean;
  onClick?: (e: React.MouseEvent<HTMLButtonElement>) => void;
  htmlAttributes?: React.ButtonHTMLAttributes<HTMLButtonElement>;
}

export declare function Button(props: ButtonProps): React.ReactElement;
