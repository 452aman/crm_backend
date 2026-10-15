import Logo from '../components/Logo'
import { useState, type FormEvent } from 'react'
import { useDispatch, useSelector } from 'react-redux'
import { Link, Navigate } from 'react-router-dom'
import type { RootState } from '../store'
import { useLoginMutation, useSignupMutation } from '../store/api'
import { setTokens } from '../store/auth'

const msg = (e: unknown) => ((e as { data?: { detail?: string } })?.data?.detail) ?? 'Something went wrong'

export default function Auth({ mode }: { mode: 'login' | 'signup' }) {
  const dispatch = useDispatch()
  const token = useSelector((s: RootState) => s.auth.access)
  const [login, { isLoading: l1 }] = useLoginMutation()
  const [signup, { isLoading: l2 }] = useSignupMutation()
  const [f, setF] = useState({ name: '', email: '', password: '', role: 'rep' })
  const [error, setError] = useState('')
  if (token) return <Navigate to="/" replace />
  const set = (k: keyof typeof f) => (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => setF({ ...f, [k]: e.target.value })

  const submit = async (e: FormEvent) => {
    e.preventDefault(); setError('')
    try {
      if (mode === 'signup') await signup(f).unwrap()
      const t = await login({ email: f.email, password: f.password }).unwrap()
      dispatch(setTokens({ access: t.access_token, refresh: t.refresh_token }))
    } catch (err) { setError(msg(err)) }
  }
  return (
    <div className="flex min-h-screen items-center justify-center bg-transparent px-4">
      <form onSubmit={submit} className="card w-full max-w-sm space-y-4 p-8">
        <div className="flex items-center gap-2 text-xl font-bold text-brand-dark"><Logo className="h-8 w-8" />AI-First CRM</div>
        <p className="text-sm text-slate-400">{mode === 'login' ? 'Sign in to log and review HCP interactions.' : 'Create your account.'}</p>
        {mode === 'signup' && <>
          <div><label className="label">Name</label><input className="input" required minLength={2} value={f.name} onChange={set('name')} /></div>
          <div><label className="label">Role</label><select className="input" value={f.role} onChange={set('role')}><option value="rep">Field rep</option><option value="manager">Manager</option></select></div></>}
        <div><label className="label">Email</label><input className="input" type="email" required value={f.email} onChange={set('email')} /></div>
        <div><label className="label">Password</label><input className="input" type="password" required minLength={mode === 'signup' ? 8 : 1} value={f.password} onChange={set('password')} /></div>
        {error && <p className="rounded-lg bg-rose-400/10 px-3 py-2 text-sm text-rose-300">{error}</p>}
        <button className="btn w-full" disabled={l1 || l2}>{mode === 'login' ? 'Sign in' : 'Create account'}</button>
        <p className="text-center text-sm text-slate-400">{mode === 'login' ? <>New here? <Link className="text-brand-dark hover:underline" to="/signup">Sign up</Link></> : <>Have an account? <Link className="text-brand-dark hover:underline" to="/login">Sign in</Link></>}</p>
        {mode === 'login' && <p className="rounded-lg bg-white/[0.04] p-2 text-center text-xs text-slate-400">Demo: rep1@crm.dev / rep12345 · manager@crm.dev / manager123</p>}
      </form>
    </div>
  )
}
