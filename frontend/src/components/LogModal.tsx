import { Sparkles, X } from 'lucide-react'
import { useState } from 'react'
import { useCreateInteractionMutation, useHcpsQuery, useParseNoteMutation, useProductsQuery } from '../store/api'
import { INTERACTION_TYPES, type ITypeName, type Parsed, type Sentiment } from '../types'

interface Draft { hcp_id: number | ''; type: ITypeName; occurred_on: string; location: string; notes: string; sentiment: Sentiment; next_steps: string; product_ids: number[]; follow_up_days: number | ''; source: string }
const blank = (hcp?: number): Draft => ({ hcp_id: hcp ?? '', type: 'visit', occurred_on: new Date().toISOString().slice(0, 10), location: '', notes: '', sentiment: 'neutral', next_steps: '', product_ids: [], follow_up_days: '', source: 'form' })
const errText = (e: unknown) => ((e as { data?: { detail?: string } })?.data?.detail) ?? 'Could not save'

export default function LogModal({ onClose, hcpId }: { onClose: () => void; hcpId?: number }) {
  const [mode, setMode] = useState<'quick' | 'form'>(hcpId ? 'form' : 'quick')
  const [text, setText] = useState('')
  const [d, setD] = useState<Draft>(blank(hcpId))
  const [parsedInfo, setParsedInfo] = useState<Parsed | null>(null)
  const { data: hcps } = useHcpsQuery({ size: 100 })
  const { data: products = [] } = useProductsQuery()
  const [parse, { isLoading: parsing }] = useParseNoteMutation()
  const [create, { isLoading: saving, error }] = useCreateInteractionMutation()

  const runParse = async () => {
    const p = await parse(text).unwrap()
    setParsedInfo(p)
    setD({ hcp_id: p.hcp_id ?? '', type: p.type, occurred_on: p.occurred_on, location: p.location, notes: p.notes, sentiment: p.sentiment, next_steps: p.next_steps, product_ids: p.product_ids, follow_up_days: p.follow_up_days ?? '', source: 'quick_log' })
    setMode('form')
  }
  const save = async () => {
    await create({ ...d, hcp_id: d.hcp_id, follow_up_days: d.follow_up_days || null }).unwrap()
    onClose()
  }
  const set = <K extends keyof Draft>(k: K, v: Draft[K]) => setD({ ...d, [k]: v })
  const toggleProduct = (id: number) => set('product_ids', d.product_ids.includes(id) ? d.product_ids.filter((x) => x !== id) : [...d.product_ids, id])

  return (
    <div className="fixed inset-0 z-50 flex items-start justify-center overflow-y-auto bg-slate-900/50 p-4 pt-12" onClick={onClose}>
      <div className="card w-full max-w-2xl space-y-4 p-6" onClick={(e) => e.stopPropagation()}>
        <div className="flex items-center justify-between"><h2 className="text-lg font-semibold">Log interaction</h2><button onClick={onClose} aria-label="Close"><X size={18} /></button></div>
        <div className="inline-flex rounded-lg bg-slate-100 p-1 text-sm">
          <button onClick={() => setMode('quick')} className={`flex items-center gap-1 rounded-md px-3 py-1.5 font-medium ${mode === 'quick' ? 'bg-white shadow-sm' : 'text-slate-500'}`}><Sparkles size={14} />Quick log (AI)</button>
          <button onClick={() => setMode('form')} className={`rounded-md px-3 py-1.5 font-medium ${mode === 'form' ? 'bg-white shadow-sm' : 'text-slate-500'}`}>Form</button>
        </div>
        {mode === 'quick' ? (
          <div className="space-y-3">
            <p className="text-sm text-slate-500">Describe the meeting in your own words. The AI fills in the form, and you review it before anything is saved.</p>
            <textarea className="input" rows={5} value={text} onChange={(e) => setText(e.target.value)} placeholder="Met Dr. Verma at Lakeview this morning. She was positive about CardioMax and asked for the trial data. Follow up in 2 weeks." />
            <button className="btn" disabled={text.trim().length < 10 || parsing} onClick={runParse}>{parsing ? 'Reading…' : 'Parse note'}</button>
          </div>
        ) : (
          <div className="space-y-3">
            {parsedInfo && <p className={`rounded-lg px-3 py-2 text-xs ${parsedInfo.used_llm ? 'bg-teal-50 text-teal-800' : 'bg-amber-50 text-amber-800'}`}>{parsedInfo.used_llm ? 'Filled in by AI. Check each field.' : 'Filled in by simple rules (no AI key). Check each field.'}{!parsedInfo.hcp_id && parsedInfo.doctor_name && ` Could not match "${parsedInfo.doctor_name}", please pick the doctor.`}</p>}
            <div className="grid gap-3 sm:grid-cols-2">
              <div className="sm:col-span-2"><label className="label">Doctor</label><select className="input" value={d.hcp_id} onChange={(e) => set('hcp_id', +e.target.value)}><option value="">Select…</option>{hcps?.items.map((h) => <option key={h.id} value={h.id}>{h.name}, {h.hospital}</option>)}</select></div>
              <div><label className="label">Type</label><select className="input" value={d.type} onChange={(e) => set('type', e.target.value as ITypeName)}>{INTERACTION_TYPES.map((t) => <option key={t} value={t}>{t.replace('_', ' ')}</option>)}</select></div>
              <div><label className="label">Date</label><input type="date" className="input" value={d.occurred_on} onChange={(e) => set('occurred_on', e.target.value)} /></div>
              <div><label className="label">Sentiment</label><select className="input" value={d.sentiment} onChange={(e) => set('sentiment', e.target.value as Sentiment)}>{['positive', 'neutral', 'negative'].map((s) => <option key={s}>{s}</option>)}</select></div>
              <div><label className="label">Location</label><input className="input" value={d.location} onChange={(e) => set('location', e.target.value)} /></div>
            </div>
            <div><label className="label">Products discussed</label><div className="flex flex-wrap gap-1.5">{products.map((p) => <button type="button" key={p.id} onClick={() => toggleProduct(p.id)} className={`rounded-full border px-3 py-1 text-xs ${d.product_ids.includes(p.id) ? 'border-brand bg-teal-50 font-medium text-brand-dark' : 'border-slate-300 text-slate-600'}`}>{p.name}</button>)}</div></div>
            <div><label className="label">Notes</label><textarea className="input" rows={3} value={d.notes} onChange={(e) => set('notes', e.target.value)} /></div>
            <div className="grid gap-3 sm:grid-cols-3"><div className="sm:col-span-2"><label className="label">Next steps</label><input className="input" value={d.next_steps} onChange={(e) => set('next_steps', e.target.value)} /></div>
              <div><label className="label">Follow up in (days)</label><input type="number" min={1} className="input" value={d.follow_up_days} onChange={(e) => set('follow_up_days', e.target.value ? +e.target.value : '')} /></div></div>
            {error && <p className="rounded-lg bg-rose-50 px-3 py-2 text-sm text-rose-700">{errText(error)}</p>}
            <button className="btn" disabled={!d.hcp_id || saving} onClick={save}>{saving ? 'Saving…' : 'Save interaction'}</button>
          </div>
        )}
      </div>
    </div>
  )
}
