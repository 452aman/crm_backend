import { Bot, Check, ChevronDown, Send, Trash2, Wrench, X } from 'lucide-react'
import { Fragment, useEffect, useRef, useState } from 'react'
import { useSelector } from 'react-redux'
import type { RootState } from '../store'
import { api, useCancelActionMutation, useChatHistoryQuery, useClearChatMutation, useConfirmActionMutation } from '../store/api'
import { useDispatch } from 'react-redux'
import Markdown from '../components/Markdown'
import type { Action, ChatMsg, TraceEv } from '../types'

const SUGGEST = ["Which important doctors haven't I seen in a while?", 'What follow-ups are overdue?', 'Show my history with Dr. Verma', "I met Dr. Rao today at Greenfield. He was keen on CardioMax. Follow up in a week."]
const KIND: Record<string, string> = { log_interaction: 'Log interaction', edit_interaction: 'Edit interaction', create_followup: 'Create follow-up' }

function ActionCard({ a }: { a: Action }) {
  const [confirm, { isLoading: c1, error }] = useConfirmActionMutation()
  const [cancel, { isLoading: c2 }] = useCancelActionMutation()
  const p = a.payload as Record<string, unknown>
  const rows: [string, string][] = [['Doctor', String(p.hcp_name ?? '')], ['Type', String(p.type ?? '')], ['Sentiment', String(p.sentiment ?? '')],
    ['Products', ((p.product_names as string[]) ?? []).join(', ')], ['Notes', String(p.notes ?? p.title ?? '')], ['Next steps', String(p.next_steps ?? '')],
    ['Follow-up', p.follow_up_days ? `in ${p.follow_up_days} days` : p.due_in_days ? `in ${p.due_in_days} days` : '']].filter(([, v]) => v) as [string, string][]
  return (
    <div className={`mt-3 rounded-xl border p-4 ${a.status === 'pending' ? 'border-amber-400/40 bg-amber-400/10' : a.status === 'confirmed' ? 'border-emerald-400/40 bg-emerald-400/10' : 'border-white/10 bg-white/[0.04] opacity-70'}`}>
      <div className="mb-2 flex items-center justify-between text-sm font-semibold"><span>{KIND[a.kind] ?? a.kind}</span><span className="text-xs font-medium uppercase">{a.status === 'pending' ? 'Awaiting your confirmation' : a.status}</span></div>
      <dl className="grid grid-cols-[90px_1fr] gap-x-3 gap-y-1 text-sm">{rows.map(([k, v]) => <Fragment key={k}><dt className="text-slate-400">{k}</dt><dd>{v}</dd></Fragment>)}</dl>
      {a.status === 'pending' && <div className="mt-3 flex gap-2"><button className="btn" disabled={c1 || c2} onClick={() => confirm(a.id)}><Check size={14} />Confirm and save</button><button className="btn-ghost" disabled={c1 || c2} onClick={() => cancel(a.id)}><X size={14} />Discard</button></div>}
      {error && <p className="mt-2 text-sm text-rose-400">{((error as { data?: { detail?: string } }).data?.detail) ?? 'Failed'}</p>}
      {a.status === 'confirmed' && <p className="mt-2 text-sm text-emerald-300">{String((a.result as { message?: string }).message ?? 'Saved.')}</p>}
    </div>
  )
}

function Trace({ trace }: { trace: TraceEv[] }) {
  const [open, setOpen] = useState(false)
  const calls = trace.filter((t) => t.type === 'tool_call')
  if (!calls.length) return null
  return (
    <div className="mb-2 text-xs">
      <button onClick={() => setOpen(!open)} className="flex items-center gap-1 rounded-full bg-white/[0.07] px-2.5 py-1 text-slate-300"><Wrench size={11} />{calls.map((c) => c.name).join(' → ')}<ChevronDown size={11} className={open ? 'rotate-180' : ''} /></button>
      {open && <div className="mt-1 space-y-1 rounded-lg bg-black/50 p-3 font-mono text-[11px] text-emerald-300">{trace.map((t, i) => <div key={i}>{t.type === 'tool_call' ? `> ${t.name}(${JSON.stringify(t.args)})` : `< ${t.content}`}</div>)}</div>}
    </div>
  )
}

