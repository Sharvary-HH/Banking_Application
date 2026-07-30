import { useEffect, useState, type FormEvent } from 'react'
import { accountsApi } from '../api/accounts'
import { beneficiariesApi } from '../api/beneficiaries'
import { getErrorMessage } from '../api/errorMessage'
import type { Beneficiary } from '../api/types'
import Alert from '../components/Alert'
import Layout from '../components/Layout'

export default function Beneficiaries() {
  const [beneficiaries, setBeneficiaries] = useState<Beneficiary[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [loadError, setLoadError] = useState<string | null>(null)

  const [nickname, setNickname] = useState('')
  const [accountNumber, setAccountNumber] = useState('')
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [formError, setFormError] = useState<string | null>(null)
  const [successMessage, setSuccessMessage] = useState<string | null>(null)

  async function loadBeneficiaries() {
    setIsLoading(true)
    setLoadError(null)
    try {
      const data = await beneficiariesApi.list()
      setBeneficiaries(data)
    } catch (err) {
      setLoadError(getErrorMessage(err, 'Could not load beneficiaries.'))
    } finally {
      setIsLoading(false)
    }
  }

  useEffect(() => {
    void loadBeneficiaries()
  }, [])

  async function handleAdd(e: FormEvent) {
    e.preventDefault()
    setFormError(null)
    setSuccessMessage(null)
    setIsSubmitting(true)
    try {
      const account = await accountsApi.lookupByAccountNumber(accountNumber.trim())
      await beneficiariesApi.create({ nickname: nickname.trim(), account_id: account.id })
      setSuccessMessage(`Saved "${nickname.trim()}" (account #${account.account_number}).`)
      setNickname('')
      setAccountNumber('')
      await loadBeneficiaries()
    } catch (err) {
      setFormError(getErrorMessage(err, 'Could not save beneficiary. Check the account number and try again.'))
    } finally {
      setIsSubmitting(false)
    }
  }

  async function handleDelete(id: string) {
    try {
      await beneficiariesApi.remove(id)
      setBeneficiaries((prev) => prev.filter((b) => b.id !== id))
    } catch (err) {
      setLoadError(getErrorMessage(err, 'Could not remove beneficiary.'))
    }
  }

  return (
    <Layout>
      <h1 className="mb-6 text-2xl font-bold text-zinc-100">Beneficiaries</h1>

      <div className="card mb-6">
        <h2 className="mb-4 text-lg font-semibold text-zinc-100">Add a beneficiary</h2>
        <form onSubmit={handleAdd} className="grid grid-cols-1 gap-4 sm:grid-cols-3 sm:items-end">
          <div>
            <label htmlFor="nickname" className="label">
              Nickname
            </label>
            <input
              id="nickname"
              type="text"
              required
              className="input"
              placeholder="e.g. Landlord"
              value={nickname}
              onChange={(e) => setNickname(e.target.value)}
            />
          </div>
          <div>
            <label htmlFor="accountNumber" className="label">
              Account number
            </label>
            <input
              id="accountNumber"
              type="text"
              required
              className="input"
              placeholder="10-digit account number"
              value={accountNumber}
              onChange={(e) => setAccountNumber(e.target.value)}
            />
          </div>
          <button type="submit" disabled={isSubmitting} className="btn-primary">
            {isSubmitting ? 'Saving…' : 'Save beneficiary'}
          </button>
        </form>
        {formError && (
          <div className="mt-4">
            <Alert variant="error">{formError}</Alert>
          </div>
        )}
        {successMessage && (
          <div className="mt-4">
            <Alert variant="success">{successMessage}</Alert>
          </div>
        )}
      </div>

      {loadError && (
        <div className="mb-4">
          <Alert variant="error">{loadError}</Alert>
        </div>
      )}

      {isLoading ? (
        <p className="text-sm text-zinc-400">Loading beneficiaries…</p>
      ) : beneficiaries.length === 0 ? (
        <div className="card text-center text-sm text-zinc-400">No saved beneficiaries yet.</div>
      ) : (
        <div className="card divide-y divide-zinc-800">
          {beneficiaries.map((b) => (
            <div key={b.id} className="flex items-center justify-between py-3 first:pt-0 last:pb-0">
              <div>
                <p className="font-medium text-zinc-100">{b.nickname}</p>
                <p className="text-xs text-zinc-500">Account #{b.account_number}</p>
              </div>
              <button type="button" className="btn-secondary" onClick={() => void handleDelete(b.id)}>
                Remove
              </button>
            </div>
          ))}
        </div>
      )}
    </Layout>
  )
}
