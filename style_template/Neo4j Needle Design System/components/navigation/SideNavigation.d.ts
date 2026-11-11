import * as React from 'react';

export interface SideNavItem {
  value?: string;
  label: React.ReactNode;
  icon?: React.ReactNode;
  trailing?: React.ReactNode;
  /** Renders as a non-interactive group heading. */
  isSection?: boolean;
}

/** Fixed left navigation for product screens. Active item uses the primary tint background. */
export interface SideNavigationProps {
  items?: SideNavItem[];
  value?: string;
  onChange?: (value: string) => void;
  header?: React.ReactNode;
  footer?: React.ReactNode;
  isCollapsed?: boolean;
  /** @default 240 */
  width?: number;
}

export declare function SideNavigation(props: SideNavigationProps): React.ReactElement;
