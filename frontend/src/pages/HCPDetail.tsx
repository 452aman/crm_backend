import { ArrowLeft, Plus } from 'lucide-react'
import { useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { Bar, BarChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import LogModal from '../components/LogModal'
import { SentimentBadge, TierBadge, fmtDate } from '../components/ui'
import { useHcpQuery } from '../store/api'

export default function HCPDetail() {
  const { id } = useParams()
  const { data } = useHcpQuery(Number(id))
  const [open, setOpen] = useState(false)
  if (!data) return <p className="text-slate-400">Loading…</p>
  const { hcp: h } = data
  return (
    <div className="space-y-5">
      <Link to="/hcps" className="flex items-center gap-1 text-sm text-slate-400 hover:text-slate-100"><ArrowLeft size={14} />All doctors</Link>
      <div className="card flex flex-wrap items-center gap-4 p-5">
        <TierBadge t={h.tier} /><div className="min-w-0 flex-1"><h1 className="text-xl font-bold">{h.name}</h1><p className="text-sm text-slate-400">{h.specialty} · {h.hospital}, {h.city}</p></div>
        <div className="text-right text-sm"><div className="text-slate-400">Last contact</div><div className="font-semibold">{fmtDate(h.last_contact)}</div></div>
        <button className="btn" onClick={() => setOpen(true)}><Plus size={16} />Log interaction</button>
      </div>
      <div className="grid gap-5 lg:grid-cols-3">
        <div className="space-y-3 lg:col-span-2"><h2 className="font-semibold">Timeline</h2>
          {data.timeline.length === 0 && <p className="card p-8 text-center text-slate-400">No interactions yet.</p>}
          <ol className="relative space-y-3 border-l-2 border-white/10 pl-5">{data.timeline.map((i) => (
            <li key={i.id} className="relative"><span className="absolute -left-[27px] top-4 h-3 w-3 rounded-full border-2 border-white/20 bg-brand" />
              <div className="card p-4"><div className="flex flex-wrap items-center gap-2"><SentimentBadge s={i.sentiment} /><span className="rounded bg-white/[0.07] px-2 py-0.5 text-xs">{i.type.replace('_', ' ')}</span><span className="ml-auto text-xs text-slate-400">{fmtDate(i.occurred_on)} · {i.rep.name}</span></div>
                <p className="mt-2 text-sm text-slate-300">{i.notes}</p>{i.products.length > 0 && <div className="mt-2 flex gap-1.5">{i.products.map((p) => <span key={p.id} className="rounded-full bg-teal-400/10 px-2 py-0.5 text-xs text-brand-dark">{p.name}</span>)}</div>}</div></li>))}</ol></div>
        <div className="space-y-4">
          <div className="card p-5"><h2 className="mb-2 font-semibold">Sentiment</h2><div className="flex gap-2">{(['positive', 'neutral', 'negative'] as const).map((s) => <div key={s} className="flex-1 rounded-lg bg-white/[0.04] p-3 text-center"><div className="text-xl font-bold">{data.sentiment[s] ?? 0}</div><div className="text-xs text-slate-400">{s}</div></div>)}</div></div>
          <div className="card p-5"><h2 className="mb-2 font-semibold">Products discussed</h2>{data.products.length === 0 ? <p className="text-sm text-slate-400">None yet.</p> :
            <ResponsiveContainer width="100%" height={Math.max(90, data.products.length * 34)}><BarChart data={data.products} layout="vertical" margin={{ left: 20 }}><XAxis type="number" hide /><YAxis type="category" dataKey="name" width={90} fontSize={11} /><Tooltip /><Bar dataKey="count" fill="#0f9d8a" radius={[0, 4, 4, 0]} /></BarChart></ResponsiveContainer>}</div>
          <div className="card p-5"><h2 className="mb-2 font-semibold">Open follow-ups</h2>{data.followups.length === 0 ? <p className="text-sm text-slate-400">None.</p> : <ul className="space-y-1.5 text-sm">{data.followups.map((f) => <li key={f.id} className="flex justify-between"><span>{f.title}</span><span className={f.overdue ? 'font-semibold text-rose-400' : 'text-slate-500'}>{fmtDate(f.due_on)}</span></li>)}</ul>}</div>
        </div>
      </div>
      {open && <LogModal hcpId={h.id} onClose={() => setOpen(false)} />}
    </div>
  )
}
