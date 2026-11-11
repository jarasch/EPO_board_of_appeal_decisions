import * as React from 'react';

export interface BreadcrumbItem { label: React.ReactNode; href?: string }

/** Ancestor trail for nested management screens. Current page is last, bold, not a link. */
export interface BreadcrumbsProps {
  items?: BreadcrumbItem[];
  onNavigate?: (item: BreadcrumbItem, index: number) => void;
}

export declare function Breadcrumbs(props: BreadcrumbsProps): React.ReactElement;
