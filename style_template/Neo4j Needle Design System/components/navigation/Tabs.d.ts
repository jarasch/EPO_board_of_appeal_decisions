import * as React from 'react';

export interface TabItem { value: string; label: React.ReactNode; icon?: React.ReactNode; count?: number; isDisabled?: boolean }

/**
 * Horizontal section switch within one screen. 2px primary underline marks the active tab.
 *
 * @startingPoint section="Navigation" subtitle="Tabs, breadcrumbs and side navigation" viewport="700x320"
 */
export interface TabsProps {
  items?: TabItem[];
  value?: string;
  onChange?: (value: string) => void;
  size?: 'small' | 'medium';
}

export declare function Tabs(props: TabsProps): React.ReactElement;
