import * as React from 'react';

/** Fira Code block for Cypher, driver snippets and configuration. Cypher keywords take the discovery colour. */
export interface CodeBlockProps {
  code?: string;
  /** @default "cypher" */
  language?: 'cypher' | 'plain';
  showLineNumbers?: boolean;
  /** Renders a Copy button when provided. */
  onCopy?: () => void;
}

export declare function CodeBlock(props: CodeBlockProps): React.ReactElement;
