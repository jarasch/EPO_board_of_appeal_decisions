import React from 'react';

export function LoadingSpinner({ size = 24, label }) {
  return (
    <span role="status" aria-live="polite" style={{ display: 'inline-flex', alignItems: 'center', gap: 8, fontFamily: 'var(--font-sans)' }}>
      <svg width={size} height={size} viewBox="0 0 16 16" fill="none" aria-hidden="true" style={{ color: 'var(--primary-icon)' }}>
        <circle cx="8" cy="8" r="6.5" stroke="currentColor" strokeWidth="2" opacity="0.25" />
        <path d="M8 1.5A6.5 6.5 0 0 1 14.5 8" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
          <animateTransform attributeName="transform" type="rotate" from="0 8 8" to="360 8 8" dur="0.7s" repeatCount="indefinite" />
        </path>
      </svg>
      {label && <span style={{ fontSize: 14, lineHeight: 1.43, color: 'var(--text-weak)' }}>{label}</span>}
    </span>
  );
}
