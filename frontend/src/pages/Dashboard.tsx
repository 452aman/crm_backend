import { AlertTriangle, CheckCircle2, Lightbulb } from 'lucide-react'
import { useState } from 'react'
import { Link } from 'react-router-dom'
import { Area, AreaChart, Bar, BarChart, CartesianGrid, Cell, Pie, PieChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import { Tile, TierBadge, fmtDate, pct } from '../components/ui'
import { useAtRiskQuery, useDoneFollowupMutation, useFollowupsQuery, useOverviewQuery } from '../store/api'

const SENT = { positive: '#10b981', neutral: '#94a3b8', negative: '#f43f5e' }

export default function Dashboard() {
  const [days, setDays] = useState(30)
  const { data: o } = useOverviewQuery({ days })
  const { data: risk = [] } = useAtRiskQuery()
  const { data: fu = [] } = useFollowupsQuery()
  const [done] = useDoneFollowupMutation()
  if (!o) return <p className="text-slate-500">Loading…</p>
  const sent = Object.entries(o.by_sentiment).map(([name, value]) => ({ name, value }))
  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <h1 className="text-2xl font-bold">Dashboard</h1>
        <div className="inline-flex rounded-lg bg-slate-200/70 p-1 text-sm">{[7, 30, 90].map((d) => <button key={d} onClick={() => setDays(d)} className={`rounded-md px-3 py-1 font-medium ${days === d ? 'bg-white shadow-sm' : 'text-slate-500'}`}>{d}d</button>)}</div>
      </div>
      <div className="grid grid-cols-2 gap-4 lg:grid-cols-5">
        <Tile label="Interactions" value={o.interactions} hint={`last ${days} days`} />
        <Tile label="Doctors reached" value={o.unique_hcps} />
        <Tile label="Positive rate" value={pct(o.positive_rate)} tone="text-emerald-600" />
        <Tile label="Tier A coverage" value={pct(o.tier_a_coverage)} hint="contacted in period" />
        <Tile label="Overdue follow-ups" value={o.overdue_followups} tone={o.overdue_followups ? 'text-rose-600' : ''} hint={`${o.open_followups} open`} />
      </div>
      <div className="grid gap-4 lg:grid-cols-3">
        <div className="card p-5 lg:col-span-2"><h2 className="mb-3 font-semibold">Activity</h2>
          <ResponsiveContainer width="100%" height={230}><AreaChart data={o.series}><defs><linearGradient id="g" x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stopColor="#0f9d8a" stopOpacity={0.35} /><stop offset="100%" stopColor="#0f9d8a" stopOpacity={0} /></linearGradient></defs>
            <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" /><XAxis dataKey="label" fontSize={11} interval="preserveStartEnd" /><YAxis allowDecimals={false} fontSize={11} /><Tooltip /><Area dataKey="count" stroke="#0f9d8a" strokeWidth={2} fill="url(#g)" /></AreaChart></ResponsiveContainer></div>
        <div className="card p-5"><h2 className="mb-3 font-semibold">Sentiment</h2>
          <ResponsiveContainer width="100%" height={230}><PieChart><Pie data={sent} dataKey="value" nameKey="name" innerRadius={50} outerRadius={85}>{sent.map((s) => <Cell key={s.name} fill={SENT[s.name as keyof typeof SENT]} />)}</Pie><Tooltip /></PieChart></ResponsiveContainer></div>
      </div>
      <div className="grid gap-4 lg:grid-cols-3">
        <div className="card p-5 lg:col-span-2">
          <h2 className="mb-3 flex items-center gap-2 font-semibold"><AlertTriangle size={16} className="text-amber-500" />Needs attention</h2>
          {risk.length === 0 && <p className="text-sm text-slate-500">All important doctors are up to date.</p>}
          <ul className="divide-y divide-slate-100">{risk.slice(0, 6).map((r) => (
            <li key={r.hcp_id} className="flex items-start gap-3 py-3"><TierBadge t={r.tier} />
              <div className="min-w-0 flex-1"><Link to={`/hcps/${r.hcp_id}`} className="font-medium hover:underline">{r.name}</Link><div className="text-xs text-slate-500">{r.specialty} · {r.hospital}</div>
                <div className="mt-1 flex gap-1.5 text-xs text-amber-700"><Lightbulb size={12} className="mt-0.5 shrink-0" />{r.suggestion}</div></div>
              <span className="whitespace-nowrap text-xs font-semibold text-rose-600">{r.days_since == null ? 'never' : `${r.days_since}d`}</span></li>))}</ul></div>
        <div className="space-y-4">
          <div className="card p-5"><h2 className="mb-3 font-semibold">Top products</h2>
            <ResponsiveContainer width="100%" height={150}><BarChart data={o.top_products} layout="vertical" margin={{ left: 20 }}><XAxis type="number" hide /><YAxis type="category" dataKey="name" width={90} fontSize={11} /><Tooltip /><Bar dataKey="count" fill="#0f9d8a" radius={[0, 4, 4, 0]} /></BarChart></ResponsiveContainer></div>
          <div className="card p-5"><h2 className="mb-2 font-semibold">Follow-ups</h2>
            {fu.length === 0 && <p className="text-sm text-slate-500">Nothing pending.</p>}
            <ul className="space-y-2">{fu.slice(0, 5).map((f) => (
              <li key={f.id} className="flex items-start gap-2 text-sm"><button onClick={() => done({ id: f.id, done: true })} className="mt-0.5 text-slate-300 hover:text-emerald-500" aria-label="Mark done"><CheckCircle2 size={16} /></button>
                <div className="min-w-0 flex-1"><div className="truncate">{f.title}</div><div className="text-xs text-slate-500">{f.hcp.name}</div></div>
                <span className={`text-xs ${f.overdue ? 'font-semibold text-rose-600' : 'text-slate-400'}`}>{fmtDate(f.due_on)}</span></li>))}</ul></div>
        </div>
      </div>
    </div>
  )
}
