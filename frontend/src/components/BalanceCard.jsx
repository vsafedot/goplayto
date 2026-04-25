import React from 'react';
import { TrendingUp, Clock, Wallet } from 'lucide-react';

function formatINR(paise) {
  return '₹' + (paise / 100).toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}

function SkeletonCard({ accent }) {
  return (
    <div className="stat-card" style={{ '--accent': accent }}>
      <div className="skeleton h-3 w-24 mb-4" style={{ height: 12, borderRadius: 0 }} />
      <div className="skeleton h-9 w-40 mb-4" style={{ height: 36, borderRadius: 0 }} />
      <div className="progress-bar">
        <div className="skeleton progress-fill" style={{ width: '60%' }} />
      </div>
      <div className="skeleton h-3 w-20 mt-3" style={{ height: 12, borderRadius: 0 }} />
    </div>
  );
}

export function BalanceCard({ merchant }) {
  if (!merchant) {
    return (
      <div className="grid grid-cols-1 md:grid-cols-3 gap-5 mb-8">
        <SkeletonCard /><SkeletonCard /><SkeletonCard />
      </div>
    );
  }

  const available = merchant.available_balance ?? 0;
  const held      = merchant.held_balance ?? 0;
  const total     = available + held;
  const availPct  = total > 0 ? Math.round((available / total) * 100) : 0;
  const heldPct   = total > 0 ? Math.round((held / total) * 100) : 0;

  const cards = [
    {
      label: 'Available',
      value: formatINR(available),
      sub: `${availPct}% of total balance`,
      icon: TrendingUp,
      accent: '#16a34a',
      barPct: availPct,
      barColor: '#16a34a',
      cls: 'stat-card-green',
    },
    {
      label: 'Held',
      value: formatINR(held),
      sub: 'funds locked in pending payouts',
      icon: Clock,
      accent: '#d97706',
      barPct: heldPct,
      barColor: '#d97706',
      cls: 'stat-card-amber',
    },
    {
      label: 'Total',
      value: formatINR(total),
      sub: 'available + held',
      icon: Wallet,
      accent: '#0a0a0a',
      barPct: 100,
      barColor: '#0a0a0a',
      cls: 'stat-card-black',
    },
  ];

  return (
    <div className="grid grid-cols-1 md:grid-cols-3 gap-5 mb-8">
      {cards.map(({ label, value, sub, icon: Icon, accent, barPct, barColor, cls }) => (
        <div key={label} className={`stat-card ${cls}`}>
          <div className="flex items-center justify-between mb-4">
            <p className="section-heading">{label} Balance</p>
            <Icon style={{ width: 16, height: 16, color: accent }} />
          </div>
          <p className="text-[2rem] font-black tracking-tight leading-none text-ink">{value}</p>
          <div className="progress-bar">
            <div className="progress-fill" style={{ width: `${barPct}%`, background: barColor }} />
          </div>
          <p className="text-[11px] text-muted mt-2 font-medium">{sub}</p>
        </div>
      ))}
    </div>
  );
}
