import { Navigate, Route, Routes } from 'react-router-dom'
import { useSelector } from 'react-redux'
import Layout from './components/Layout'
import Assistant from './pages/Assistant'
import Auth from './pages/Auth'
import Dashboard from './pages/Dashboard'
import HCPDetail from './pages/HCPDetail'
import HCPs from './pages/HCPs'
import Interactions from './pages/Interactions'
import Team from './pages/Team'
import type { RootState } from './store'
import { useMeQuery } from './store/api'

function Protected({ manager = false }: { manager?: boolean }) {
  const token = useSelector((s: RootState) => s.auth.access)
  const { data: user, isLoading } = useMeQuery(undefined, { skip: !token })
  if (!token) return <Navigate to="/login" replace />
  if (isLoading || !user) return <p className="p-8 text-slate-500">Loading…</p>
  if (manager && user.role !== 'manager') return <Navigate to="/" replace />
  return <Layout user={user} />
}

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<Auth mode="login" />} />
      <Route path="/signup" element={<Auth mode="signup" />} />
      <Route element={<Protected />}>
        <Route index element={<Dashboard />} />
        <Route path="hcps" element={<HCPs />} />
        <Route path="hcps/:id" element={<HCPDetail />} />
        <Route path="interactions" element={<Interactions />} />
        <Route path="assistant" element={<Assistant />} />
      </Route>
      <Route element={<Protected manager />}><Route path="team" element={<Team />} /></Route>
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}
