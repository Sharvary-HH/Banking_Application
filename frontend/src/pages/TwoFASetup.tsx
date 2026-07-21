import { useEffect, useState, type FormEvent } from 'react'
import { authApi } from '../api/auth'
import { getErrorMessage } from '../api/errorMessage'
import Alert from '../components/Alert'
import Layout from '../components/Layout'
import type { Setup2FaResponse } from '../api/types'
import { useAuth } from '../context/AuthContext'

export default function TwoFASetup() {
  const [setupData, setSetupData] = useState<Setup2FaResponse | null>(null)
  const [loadError, setLoadError] = useState<string | null>(null)
  const [isLoadingSetup, setIsLoadingSetup] = useState(true)

  const [code, setCode] = useState('')
  const [submitError, setSubmitError] = useState<string | null>(null)
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [isEnabled, setIsEnabled] = useState(false)

  const { refreshUser } = useAuth()

  useEffect(() => {
    let cancelled = false
    async function loadSetup() {
      setIsLoadingSetup(true)
      setLoadError(null)
      try {
        const data = await authApi.setup2fa()
        if (!cancelled) setSetupData(data)
      } catch (err) {
        if (!cancelled) setLoadError(getErrorMessage(err, 'Could not load 2FA setup.'))
      } finally {
        if (!cancelled) setIsLoadingSetup(false)
      }
    }
    void loadSetup()
    return () => {
      cancelled = true
    }
  }, [])

  async function handleSubmit(e: FormEvent) {
    e.preventDefault()
    setSubmitError(null)
    setIsSubmitting(true)
    try {
      await authApi.enable2fa({ code })
      setIsEnabled(true)
      await refreshUser()
    } catch (err) {
      setSubmitError(getErrorMessage(err, 'Invalid code. Please try again.'))
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <Layout>
      <div className="mx-auto max-w-md">
        <h1 className="mb-6 text-2xl font-bold text-zinc-100">Two-factor authentication</h1>

        {isEnabled ? (
          <div className="card">
            <Alert variant="success">
              Two-factor authentication is now enabled on your account.
            </Alert>
          </div>
        ) : (
          <div className="card space-y-6">
            {isLoadingSetup && <p className="text-sm text-zinc-400">Loading setup…</p>}

            {loadError && <Alert variant="error">{loadError}</Alert>}

            {setupData && (
              <>
                <div>
                  <p className="mb-3 text-sm text-zinc-400">
                    Scan this QR code with your authenticator app (e.g. Google Authenticator, Authy).
                  </p>
                  <div className="flex justify-center">
                    <img
                      src={`data:image/png;base64,${setupData.qr_code_base64}`}
                      alt="2FA QR code"
                      className="h-48 w-48 rounded-md border border-zinc-700 bg-white p-2"
                    />
                  </div>
                </div>

                <div>
                  <p className="label">Can&apos;t scan? Enter this code manually:</p>
                  <code className="block break-all rounded-md bg-zinc-800 px-3 py-2 text-sm text-zinc-200">
                    {setupData.secret}
                  </code>
                </div>

                <form onSubmit={handleSubmit} className="space-y-4">
                  {submitError && <Alert variant="error">{submitError}</Alert>}
                  <div>
                    <label htmlFor="code" className="label">
                      Enter the 6-digit code to confirm
                    </label>
                    <input
                      id="code"
                      type="text"
                      inputMode="numeric"
                      pattern="[0-9]{6}"
                      maxLength={6}
                      required
                      className="input tracking-widest text-center text-lg"
                      value={code}
                      onChange={(e) => setCode(e.target.value.replace(/\D/g, ''))}
                      placeholder="000000"
                    />
                  </div>
                  <button
                    type="submit"
                    disabled={isSubmitting || code.length !== 6}
                    className="btn-primary w-full"
                  >
                    {isSubmitting ? 'Enabling…' : 'Enable 2FA'}
                  </button>
                </form>
              </>
            )}
          </div>
        )}
      </div>
    </Layout>
  )
}
