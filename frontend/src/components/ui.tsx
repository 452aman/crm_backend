import type { Sentiment, Tier } from '../types'

export const sentimentCls: Record<Sentiment, string> = {
  positive: 'bg-emerald-400/10 text-emerald-300 ring-emerald-400/30', neutral: 'bg-white/[0.07] text-slate-300 ring-white/10', negative: 'bg-rose-400/10 text-rose-300 ring-rose-400/30',
}
export const tierCls: Record<Tier, string> = { A: 'bg-violet-400/15 text-violet-300', B: 'bg-sky-400/15 text-sky-300', C: 'bg-white/[0.07] text-slate-300' }

export const SentimentBadge = ({ s }: { s: Sentiment }) => <span className={`rounded-full px-2 py-0.5 text-xs font-medium ring-1 ${sentimentCls[s]}`}>{s}</span>
export const TierBadge = ({ t }: { t: Tier }) => <span className={`rounded px-1.5 py-0.5 text-xs font-bold ${tierCls[t]}`}>{t}</span>
export const fmtDate = (d: string | null) => (d ? new Date(d).toLocaleDateString(undefined, { day: 'numeric', month: 'short', year: 'numeric' }) : 'never')
export const Tile = ({ label, value, hint, tone }: { label: string; value: string | number; hint?: string; tone?: string }) => (
  <div className="card p-5"><div className="text-xs font-medium uppercase tracking-wide text-slate-400">{label}</div>
    <div className={`mt-1 text-3xl font-bold ${tone ?? ''}`}>{value}</div>{hint && <div className="mt-1 text-xs text-slate-500">{hint}</div>}</div>
)
export const pct = (v: number | null) => (v == null ? '–' : `${Math.round(v * 100)}%`)
