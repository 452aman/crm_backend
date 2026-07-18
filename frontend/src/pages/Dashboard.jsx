import { useState } from 'react'
import { useDispatch, useSelector } from 'react-redux'
import { useNavigate } from 'react-router-dom'
import { logout } from '../store/authSlice'
import LogInteractionForm from '../components/LogInteractionForm'
import ChatInterface from '../components/ChatInterface'

export default function Dashboard() {
  const dispatch = useDispatch()
  const navigate = useNavigate()
  const user = useSelector((state) => state.auth.user)
  const [activeTab, setActiveTab] = useState('log')

  const handleLogout = () => {
    dispatch(logout())
    navigate('/login')
  }

  return (
    <div className="dashboard">
      {/* Header */}
      <header className="dashboard-header">
        <div className="header-brand">
          <div className="header-logo-icon">Rx</div>
          <span className="header-logo-text">PharmaConnect CRM</span>
        </div>
        <div className="header-right">
          {user?.email && (
            <span className="header-user">{user.email}</span>
          )}
          <button className="btn-logout" onClick={handleLogout}>
            Log out
          </button>
        </div>
      </header>

      {/* Main Content */}
      <main className="dashboard-main">
        <div className="dashboard-container">
          {/* Tab Bar */}
          <div className="tab-bar">
            <button
              className={`tab-btn ${activeTab === 'log' ? 'tab-btn--active' : ''}`}
              onClick={() => setActiveTab('log')}
            >
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
                <polyline points="14 2 14 8 20 8" />
                <line x1="12" y1="18" x2="12" y2="12" />
                <line x1="9" y1="15" x2="15" y2="15" />
              </svg>
              Log Interaction
            </button>
            <button
              className={`tab-btn ${activeTab === 'chat' ? 'tab-btn--active' : ''}`}
              onClick={() => setActiveTab('chat')}
            >
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
              </svg>
              AI Chat
            </button>
          </div>

          {/* Tab Content */}
          <div className="tab-content">
            {activeTab === 'log' && <LogInteractionForm />}
            {activeTab === 'chat' && <ChatInterface />}
          </div>
        </div>
      </main>
    </div>
  )
}
