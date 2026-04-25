import React, { useEffect, useState } from 'react';
import { formatDistanceToNow } from 'date-fns';
import { ArrowDownLeft, ArrowUpRight, PauseCircle, RotateCcw, BookOpen } from 'lucide-react';
import { getLedger } from '../api/client';

const ENTRY_CFG = {
  credit:  { icon: ArrowDownLeft, color: '#16a34a', sign: '+' },
  debit:   { icon: ArrowUpRight,  color: '#dc2626', sign: '−' },
  hold:    { icon: PauseCircle,   color: '#d97706', sign: '−' },
  release: { icon: RotateCcw,     color: '#2563eb', sign: '+' },
};

function SkeletonRow() {
  return (
    <div className="flex items-center gap-3 py-3 border-b-2" style={{ borderColor: '#e5e2dd' }}>
      <div className="skeleton w-8 h-8 flex-shrink-0" style={{ borderRadius: 0 }} />
      <div className="flex-1 space-y-1.5">
        <div className="skeleton" style={{ height: 11, width: 80, borderRadius: 0 }} />
        <div className="skeleton" style={{ height: 11, width: 140, borderRadius: 0 }} />
      </div>
      <div className="skeleton" style={{ height: 13, width: 60, borderRadius: 0 }} />
    </div>
  );
}

export function LedgerTable({ merchantId, refreshTrigger }) {
  const [entries, setEntries] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!merchantId) return;
    // Reset immediately so old merchant data never flashes
    setEntries(null);
    setLoading(true);
    getLedger(merchantId)
      .then(({ data }) => setEntries(data))
      .catch(console.error)
      .finally(() => setLoading(false));
  }, [merchantId, refreshTrigger]);

  return (
    <div className="block-card" style={{ padding: 0 }}>
      {/* Header */}
      <div className="flex items-center gap-2 p-6 border-b-2 border-ink">
        <BookOpen style={{ width: 16, height: 16 }} />
        <div>
          <h3 className="font-black text-ink text-base leading-none">Ledger</h3>
          <p className="text-[11px] font-semibold text-muted mt-0.5">Credits, debits &amp; holds</p>
        </div>
      </div>

      <div className="p-6">
        {loading ? (
          <div>{[...Array(5)].map((_, i) => <SkeletonRow key={i} />)}</div>
        ) : !entries || entries.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-10 border-2 border-dashed" style={{ borderColor: '#ccc' }}>
            <BookOpen style={{ width: 24, height: 24, color: '#ccc' }} className="mb-2" />
            <p className="text-xs font-semibold text-muted">No ledger entries</p>
          </div>
        ) : (
          <div className="max-h-[380px] overflow-y-auto -mr-2 pr-2">
            {entries.map((entry, idx) => {
              const type = entry.entry_type?.toLowerCase() ?? 'credit';
              const cfg  = ENTRY_CFG[type] ?? ENTRY_CFG.credit;
              const Icon = cfg.icon;
              const isPos = ['credit', 'release'].includes(type);
              const isLast = idx === entries.length - 1;

              return (
                <div
                  key={entry.id}
                  className="flex items-center gap-3 py-3"
                  style={{ borderBottom: isLast ? 'none' : '1.5px solid #e5e2dd' }}
                >
                  {/* Icon box */}
                  <div
                    className="w-8 h-8 flex items-center justify-center flex-shrink-0 border-2"
                    style={{ borderColor: cfg.color, backgroundColor: `${cfg.color}10` }}
                  >
                    <Icon style={{ width: 13, height: 13, color: cfg.color }} />
                  </div>

                  {/* Info */}
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2">
                      <span
                        className="text-[10px] font-black uppercase tracking-wider border-2 px-1.5 py-px"
                        style={{ color: cfg.color, borderColor: cfg.color }}
                      >
                        {entry.entry_type_display ?? type}
                      </span>
                      <span className="text-[10px] font-semibold text-muted">
                        {formatDistanceToNow(new Date(entry.created_at), { addSuffix: true })}
                      </span>
                    </div>
                    <p className="text-[11px] font-medium text-muted mt-0.5 truncate">
                      {entry.description || 'System entry'}
                    </p>
                  </div>

                  {/* Amount */}
                  <p
                    className="text-sm font-black flex-shrink-0"
                    style={{ color: isPos ? '#16a34a' : '#dc2626' }}
                  >
                    {cfg.sign}₹{(entry.amount_paise / 100).toLocaleString('en-IN', { minimumFractionDigits: 2 })}
                  </p>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}
