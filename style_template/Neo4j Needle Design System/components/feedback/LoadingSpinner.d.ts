import * as React from 'react';

/** Indeterminate progress. One continuous rotation, no pulsing or bouncing. */
export interface LoadingSpinnerProps {
  /** Pixel diameter. 16 inline, 24 default, 40 for a full-panel load. @default 24 */
  size?: number;
  /** Optional text, e.g. "Running query…". */
  label?: string;
}

export declare function LoadingSpinner(props: LoadingSpinnerProps): React.ReactElement;
