import { Bot, ClipboardList, LayoutDashboard, LogOut, Stethoscope, Users } from 'lucide-react'
import { useDispatch } from 'react-redux'
import { NavLink, Outlet } from 'react-router-dom'
import { api } from '../store/api'
import { clear } from '../store/auth'
import type { User } from '../types'

const cls = ({ isActive }: { isActive: boolean }) =>
  `flex items-center gap-2 rounded-lg px-3 py-2 text-sm font-medium ${isActive ? 'bg-white/15 text-white' : 'text-teal-100 hover:bg-white/10'}`

export default function Layout({ user }: { user: User }) {
  const dispatch = useDispatch()
  const logout = () => { dispatch(clear()); dispatch(api.util.resetApiState()) }
  return (
    <div className="min-h-screen">
      <header className="bg-ink">
        <div className="mx-auto flex max-w-7xl flex-wrap items-center gap-5 px-4 py-3">
          <div className="flex items-center gap-2 text-lg font-semibold text-white"><Stethoscope className="text-brand" />AI-First CRM</div>
          <nav className="flex flex-wrap gap-1">
            <NavLink to="/" end className={cls}><LayoutDashboard size={16} />Dashboard</NavLink>
            <NavLink to="/hcps" className={cls}><Users size={16} />Doctors</NavLink>
            <NavLink to="/interactions" className={cls}><ClipboardList size={16} />Interactions</NavLink>
            <NavLink to="/assistant" className={cls}><Bot size={16} />Assistant</NavLink>
            {user.role === 'manager' && <NavLink to="/team" className={cls}><Users size={16} />Team</NavLink>}
          </nav>
          <div className="ml-auto flex items-center gap-3 text-sm text-teal-100">
            <span>{user.name} <span className="rounded bg-white/10 px-1.5 py-0.5 text-xs">{user.role}</span></span>
            <button onClick={logout} className="rounded-lg p-2 hover:bg-white/10" aria-label="Log out"><LogOut size={16} /></button>
          </div>
        </div>
      </header>
      <main className="mx-auto max-w-7xl px-4 py-6"><Outlet /></main>
    </div>
  )
}
