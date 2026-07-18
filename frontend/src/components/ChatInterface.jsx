import { useState, useRef, useEffect } from 'react'
import { useSelector } from 'react-redux'
import api from '../api/axios'

export default function ChatInterface() {
  const token = useSelector((state) => state.auth.token)

  const [messages, setMessages] = useState([
    {
      id: 'welcome',
      role: 'ai',
      text: 'Hello! I\'m your PharmaConnect AI assistant. I can help you with HCP insights, interaction summaries, product details, or any CRM-related questions. How can I help you today?',
    },
  ])
  const [input, setInput] = useState('')
  const [sending, setSending] = useState(false)

  const messagesEndRef = useRef(null)
  const inputRef = useRef(null)

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  const sendMessage = async () => {
    const text = input.trim()
    if (!text || sending) return

    const userMsg = { id: Date.now(), role: 'user', text }
    setMessages((prev) => [...prev, userMsg])
    setInput('')
    setSending(true)

    try {
      const res = await api.post('/chat', null, {
        params: { token, message: text },
      })
      const aiText = res.data?.response || 'No response received.'
      setMessages((prev) => [
        ...prev,
        { id: Date.now() + 1, role: 'ai', text: aiText },
      ])
    } catch (err) {
      const errMsg =
        err.response?.data?.detail ||
        err.response?.data?.message ||
        'Failed to get a response. Please try again.'
      setMessages((prev) => [
        ...prev,
        { id: Date.now() + 1, role: 'ai', text: errMsg, isError: true },
      ])
    } finally {
      setSending(false)
      inputRef.current?.focus()
    }
  }

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      sendMessage()
    }
  }

  return (
    <div className="panel chat-panel">
      <div className="panel-header">
        <h2 className="panel-title">AI Assistant</h2>
        <p className="panel-subtitle">Ask questions about HCPs, interactions, and products</p>
      </div>

      {/* Messages area */}
      <div className="chat-messages">
        {messages.map((msg) => (
          <div
            key={msg.id}
            className={`chat-message ${msg.role === 'user' ? 'chat-message--user' : 'chat-message--ai'}`}
          >
            {msg.role === 'ai' && (
              <div className="chat-avatar">AI</div>
            )}
            <div
              className={`chat-bubble ${
                msg.role === 'user'
                  ? 'chat-bubble--user'
                  : msg.isError
                  ? 'chat-bubble--error'
                  : 'chat-bubble--ai'
              }`}
            >
              {msg.text}
            </div>
            {msg.role === 'user' && (
              <div className="chat-avatar chat-avatar--user">You</div>
            )}
          </div>
        ))}

        {sending && (
          <div className="chat-message chat-message--ai">
            <div className="chat-avatar">AI</div>
            <div className="chat-bubble chat-bubble--ai chat-bubble--typing">
              <span className="typing-dot" />
              <span className="typing-dot" />
              <span className="typing-dot" />
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Input area */}
      <div className="chat-input-area">
        <textarea
          ref={inputRef}
          className="chat-input"
          rows={1}
          placeholder="Type your message... (Enter to send, Shift+Enter for new line)"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          disabled={sending}
        />
        <button
          className="chat-send-btn"
          onClick={sendMessage}
          disabled={sending || !input.trim()}
          aria-label="Send message"
        >
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <line x1="22" y1="2" x2="11" y2="13" />
            <polygon points="22 2 15 22 11 13 2 9 22 2" />
          </svg>
        </button>
      </div>
    </div>
  )
}
