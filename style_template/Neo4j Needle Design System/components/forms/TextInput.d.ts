import * as React from 'react';

/**
 * Single-line text field with label, help text and error text.
 *
 * @startingPoint section="Forms" subtitle="Inputs, select, checkbox, radio, switch" viewport="700x320"
 */
export interface TextInputProps {
  label?: string;
  value?: string;
  onChange?: (value: string) => void;
  placeholder?: string;
  helpText?: string;
  /** Presence switches the field to the error style and replaces helpText. */
  errorText?: string;
  isDisabled?: boolean;
  isReadOnly?: boolean;
  /** @default "medium" */
  size?: 'small' | 'medium' | 'large';
  leftIcon?: React.ReactNode;
  rightIcon?: React.ReactNode;
  type?: string;
  isFullWidth?: boolean;
}

export declare function TextInput(props: TextInputProps): React.ReactElement;
