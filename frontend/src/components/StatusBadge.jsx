import React from 'react';

const STATUS_CFG = {
  pending:    { dot: '#2563eb', text: '#1e3a8a', bg: '#eff6ff', border: '#2563eb', label: 'Pending' },
  processing: { dot: '#d97706', text: '#78350f', bg: '#fffbeb', border: '#d97706', label: 'Processing' },
  completed:  { dot: '#16a34a', text: '#14532d', bg: '#f0fdf4', border: '#16a34a', label: 'Completed' },
  failed:     { dot: '#dc2626', text: '#7f1d1d', bg: '#fef2f2', border: '#dc2626', label: 'Failed' },
};

export function StatusBadge({ status }) {
  const s = status?.toLowerCase() ?? 'pending';
  const { dot, text, bg, border, label } = STATUS_CFG[s] ?? STATUS_CFG.pending;
  const isPulsing = s === 'processing';

  return (
    <span
      className="inline-flex items-center gap-1.5 px-2 py-0.5 text-[11px] font-bold uppercase tracking-wider border-2"
      style={{ background: bg, color: text, borderColor: border }}
    >
      <span
        className="w-1.5 h-1.5 rounded-full flex-shrink-0"
        style={{
          background: dot,
          animation: isPulsing ? 'pulse 1.2s ease-in-out infinite' : 'none',
        }}
      />
      {label}
    </span>
  );
}
