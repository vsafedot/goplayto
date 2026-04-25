import React, { useState, useCallback } from 'react';
import { formatDistanceToNow } from 'date-fns';
import { Copy, Check, RefreshCw, ArrowRight } from 'lucide-react';
import { StatusBadge } from './StatusBadge';
import { getPayouts } from '../api/client';
import { usePolling } from '../hooks/usePolling';
import { useToast } from './Toast';

const FILTERS = ['All', 'Pending', 'Processing', 'Completed', 'Failed'];

function EmptyState({ filter }) {
  return (
    <div className="flex flex-col items-center justify-center py-14 text-center border-2 border-dashed" style={{ borderColor: '#ccc' }}>
      <div className="w-12 h-12 border-2 border-ink flex items-center justify-center mb-3">
        <ArrowRight className="w-5 h-5" />
      </div>
      <p className="font-black text-ink mb-1">{filter === 'All' ? 'No payouts yet' : `No ${filter.toLowerCase()} payouts`}</p>
      <p className="text-xs text-muted font-medium">
        {filter === 'All' ? 'Use the form to request a payout.' : 'Try a different filter.'}
      </p>
    </div>
  );
}

function SkeletonRow() {
  return (
    <tr className="border-b-2" style={{ borderColor: '#e5e2dd' }}>
      {[80, 110, 70, 80, 90].map((w, i) => (
        <td key={i} className="py-4 px-3">
          <div className="skeleton" style={{ height: 12, width: w, borderRadius: 0 }} />
        </td>
      ))}
    </tr>
  );
}

function CopyBtn({ text }) {
  const [copied, setCopied] = useState(false);
  const handle = () => {
    navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 1600);
  };
  return (
    <button
      onClick={handle}
      className="ml-1.5 inline-flex items-center opacity-30 hover:opacity-100 transition-opacity"
      title="Copy ID"
    >
      {copied ? <Check style={{ width: 11, height: 11, color: '#16a34a' }} /> : <Copy style={{ width: 11, height: 11 }} />}
    </button>
  );
}

export function PayoutHistory({ merchantId, refreshTrigger }) {
  const toast = useToast();
  const [filter, setFilter] = useState('All');
  const [lastRefreshed, setLastRefreshed] = useState(new Date());

  const fetchFn = useCallback(
    () => getPayouts(merchantId).then(res => { setLastRefreshed(new Date()); return res; }),
    [merchantId, refreshTrigger]
  );

  const { data: payouts, loading, refetch } = usePolling(fetchFn, 3000, [merchantId, refreshTrigger]);

  const filtered = (payouts ?? []).filter(p =>
    filter === 'All' ? true : p.status.toLowerCase() === filter.toLowerCase()
  );

  const count = (s) => (payouts ?? []).filter(p => p.status.toLowerCase() === s).length;

  return (
    <div className="block-card" style={{ padding: 0 }}>
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 p-6 border-b-2 border-ink">
        <div>
          <h3 className="font-black text-ink text-base">Payout History</h3>
          <div className="flex items-center gap-2 mt-0.5">
            <span className="w-2 h-2 rounded-full bg-green-600 animate-pulse flex-shrink-0" />
            <span className="text-[11px] font-semibold text-muted">
              Live · {formatDistanceToNow(lastRefreshed, { addSuffix: true })}
            </span>
          </div>
        </div>

        <div className="flex items-center gap-2">
          {/* Mini stats */}
          {payouts && payouts.length > 0 && (
            <div className="hidden sm:flex items-center gap-3 mr-2">
              <span className="text-xs font-bold" style={{ color: '#16a34a' }}>{count('completed')} done</span>
              <span className="text-xs font-bold" style={{ color: '#d97706' }}>{count('pending') + count('processing')} pending</span>
              {count('failed') > 0 && <span className="text-xs font-bold" style={{ color: '#dc2626' }}>{count('failed')} failed</span>}
            </div>
          )}
          <button
            onClick={() => { refetch(); toast('Refreshed', 'info', 1200); }}
            className="btn-ghost"
          >
            <RefreshCw style={{ width: 14, height: 14, ...(loading ? { animation: 'spin 0.8s linear infinite' } : {}) }} />
          </button>
        </div>
      </div>

      {/* Filter tabs */}
      <div className="flex items-center gap-1 px-6 py-3 border-b-2 border-ink overflow-x-auto" style={{ borderColor: '#e5e2dd' }}>
        {FILTERS.map(f => (
          <button
            key={f}
            onClick={() => setFilter(f)}
            className={`filter-tab ${filter === f ? 'active' : ''}`}
          >
            {f}
            {f !== 'All' && payouts && (
              <span className="ml-1 opacity-60">{count(f.toLowerCase())}</span>
            )}
          </button>
        ))}
      </div>

      {/* Table */}
      <div className="p-6">
        {loading && !payouts ? (
          <table className="w-full">
            <tbody>{[...Array(5)].map((_, i) => <SkeletonRow key={i} />)}</tbody>
          </table>
        ) : filtered.length === 0 ? (
          <EmptyState filter={filter} />
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full min-w-[540px] border-collapse">
              <thead>
                <tr className="border-b-2 border-ink">
                  {['Payout ID', 'Bank Account', 'Amount', 'Status', 'Updated'].map((h, i) => (
                    <th
                      key={h}
                      className="pb-3 section-heading text-left"
                      style={i >= 2 ? { textAlign: i === 2 || i === 4 ? 'right' : 'center' } : {}}
                    >
                      {h}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {filtered.map(p => (
                  <tr
                    key={p.id}
                    className="border-b-2 last:border-0 hover:bg-canvas transition-colors group"
                    style={{ borderColor: '#e5e2dd' }}
                  >
                    <td className="py-4 pr-4">
                      <div className="flex items-center">
                        <span className="font-mono text-[11px] font-bold text-muted">
                          {p.id.substring(0, 8)}…
                        </span>
                        <span className="opacity-0 group-hover:opacity-100 transition-opacity">
                          <CopyBtn text={p.id} />
                        </span>
                      </div>
                    </td>
                    <td className="py-4 pr-4 text-sm font-semibold text-ink">{p.bank_account_id}</td>
                    <td className="py-4 pr-4 text-right font-black text-ink">
                      ₹{(p.amount_paise / 100).toLocaleString('en-IN', { minimumFractionDigits: 2 })}
                    </td>
                    <td className="py-4 pr-4 text-center">
                      <StatusBadge status={p.status} />
                    </td>
                    <td className="py-4 text-right text-[11px] font-semibold text-muted">
                      {formatDistanceToNow(new Date(p.updated_at), { addSuffix: true })}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
