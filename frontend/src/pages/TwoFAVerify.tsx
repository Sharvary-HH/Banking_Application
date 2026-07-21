import { useState, type FormEvent } from 'react'
import { Navigate, useLocation, useNavigate } from 'react-router-dom'
import { authApi } from '../api/auth'
import { getErrorMessage } from '../api/errorMessage'
import Alert from '../components/Alert'
import { useAuth } from '../context/AuthContext'

interface LocationState {
  two_fa_token?: string
}

export default function TwoFAVerify() {
  const location = useLocation()
  const navigate = useNavigate()
  const { login } = useAuth()
  const state = location.state as LocationState | null
  const twoFaToken = state?.two_fa_token

  const [code, setCode] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [isSubmitting, setIsSubmitting] = useState(false)

  if (!twoFaToken) {
    return <Navigate to="/login" replace />
  }

  async function handleSubmit(e: FormEvent) {
    e.preventDefault()
    setError(null)
    setIsSubmitting(true)
    try {
      const tokens = await authApi.verify2fa({ two_fa_token: twoFaToken as string, code })
      await login(tokens)
      navigate('/dashboard')
    } catch (err) {
      setError(getErrorMessage(err, 'Invalid or expired code.'))
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-black px-4">
      <div className="w-full max-w-sm">
        <h1 className="mb-6 text-center text-2xl font-bold text-brand-400">Banking App</h1>
        <div className="card">
          <h2 className="mb-1 text-lg font-semibold text-zinc-100">Two-factor verification</h2>
          <p className="mb-4 text-sm text-zinc-400">Enter the 6-digit code from your authenticator app.</p>

          {error && (
            <div className="mb-4">
              <Alert variant="error">{error}</Alert>
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label htmlFor="code" className="label">
                Authentication code
              </label>
              <input
                id="code"
                type="text"
                inputMode="numeric"
                pattern="[0-9]{6}"
                maxLength={6}
                required
                autoFocus
                className="input tracking-widest text-center text-lg"
                value={code}
                onChange={(e) => setCode(e.target.value.replace(/\D/g, ''))}
                placeholder="000000"
              />
            </div>
            <button type="submit" disabled={isSubmitting || code.length !== 6} className="btn-primary w-full">
              {isSubmitting ? 'Verifying…' : 'Verify'}
            </button>
          </form>
        </div>
      </div>
    </div>
  )
}