export default function Assistant() {
  const token = useSelector((s: RootState) => s.auth.access)
  const dispatch = useDispatch()
  const { data: hist } = useChatHistoryQuery()
  const [clearChat] = useClearChatMutation()
  const [msgs, setMsgs] = useState<ChatMsg[]>([])
  const [input, setInput] = useState('')
  const [busy, setBusy] = useState(false)
  const bottom = useRef<HTMLDivElement>(null)
  const loaded = useRef(false)
  useEffect(() => { if (hist && !loaded.current) { loaded.current = true; setMsgs(hist.map((m) => ({ ...m, trace: m.trace as unknown as TraceEv[] }))) } }, [hist])
  useEffect(() => { bottom.current?.scrollIntoView({ behavior: 'smooth' }) }, [msgs])

  const send = async (text: string) => {
    if (!text.trim() || busy) return
    setBusy(true); setInput('')
    setMsgs((m) => [...m, { role: 'user', content: text }, { role: 'assistant', content: '', trace: [], actions: [], streaming: true }])
    const patch = (fn: (m: ChatMsg) => ChatMsg) => setMsgs((all) => all.map((m, i) => (i === all.length - 1 ? fn(m) : m)))
    try {
      const res = await fetch('/api/v1/chat', { method: 'POST', headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` }, body: JSON.stringify({ message: text }) })
      if (!res.ok || !res.body) throw new Error((await res.json().catch(() => ({}))).detail ?? `HTTP ${res.status}`)
      const reader = res.body.getReader(); const dec = new TextDecoder(); let buf = ''
      for (;;) {
        const { done, value } = await reader.read(); if (done) break
        buf += dec.decode(value, { stream: true })
        const parts = buf.split('\n\n'); buf = parts.pop() ?? ''
        for (const part of parts) {
          if (!part.startsWith('data: ')) continue
          const ev = JSON.parse(part.slice(6))
          if (ev.type === 'token') patch((m) => ({ ...m, content: m.content + ev.text }))
          else if (ev.type === 'tool_call' || ev.type === 'tool_result') patch((m) => ({ ...m, trace: [...(m.trace ?? []), ev] }))
          else if (ev.type === 'actions') patch((m) => ({ ...m, actions: ev.actions }))
          else if (ev.type === 'error') patch((m) => ({ ...m, error: ev.message }))
        }
      }
    } catch (e) { patch((m) => ({ ...m, error: (e as Error).message })) }
    patch((m) => ({ ...m, streaming: false }))
    setBusy(false)
    dispatch(api.util.invalidateTags(['Chat']))
  }

  // Action cards live in the server cache, so a confirmed/cancelled status shows after the refetch.
  const latest = (a: Action) => hist?.flatMap((h) => h.actions).find((x) => x.id === a.id) ?? a
  return (
    <div className="mx-auto flex h-[calc(100vh-130px)] min-h-[520px] max-w-3xl flex-col card">
      <div className="flex items-center justify-between border-b border-white/10 px-5 py-3"><div className="flex items-center gap-2 font-semibold"><Bot className="text-brand" size={18} />CRM Assistant</div>
        <button className="btn-ghost" onClick={async () => { await clearChat(); setMsgs([]) }}><Trash2 size={13} />Clear</button></div>
      <div className="flex-1 space-y-5 overflow-y-auto p-5">
        {msgs.length === 0 && <div className="mx-auto max-w-md space-y-2 pt-6 text-center"><p className="text-sm text-slate-400">Ask about your accounts, or describe a meeting and I'll draft the log for you to confirm. I never save anything without your approval.</p>
          <div className="grid gap-2 pt-2">{SUGGEST.map((s) => <button key={s} onClick={() => send(s)} className="rounded-lg border border-white/10 px-3 py-2 text-left text-sm hover:bg-white/[0.07]">{s}</button>)}</div></div>}
        {msgs.map((m, i) => m.role === 'user'
          ? <div key={i} className="ml-auto max-w-[80%] rounded-2xl rounded-br-sm bg-gradient-to-br from-brand to-emerald-400 px-4 py-2.5 text-sm font-medium text-slate-900">{m.content}</div>
          : <div key={i} className="max-w-[92%] text-sm"><Trace trace={m.trace ?? []} />
              <div className="leading-relaxed"><Markdown text={m.content} />{m.streaming && <span className="ml-0.5 inline-block h-4 w-1.5 animate-pulse bg-brand align-middle" />}</div>
              {m.error && <p className="mt-2 rounded-lg bg-rose-400/10 px-3 py-2 text-rose-300">{m.error}</p>}
              {(m.actions ?? []).map((a) => <ActionCard key={a.id} a={latest(a)} />)}</div>)}
        <div ref={bottom} />
      </div>
      <form className="flex gap-2 border-t border-white/10 p-3" onSubmit={(e) => { e.preventDefault(); send(input) }}>
        <input className="input" placeholder="Ask or describe a meeting…" value={input} onChange={(e) => setInput(e.target.value)} disabled={busy} />
        <button className="btn" disabled={busy || !input.trim()}><Send size={16} /></button></form>
    </div>
  )
}
