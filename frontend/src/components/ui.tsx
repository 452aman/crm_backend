import type { Sentiment, Tier } from '../types'

export const sentimentCls: Record<Sentiment, string> = {
  positive: 'bg-emerald-50 text-emerald-700 ring-emerald-200', neutral: 'bg-slate-100 text-slate-600 ring-slate-200', negative: 'bg-rose-50 text-rose-700 ring-rose-200',
}
export const tierCls: Record<Tier, string> = { A: 'bg-violet-100 text-violet-700', B: 'bg-sky-100 text-sky-700', C: 'bg-slate-100 text-slate-600' }

export const SentimentBadge = ({ s }: { s: Sentiment }) => <span className={`rounded-full px-2 py-0.5 text-xs font-medium ring-1 ${sentimentCls[s]}`}>{s}</span>
export const TierBadge = ({ t }: { t: Tier }) => <span className={`rounded px-1.5 py-0.5 text-xs font-bold ${tierCls[t]}`}>{t}</span>
export const fmtDate = (d: string | null) => (d ? new Date(d).toLocaleDateString(undefined, { day: 'numeric', month: 'short', year: 'numeric' }) : 'never')
export const Tile = ({ label, value, hint, tone }: { label: string; value: string | number; hint?: string; tone?: string }) => (
  <div className="card p-5"><div className="text-xs font-medium uppercase tracking-wide text-slate-500">{label}</div>
    <div className={`mt-1 text-3xl font-bold ${tone ?? ''}`}>{value}</div>{hint && <div className="mt-1 text-xs text-slate-400">{hint}</div>}</div>
)
export const pct = (v: number | null) => (v == null ? '–' : `${Math.round(v * 100)}%`)
