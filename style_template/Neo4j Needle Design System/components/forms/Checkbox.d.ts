import * as React from 'react';

/** Multi-select toggle. Supports an indeterminate state for parent rows. */
export interface CheckboxProps {
  label?: React.ReactNode;
  isChecked?: boolean;
  isIndeterminate?: boolean;
  onChange?: (checked: boolean) => void;
  isDisabled?: boolean;
  helpText?: string;
}

export declare function Checkbox(props: CheckboxProps): React.ReactElement;
