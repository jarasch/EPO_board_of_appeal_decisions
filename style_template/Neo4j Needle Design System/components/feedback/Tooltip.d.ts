import * as React from 'react';

/** Short label on hover or focus. Never holds information the user needs to complete a task. */
export interface TooltipProps {
  children?: React.ReactNode;
  content?: React.ReactNode;
  /** @default "top" */
  placement?: 'top' | 'bottom' | 'left' | 'right';
}

export declare function Tooltip(props: TooltipProps): React.ReactElement;
