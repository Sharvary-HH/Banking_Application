import { useState, type FormEvent } from 'react'
import { Link, useLocation, useNavigate } from 'react-router-dom'
import { authApi, isTwoFaRequired } from '../api/auth'
import { getErrorMessage } from '../api/errorMessage'
import Alert from '../components/Alert'
import { useAuth } from '../context/AuthContext'

interface LocationState {
  successMessage?: string
}

export default function Login() {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [isSubmitting, setIsSubmitting] = useState(false)
  const { login } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()
  const state = location.state as LocationState | null

  async function handleSubmit(e: FormEvent) {
    e.preventDefault()
    setError(null)
    setIsSubmitting(true)
    try {
      const res = await authApi.login({ email, password })
      if (isTwoFaRequired(res)) {
        navigate('/login/2fa', { state: { two_fa_token: res.two_fa_token } })
        return
      }
      await login(res)
      navigate('/dashboard')
    } catch (err) {
      setError(getErrorMessage(err, 'Login failed. Check your credentials and try again.'))
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-black px-4">
      <div className="w-full max-w-sm">
        <h1 className="mb-6 text-center text-2xl font-bold text-brand-400">Banking App</h1>
        <div className="card">
          <h2 className="mb-4 text-lg font-semibold text-zinc-100">Log in</h2>

          {state?.successMessage && (
            <div className="mb-4">
              <Alert variant="success">{state.successMessage}</Alert>
            </div>
          )}
          {error && (
            <div className="mb-4">
              <Alert variant="error">{error}</Alert>
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label htmlFor="email" className="label">
                Email
              </label>
              <input
                id="email"
                type="email"
                required
                autoComplete="email"
                className="input"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
              />
            </div>
            <div>
              <label htmlFor="password" className="label">
                Password
              </label>
              <input
                id="password"
                type="password"
                required
                autoComplete="current-password"
                className="input"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
              />
            </div>
            <button type="submit" disabled={isSubmitting} className="btn-primary w-full">
              {isSubmitting ? 'Logging in…' : 'Log in'}
            </button>
          </form>

          <p className="mt-4 text-center text-sm text-zinc-400">
            Don&apos;t have an account?{' '}
            <Link to="/register" className="font-medium text-brand-400 hover:text-brand-300">
              Register
            </Link>
          </p>
        </div>
      </div>
    </div>
  )
}
