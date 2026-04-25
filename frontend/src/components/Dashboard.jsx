import React, { useState, useEffect, useCallback } from 'react';
import { ChevronDown, Zap } from 'lucide-react';
import { getMerchants, getMerchant } from '../api/client';
import { usePolling } from '../hooks/usePolling';
import { BalanceCard } from './BalanceCard';
import { PayoutForm } from './PayoutForm';
import { PayoutHistory } from './PayoutHistory';
import { LedgerTable } from './LedgerTable';

export function Dashboard() {
  const [merchants, setMerchants] = useState([]);
  const [selectedId, setSelectedId] = useState('');
  const [refreshTrigger, setRefreshTrigger] = useState(0);
  const [loadingMerchants, setLoadingMerchants] = useState(true);

  useEffect(() => {
    getMerchants()
      .then(({ data }) => {
        setMerchants(data);
        if (data.length > 0) setSelectedId(data[0].id);
      })
      .catch(console.error)
      .finally(() => setLoadingMerchants(false));
  }, []);

  const fetchMerchant = useCallback(
    () => selectedId ? getMerchant(selectedId) : Promise.reject(),
    [selectedId]
  );

  const { data: merchant, refetch: refetchMerchant } = usePolling(
    fetchMerchant,
    4000,
    [selectedId]
  );

  const handlePayoutSuccess = () => {
    setRefreshTrigger(n => n + 1);
    refetchMerchant();
  };

  const selected = merchants.find(m => m.id === selectedId);

  return (
    <div className="min-h-screen" style={{ background: '#f0ede8' }}>

      {/* ── TOPBAR ── */}
      <header
        style={{
          background: '#ffffff',
          borderBottom: '2.5px solid #0a0a0a',
          position: 'sticky',
          top: 0,
          zIndex: 50,
        }}
      >
        <div className="max-w-7xl mx-auto px-5 h-14 flex items-center justify-between gap-6">

          {/* Brand */}
          <div className="flex items-center gap-2.5 flex-shrink-0">
            <div
              style={{
                width: 28, height: 28,
                background: '#0a0a0a',
                display: 'flex', alignItems: 'center', justifyContent: 'center',
                border: '2px solid #0a0a0a',
                boxShadow: '2px 2px 0 #555',
              }}
            >
              <Zap style={{ width: 14, height: 14, color: '#fff' }} />
            </div>
            <span className="font-black text-ink text-base tracking-tight">PLAYTO PAY</span>
            <span
              className="text-[9px] font-black uppercase tracking-widest px-1.5 py-0.5 border-2 border-ink"
              style={{ background: '#f0ede8' }}
            >
              Dashboard
            </span>
          </div>

          {/* Merchant selector */}
          <div className="relative max-w-[220px] w-full">
            <select
              value={selectedId}
              onChange={e => setSelectedId(e.target.value)}
              disabled={loadingMerchants || merchants.length === 0}
              className="field appearance-none cursor-pointer pr-8"
              style={{ padding: '6px 14px', fontSize: '0.8rem', fontWeight: 700 }}
            >
              {loadingMerchants ? (
                <option value="">Loading…</option>
              ) : merchants.length === 0 ? (
                <option value="">No merchants</option>
              ) : (
                merchants.map(m => <option key={m.id} value={m.id}>{m.name}</option>)
              )}
            </select>
            <ChevronDown style={{ position: 'absolute', right: 10, top: '50%', transform: 'translateY(-50%)', width: 14, height: 14, pointerEvents: 'none', color: '#555' }} />
          </div>
        </div>
      </header>

      {/* ── MAIN ── */}
      <main className="max-w-7xl mx-auto px-5 py-8">

        {/* Page heading */}
        <div className="mb-7">
          {selected ? (
            <>
              <div className="flex items-center gap-3 mb-1">
                <h1 className="text-3xl font-black text-ink tracking-tight">{selected.name}</h1>
                <span
                  className="text-[10px] font-black uppercase px-2 py-1 border-2 border-ink"
                  style={{ background: '#fff', letterSpacing: '0.08em' }}
                >
                  Active
                </span>
              </div>
              <p className="text-sm font-semibold text-muted">{selected.email}</p>
            </>
          ) : (
            <div>
              <div className="skeleton" style={{ height: 36, width: 200, marginBottom: 8, borderRadius: 0 }} />
              <div className="skeleton" style={{ height: 14, width: 160, borderRadius: 0 }} />
            </div>
          )}
        </div>

        {/* Balance cards */}
        <BalanceCard merchant={merchant} />

        {/* ── Grid ── */}
        <div className="grid grid-cols-1 lg:grid-cols-5 gap-6">
          {/* Left: form + ledger */}
          <div className="lg:col-span-2 space-y-6">
            <PayoutForm
              merchantId={selectedId}
              onSuccess={handlePayoutSuccess}
              availableBalance={merchant?.available_balance}
            />
            <LedgerTable merchantId={selectedId} refreshTrigger={refreshTrigger} />
          </div>

          {/* Right: payout history */}
          <div className="lg:col-span-3">
            <PayoutHistory merchantId={selectedId} refreshTrigger={refreshTrigger} />
          </div>
        </div>
      </main>

      {/* ── FOOTER ── */}
      <footer
        style={{ borderTop: '2px solid #ccc', marginTop: 32 }}
        className="py-5 text-center"
      >
        <p className="text-[11px] font-bold uppercase tracking-widest text-muted">
          Playto Pay · Payout Engine · {new Date().getFullYear()}
        </p>
      </footer>
    </div>
  );
}
