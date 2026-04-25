import React, { useState } from 'react';
import { Send, AlertCircle, IndianRupee, CreditCard, X, Check } from 'lucide-react';
import { createPayout } from '../api/client';
import { useToast } from './Toast';

const QUICK_AMOUNTS = [500, 2000, 5000, 10000, 25000];

function ConfirmModal({ amountRupees, bankAccount, onConfirm, onCancel, loading }) {
  const fmt = (r) => '₹' + r.toLocaleString('en-IN', { minimumFractionDigits: 2 });

  return (
    <div className="modal-overlay" onClick={onCancel}>
      <div className="modal-box" onClick={e => e.stopPropagation()}>
        {/* Header */}
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-xl font-black text-ink">Confirm Payout</h2>
          <button onClick={onCancel} className="btn-ghost !p-2">
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Details */}
        <div className="space-y-3 mb-6">
          <div className="flex items-center justify-between p-4 border-2 border-ink bg-canvas">
            <span className="text-sm font-semibold text-muted uppercase tracking-wider">Amount</span>
            <span className="text-2xl font-black text-ink">{fmt(amountRupees)}</span>
          </div>
          <div className="flex items-center justify-between p-4 border-2 border-ink bg-canvas">
            <span className="text-sm font-semibold text-muted uppercase tracking-wider">Bank Account</span>
            <span className="font-mono font-bold text-sm text-ink">{bankAccount}</span>
          </div>
          <div className="flex items-start gap-3 p-3 border-2 bg-[#fffbeb]" style={{ borderColor: '#d97706' }}>
            <AlertCircle style={{ width: 15, height: 15, color: '#d97706', marginTop: 1, flexShrink: 0 }} />
            <p className="text-xs font-medium leading-relaxed" style={{ color: '#78350f' }}>
              Funds will be held immediately and released if the payout fails.
            </p>
          </div>
        </div>

        <div className="flex gap-3">
          <button onClick={onCancel} className="btn-outline flex-1">Cancel</button>
          <button onClick={onConfirm} disabled={loading} className="btn-primary flex-1">
            {loading ? (
              <span className="w-4 h-4 border-2 border-white/40 border-t-white rounded-full animate-spin" />
            ) : (
              <><Check className="w-4 h-4" /> Confirm</>
            )}
          </button>
        </div>
      </div>
    </div>
  );
}

export function PayoutForm({ merchantId, onSuccess, availableBalance }) {
  const toast = useToast();
  const [amount, setAmount] = useState('');
  const [bankAccount, setBankAccount] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [showConfirm, setShowConfirm] = useState(false);

  const fmtMax = () => availableBalance != null
    ? '₹' + (availableBalance / 100).toLocaleString('en-IN', { minimumFractionDigits: 0 })
    : '';

  const validate = () => {
    const p = Math.round(parseFloat(amount) * 100);
    if (isNaN(p) || p <= 0) return 'Enter a valid amount';
    if (p > (availableBalance ?? 0)) return `Exceeds available balance (${fmtMax()})`;
    if (!bankAccount.trim()) return 'Enter a bank account ID';
    return null;
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    const err = validate();
    if (err) { setError(err); return; }
    setError(null);
    setShowConfirm(true);
  };

  const handleConfirm = async () => {
    setLoading(true);
    const paise = Math.round(parseFloat(amount) * 100);
    try {
      await createPayout(crypto.randomUUID(), {
        merchant: merchantId,
        amount_paise: paise,
        bank_account_id: bankAccount,
      });
      setAmount(''); setBankAccount(''); setShowConfirm(false);
      toast('Payout requested! Funds are held.', 'success');
      if (onSuccess) onSuccess();
    } catch (err) {
      const msg = err.response?.data?.error || err.response?.data?.detail || 'Payout failed';
      setError(msg);
      setShowConfirm(false);
      toast(msg, 'error');
    } finally {
      setLoading(false);
    }
  };

  const rupees = parseFloat(amount) || 0;
  const paise  = Math.round(rupees * 100);
  const avail  = availableBalance ?? 0;
  const pct    = avail > 0 ? Math.min((paise / avail) * 100, 100) : 0;
  const over   = paise > avail && paise > 0;

  return (
    <>
      <div className="block-card">
        {/* Title */}
        <div className="flex items-center gap-2 mb-5">
          <Send style={{ width: 16, height: 16 }} />
          <h3 className="font-black text-ink text-base">Request Payout</h3>
        </div>

        {/* Error */}
        {error && (
          <div className="flex items-start gap-2 p-3 mb-4 border-2 bg-[#fef2f2]" style={{ borderColor: '#dc2626' }}>
            <AlertCircle style={{ width: 14, height: 14, color: '#dc2626', marginTop: 1, flexShrink: 0 }} />
            <p className="text-xs font-semibold leading-relaxed" style={{ color: '#7f1d1d' }}>{error}</p>
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          {/* Amount */}
          <div>
            <div className="flex justify-between items-center mb-1.5">
              <label className="section-heading">Amount (INR)</label>
              {availableBalance != null && (
                <span className="text-[11px] font-semibold text-muted">Max {fmtMax()}</span>
              )}
            </div>
            <div className="relative">
              <IndianRupee style={{ position: 'absolute', left: 12, top: '50%', transform: 'translateY(-50%)', width: 14, height: 14, color: '#888', pointerEvents: 'none' }} />
              <input
                type="number"
                step="0.01"
                min="0"
                value={amount}
                onChange={e => { setAmount(e.target.value); setError(null); }}
                className={`field ${over ? 'field-error' : ''}`}
                style={{ paddingLeft: 34 }}
                placeholder="0.00"
                disabled={loading}
              />
            </div>

            {/* Progress */}
            {rupees > 0 && (
              <div className="progress-bar">
                <div className="progress-fill" style={{ width: `${pct}%`, background: over ? '#dc2626' : '#0a0a0a' }} />
              </div>
            )}

            {/* Quick chips */}
            <div className="flex gap-2 flex-wrap mt-3">
              {QUICK_AMOUNTS.map(r => (
                <button
                  key={r}
                  type="button"
                  onClick={() => { setAmount(String(r)); setError(null); }}
                  className="chip"
                  disabled={r * 100 > avail}
                >
                  ₹{r >= 1000 ? `${r / 1000}k` : r}
                </button>
              ))}
            </div>
          </div>

          {/* Bank Account */}
          <div>
            <label className="section-heading block mb-1.5">Bank Account ID</label>
            <div className="relative">
              <CreditCard style={{ position: 'absolute', left: 12, top: '50%', transform: 'translateY(-50%)', width: 14, height: 14, color: '#888', pointerEvents: 'none' }} />
              <input
                type="text"
                value={bankAccount}
                onChange={e => { setBankAccount(e.target.value); setError(null); }}
                className="field"
                style={{ paddingLeft: 34 }}
                placeholder="e.g. BA_123456789"
                disabled={loading}
              />
            </div>
          </div>

          <button type="submit" disabled={loading || !merchantId} className="btn-primary w-full">
            {loading
              ? <span className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
              : <><Send className="w-4 h-4" /> Request Payout</>
            }
          </button>
        </form>
      </div>

      {showConfirm && (
        <ConfirmModal
          amountRupees={rupees}
          bankAccount={bankAccount}
          onConfirm={handleConfirm}
          onCancel={() => setShowConfirm(false)}
          loading={loading}
        />
      )}
    </>
  );
}
