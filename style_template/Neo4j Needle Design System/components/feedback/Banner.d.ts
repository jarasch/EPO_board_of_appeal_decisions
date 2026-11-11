import * as React from 'react';

/**
 * Inline message attached to a surface or a form. Not a floating toast.
 *
 * @startingPoint section="Feedback" subtitle="Banners, dialog, tooltip, spinner" viewport="700x300"
 */
export interface BannerProps {
  title?: React.ReactNode;
  children?: React.ReactNode;
  /** @default "info" */
  type?: 'info' | 'success' | 'warning' | 'danger' | 'discovery';
  icon?: React.ReactNode;
  onDismiss?: () => void;
  /** Buttons rendered under the message. */
  actions?: React.ReactNode;
}

export declare function Banner(props: BannerProps): React.ReactElement;
