import { Download, Plus, Trash2 } from 'lucide-react'
import { useState } from 'react'
import { useSelector } from 'react-redux'
import { Link } from 'react-router-dom'
import LogModal from '../components/LogModal'
import { SentimentBadge, fmtDate } from '../components/ui'
import type { RootState } from '../store'
import { useDeleteInteractionMutation, useInteractionsQuery, useMeQuery } from '../store/api'
import { INTERACTION_TYPES } from '../types'

export default function Interactions() {
  const [f, setF] = useState({ type: '', sentiment: '', q: '' })
  const [page, setPage] = useState(1)
  const [open, setOpen] = useState(false)
  const token = useSelector((s: RootState) => s.auth.access)
  const { data: me } = useMeQuery()
  const { data } = useInteractionsQuery({ type: f.type || undefined, sentiment: f.sentiment || undefined, q: f.q || undefined, page, size: 12 })
  const [del] = useDeleteInteractionMutation()
  const pages = data ? Math.max(1, Math.ceil(data.total / data.size)) : 1
  const exportCsv = async () => {
    const r = await fetch('/api/v1/interactions/export.csv', { headers: { Authorization: `Bearer ${token}` } })
    const url = URL.createObjectURL(await r.blob())
    Object.assign(document.createElement('a'), { href: url, download: 'interactions.csv' }).click()
    URL.revokeObjectURL(url)
  }
  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-3"><h1 className="text-2xl font-bold">Interactions</h1>
        <div className="flex gap-2"><button className="btn-ghost" onClick={exportCsv}><Download size={14} />Export CSV</button><button className="btn" onClick={() => setOpen(true)}><Plus size={16} />Log interaction</button></div></div>
      <div className="card grid gap-3 p-4 sm:grid-cols-3">
        <input className="input" placeholder="Search notes…" value={f.q} onChange={(e) => { setF({ ...f, q: e.target.value }); setPage(1) }} />
        <select className="input" value={f.type} onChange={(e) => { setF({ ...f, type: e.target.value }); setPage(1) }}><option value="">All types</option>{INTERACTION_TYPES.map((t) => <option key={t} value={t}>{t.replace('_', ' ')}</option>)}</select>
        <select className="input" value={f.sentiment} onChange={(e) => { setF({ ...f, sentiment: e.target.value }); setPage(1) }}><option value="">Any sentiment</option>{['positive', 'neutral', 'negative'].map((s) => <option key={s}>{s}</option>)}</select>
      </div>
      <div className="space-y-3">{data?.items.map((i) => (
        <div key={i.id} className="card p-4">
          <div className="flex flex-wrap items-center gap-2"><Link to={`/hcps/${i.hcp.id}`} className="font-semibold hover:underline">{i.hcp.name}</Link><SentimentBadge s={i.sentiment} />
            <span className="rounded bg-slate-100 px-2 py-0.5 text-xs">{i.type.replace('_', ' ')}</span>{i.source !== 'form' && <span className="rounded bg-violet-50 px-2 py-0.5 text-xs text-violet-700">{i.source.replace('_', ' ')}</span>}
            <span className="ml-auto text-xs text-slate-500">{fmtDate(i.occurred_on)}{me?.role === 'manager' && ` · ${i.rep.name}`}</span>
            {(me?.id === i.rep.id) && <button className="text-slate-300 hover:text-rose-500" onClick={() => confirm('Delete this interaction?') && del(i.id)} aria-label="Delete"><Trash2 size={14} /></button>}</div>
          <p className="mt-2 text-sm text-slate-600">{i.notes}</p>
          {(i.products.length > 0 || i.next_steps) && <div className="mt-2 flex flex-wrap items-center gap-1.5 text-xs">{i.products.map((p) => <span key={p.id} className="rounded-full bg-teal-50 px-2 py-0.5 text-brand-dark">{p.name}</span>)}{i.next_steps && <span className="text-slate-500">Next: {i.next_steps}</span>}</div>}
        </div>))}
        {data && data.total === 0 && <p className="card p-10 text-center text-slate-500">No interactions yet.</p>}
      </div>
      <div className="flex items-center justify-center gap-3 text-sm"><button className="btn-ghost" disabled={page <= 1} onClick={() => setPage(page - 1)}>Previous</button><span className="text-slate-500">Page {page} of {pages}</span><button className="btn-ghost" disabled={page >= pages} onClick={() => setPage(page + 1)}>Next</button></div>
      {open && <LogModal onClose={() => setOpen(false)} />}
    </div>
  )
}
