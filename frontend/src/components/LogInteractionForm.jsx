import { useState, useEffect } from 'react'
import { useSelector } from 'react-redux'
import api from '../api/axios'

const INITIAL_FORM = {
  hcp_id: '',
  date: '',
  location: '',
  interaction_type: 'visit',
  products_discussed: '',
  notes: '',
}

export default function LogInteractionForm() {
  const token = useSelector((state) => state.auth.token)

  const [hcps, setHcps] = useState([])
  const [hcpsLoading, setHcpsLoading] = useState(true)
  const [hcpsError, setHcpsError] = useState('')

  const [form, setForm] = useState(INITIAL_FORM)
  const [submitting, setSubmitting] = useState(false)
  const [submitError, setSubmitError] = useState('')
  const [submitSuccess, setSubmitSuccess] = useState('')

  useEffect(() => {
    const fetchHcps = async () => {
      setHcpsLoading(true)
      setHcpsError('')
      try {
        const res = await api.get('/hcps', { params: { token } })
        setHcps(res.data || [])
      } catch (err) {
        setHcpsError('Failed to load HCPs. Please refresh the page.')
      } finally {
        setHcpsLoading(false)
      }
    }
    if (token) fetchHcps()
  }, [token])

  const handleChange = (e) => {
    setForm({ ...form, [e.target.name]: e.target.value })
    setSubmitError('')
    setSubmitSuccess('')
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (!form.hcp_id) {
      setSubmitError('Please select an HCP.')
      return
    }
    setSubmitting(true)
    setSubmitError('')
    setSubmitSuccess('')
    try {
      await api.post('/interactions', form, { params: { token } })
      setSubmitSuccess('Interaction logged successfully!')
      setForm(INITIAL_FORM)
    } catch (err) {
      const msg =
        err.response?.data?.detail ||
        err.response?.data?.message ||
        'Failed to log interaction. Please try again.'
      setSubmitError(msg)
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div className="panel">
      <div className="panel-header">
        <h2 className="panel-title">Log an Interaction</h2>
        <p className="panel-subtitle">Record a new HCP interaction with detailed notes</p>
      </div>

      <form onSubmit={handleSubmit} className="interaction-form">
        {/* HCP Dropdown */}
        <div className="form-group">
          <label htmlFor="hcp_id" className="form-label">
            Healthcare Professional (HCP)
          </label>
          {hcpsLoading ? (
            <div className="form-loading">Loading HCPs...</div>
          ) : hcpsError ? (
            <div className="form-error">{hcpsError}</div>
          ) : (
            <select
              id="hcp_id"
              name="hcp_id"
              required
              className="form-input form-select"
              value={form.hcp_id}
              onChange={handleChange}
            >
              <option value="">Select an HCP...</option>
              {hcps.map((hcp) => (
                <option key={hcp.id} value={hcp.id}>
                  {hcp.name}
                  {hcp.specialty ? ` — ${hcp.specialty}` : ''}
                  {hcp.hospital ? ` (${hcp.hospital})` : ''}
                </option>
              ))}
            </select>
          )}
          {!hcpsLoading && !hcpsError && hcps.length === 0 && (
            <p className="form-hint">No HCPs found. Add some via the API first.</p>
          )}
        </div>

        {/* Two-column row: Date + Location */}
        <div className="form-row">
          <div className="form-group">
            <label htmlFor="date" className="form-label">Date</label>
            <input
              id="date"
              name="date"
              type="date"
              required
              className="form-input"
              value={form.date}
              onChange={handleChange}
            />
          </div>

          <div className="form-group">
            <label htmlFor="location" className="form-label">Location</label>
            <input
              id="location"
              name="location"
              type="text"
              required
              className="form-input"
              placeholder="e.g. City Hospital, Room 4B"
              value={form.location}
              onChange={handleChange}
            />
          </div>
        </div>

        {/* Interaction Type */}
        <div className="form-group">
          <label htmlFor="interaction_type" className="form-label">Interaction Type</label>
          <select
            id="interaction_type"
            name="interaction_type"
            required
            className="form-input form-select"
            value={form.interaction_type}
            onChange={handleChange}
          >
            <option value="visit">In-person Visit</option>
            <option value="call">Phone Call</option>
            <option value="email">Email</option>
          </select>
        </div>

        {/* Products Discussed */}
        <div className="form-group">
          <label htmlFor="products_discussed" className="form-label">Products Discussed</label>
          <input
            id="products_discussed"
            name="products_discussed"
            type="text"
            required
            className="form-input"
            placeholder="e.g. Cardiplex, OncoPrime XR"
            value={form.products_discussed}
            onChange={handleChange}
          />
        </div>

        {/* Notes */}
        <div className="form-group">
          <label htmlFor="notes" className="form-label">Notes</label>
          <textarea
            id="notes"
            name="notes"
            rows={4}
            className="form-input form-textarea"
            placeholder="Add any relevant notes about the interaction..."
            value={form.notes}
            onChange={handleChange}
          />
        </div>

        {submitError && <div className="form-error">{submitError}</div>}
        {submitSuccess && <div className="form-success">{submitSuccess}</div>}

        <button
          type="submit"
          className="btn-primary"
          disabled={submitting || hcpsLoading}
        >
          {submitting ? 'Logging...' : 'Log Interaction'}
        </button>
      </form>
    </div>
  )
}
