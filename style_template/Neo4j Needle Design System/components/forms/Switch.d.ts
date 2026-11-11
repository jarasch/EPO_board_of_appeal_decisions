import * as React from 'react';

/** Immediate on/off toggle — the change applies at once, with no Save step. */
export interface SwitchProps {
  label?: React.ReactNode;
  isChecked?: boolean;
  onChange?: (checked: boolean) => void;
  isDisabled?: boolean;
  size?: 'small' | 'medium';
}

export declare function Switch(props: SwitchProps): React.ReactElement;
