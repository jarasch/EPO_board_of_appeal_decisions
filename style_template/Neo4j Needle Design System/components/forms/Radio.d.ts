import * as React from 'react';

/** One choice from 2–3 visible options. For longer lists use `Select`. */
export interface RadioProps {
  label?: React.ReactNode;
  value?: string;
  /** Shared group name. */
  name?: string;
  isChecked?: boolean;
  onChange?: (value: string) => void;
  isDisabled?: boolean;
  helpText?: string;
}

export declare function Radio(props: RadioProps): React.ReactElement;
