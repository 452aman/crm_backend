import { Search } from 'lucide-react'
import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { TierBadge, fmtDate } from '../components/ui'
import { useHcpsQuery, useSpecialtiesQuery } from '../store/api'

export default function HCPs() {
  const [f, setF] = useState({ q: '', tier: '', specialty: '', mine: false })
  const [dq, setDq] = useState('')
  const [page, setPage] = useState(1)
  useEffect(() => { const t = setTimeout(() => { setDq(f.q); setPage(1) }, 300); return () => clearTimeout(t) }, [f.q])
  const { data: specs = [] } = useSpecialtiesQuery()
  const { data, isFetching } = useHcpsQuery({ q: dq || undefined, tier: f.tier || undefined, specialty: f.specialty || undefined, mine: f.mine || undefined, page, size: 12 })
  const pages = data ? Math.max(1, Math.ceil(data.total / data.size)) : 1
  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-bold">Doctors</h1>
      <div className="card grid gap-3 p-4 sm:grid-cols-2 lg:grid-cols-5">
        <div className="relative lg:col-span-2"><Search size={16} className="absolute left-3 top-2.5 text-slate-500" /><input className="input pl-9" placeholder="Search name, hospital, city" value={f.q} onChange={(e) => setF({ ...f, q: e.target.value })} /></div>
        <select className="input" value={f.tier} onChange={(e) => { setF({ ...f, tier: e.target.value }); setPage(1) }}><option value="">All tiers</option>{['A', 'B', 'C'].map((t) => <option key={t}>{t}</option>)}</select>
        <select className="input" value={f.specialty} onChange={(e) => { setF({ ...f, specialty: e.target.value }); setPage(1) }}><option value="">All specialties</option>{specs.map((s) => <option key={s}>{s}</option>)}</select>
        <label className="flex items-center gap-2 text-sm"><input type="checkbox" checked={f.mine} onChange={(e) => { setF({ ...f, mine: e.target.checked }); setPage(1) }} />My accounts only</label>
      </div>
      <div className="card overflow-x-auto"><table className="w-full text-left text-sm">
        <thead className="border-b border-white/10 text-xs uppercase text-slate-400"><tr><th className="p-3">Tier</th><th>Doctor</th><th>Specialty</th><th>Hospital</th><th>Last contact</th><th>Touches</th></tr></thead>
        <tbody className="divide-y divide-white/10">{data?.items.map((h) => (
          <tr key={h.id} className="hover:bg-white/[0.07]"><td className="p-3"><TierBadge t={h.tier} /></td><td><Link to={`/hcps/${h.id}`} className="font-medium text-brand-dark hover:underline">{h.name}</Link></td>
            <td>{h.specialty}</td><td className="text-slate-400">{h.hospital}, {h.city}</td><td>{fmtDate(h.last_contact)}</td><td>{h.interaction_count}</td></tr>))}</tbody></table>
        {data && data.total === 0 && <p className="p-8 text-center text-slate-400">No doctors match.</p>}</div>
      <div className="flex items-center justify-center gap-3 text-sm"><button className="btn-ghost" disabled={page <= 1} onClick={() => setPage(page - 1)}>Previous</button>
        <span className="text-slate-400">Page {page} of {pages} {isFetching && '· loading'}</span><button className="btn-ghost" disabled={page >= pages} onClick={() => setPage(page + 1)}>Next</button></div>
    </div>
  )
}
