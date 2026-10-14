import { useState } from 'react'
import { Bar, BarChart, CartesianGrid, Legend, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import { pct } from '../components/ui'
import { useAtRiskQuery, useTeamQuery } from '../store/api'

export default function Team() {
  const [days, setDays] = useState(30)
  const { data: team = [] } = useTeamQuery(days)
  const { data: risk = [] } = useAtRiskQuery()
  return (
    <div className="space-y-5">
      <div className="flex items-center justify-between"><h1 className="text-2xl font-bold">Team performance</h1>
        <div className="inline-flex rounded-lg bg-slate-200/70 p-1 text-sm">{[7, 30, 90].map((d) => <button key={d} onClick={() => setDays(d)} className={`rounded-md px-3 py-1 font-medium ${days === d ? 'bg-white shadow-sm' : 'text-slate-500'}`}>{d}d</button>)}</div></div>
      <div className="card p-5"><ResponsiveContainer width="100%" height={260}><BarChart data={team}><CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" /><XAxis dataKey="name" fontSize={12} /><YAxis allowDecimals={false} fontSize={12} /><Tooltip /><Legend />
        <Bar dataKey="interactions" fill="#0f9d8a" radius={[4, 4, 0, 0]} /><Bar dataKey="unique_hcps" name="doctors reached" fill="#6366f1" radius={[4, 4, 0, 0]} /><Bar dataKey="at_risk_hcps" name="at-risk doctors" fill="#f59e0b" radius={[4, 4, 0, 0]} /></BarChart></ResponsiveContainer></div>
      <div className="card overflow-x-auto"><table className="w-full text-left text-sm"><thead className="border-b border-slate-100 text-xs uppercase text-slate-500"><tr><th className="p-3">Rep</th><th>Interactions</th><th>Doctors reached</th><th>Positive rate</th><th>Overdue follow-ups</th><th>At-risk doctors</th></tr></thead>
        <tbody className="divide-y divide-slate-100">{team.map((t) => <tr key={t.rep_id}><td className="p-3 font-medium">{t.name}</td><td>{t.interactions}</td><td>{t.unique_hcps}</td><td>{pct(t.positive_rate)}</td><td className={t.overdue_followups ? 'text-rose-600' : ''}>{t.overdue_followups}</td><td>{t.at_risk_hcps}</td></tr>)}</tbody></table></div>
      <div className="card p-5"><h2 className="mb-2 font-semibold">Neglected important accounts (whole team)</h2><ul className="grid gap-2 sm:grid-cols-2">{risk.map((r) => <li key={r.hcp_id} className="rounded-lg bg-amber-50 p-3 text-sm"><b>{r.name}</b> <span className="text-xs text-slate-500">Tier {r.tier} · {r.hospital}</span><div className="text-xs text-amber-800">{r.days_since == null ? 'Never contacted' : `${r.days_since} days since last contact`}</div></li>)}</ul></div>
    </div>
  )
}
