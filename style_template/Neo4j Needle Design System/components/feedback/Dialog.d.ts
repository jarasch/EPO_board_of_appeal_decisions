import * as React from 'react';

/** Modal. Overlay elevation, 16px radius, actions right-aligned on a canvas-tinted footer. */
export interface DialogProps {
  isOpen?: boolean;
  title?: React.ReactNode;
  children?: React.ReactNode;
  /** Footer buttons, destructive action last. */
  actions?: React.ReactNode;
  onClose?: () => void;
  /** 400 / 560 / 720px. @default "medium" */
  size?: 'small' | 'medium' | 'large';
}

export declare function Dialog(props: DialogProps): React.ReactElement | null;
