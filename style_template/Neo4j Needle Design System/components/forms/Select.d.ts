import * as React from 'react';

export interface SelectOption { value: string; label: string }

/** Native single-choice select styled to the Needle input spec. */
export interface SelectProps {
  label?: string;
  value?: string;
  onChange?: (value: string) => void;
  options?: SelectOption[];
  placeholder?: string;
  helpText?: string;
  errorText?: string;
  isDisabled?: boolean;
  size?: 'small' | 'medium' | 'large';
  isFullWidth?: boolean;
}

export declare function Select(props: SelectProps): React.ReactElement;
