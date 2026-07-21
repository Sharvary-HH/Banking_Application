import { useEffect, useState, type FormEvent } from 'react'
import { Link } from 'react-router-dom'
import { accountsApi } from '../api/accounts'
import { getErrorMessage } from '../api/errorMessage'
import type { Account, AccountType } from '../api/types'
import Alert from '../components/Alert'
import Layout from '../components/Layout'
import { formatCents } from '../utils/money'

export default function Dashboard() {
  const [accounts, setAccounts] = useState<Account[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [loadError, setLoadError] = useState<string | null>(null)

  const [isDialogOpen, setIsDialogOpen] = useState(false)
  const [accountType, setAccountType] = useState<AccountType>('savings')
  const [isCreating, setIsCreating] = useState(false)
  const [createError, setCreateError] = useState<string | null>(null)

  async function loadAccounts() {
    setIsLoading(true)
    setLoadError(null)
    try {
      const data = await accountsApi.list()
      setAccounts(data)
    } catch (err) {
      setLoadError(getErrorMessage(err, 'Could not load accounts.'))
    } finally {
      setIsLoading(false)
    }
  }

  useEffect(() => {
    void loadAccounts()
  }, [])

  async function handleCreate(e: FormEvent) {
    e.preventDefault()
    setCreateError(null)
    setIsCreating(true)
    try {
      await accountsApi.create({ account_type: accountType })
      setIsDialogOpen(false)
      setAccountType('savings')
      await loadAccounts()
    } catch (err) {
      setCreateError(getErrorMessage(err, 'Could not create account.'))
    } finally {
      setIsCreating(false)
    }
  }

  return (
    <Layout>
      <div className="mb-6 flex items-center justify-between">
        <h1 className="text-2xl font-bold text-slate-900">Your accounts</h1>
        <button type="button" className="btn-primary" onClick={() => setIsDialogOpen(true)}>
          + Create account
        </button>
      </div>

      {loadError && (
        <div className="mb-4">
          <Alert variant="error">{loadError}</Alert>
        </div>
      )}

      {isLoading ? (
        <p className="text-sm text-slate-500">Loading accounts…</p>
      ) : accounts.length === 0 ? (
        <div className="card text-center text-sm text-slate-500">
          You don&apos;t have any accounts yet. Create one to get started.
        </div>
      ) : (
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
          {accounts.map((account) => (
            <div key={account.id} className="card">
              <div className="mb-2 flex items-center justify-between">
                <span className="rounded-full bg-brand-50 px-2.5 py-0.5 text-xs font-semibold uppercase tracking-wide text-brand-700">
                  {account.account_type}
                </span>
                <span className="text-xs text-slate-400">
                  {new Date(account.created_at).toLocaleDateString()}
                </span>
              </div>
              <p className="text-sm text-slate-500">Account #{account.account_number}</p>
              <p className="mt-1 text-2xl font-bold text-slate-900">
                {formatCents(account.balance_cents)}
              </p>
              <div className="mt-4 flex gap-2">
                <Link to={`/accounts/${account.id}/transfer`} className="btn-secondary flex-1 text-center">
                  Transfer / Deposit
                </Link>
                <Link to={`/accounts/${account.id}/history`} className="btn-secondary flex-1 text-center">
                  History
                </Link>
              </div>
            </div>
          ))}
        </div>
      )}

      {isDialogOpen && (
        <div className="fixed inset-0 z-10 flex items-center justify-center bg-slate-900/40 px-4">
          <div className="w-full max-w-sm rounded-xl bg-white p-6 shadow-lg">
            <h2 className="mb-4 text-lg font-semibold text-slate-900">Create account</h2>

            {createError && (
              <div className="mb-4">
                <Alert variant="error">{createError}</Alert>
              </div>
            )}

            <form onSubmit={handleCreate} className="space-y-4">
              <div>
                <label htmlFor="accountType" className="label">
                  Account type
                </label>
                <select
                  id="accountType"
                  className="input"
                  value={accountType}
                  onChange={(e) => setAccountType(e.target.value as AccountType)}
                >
                  <option value="savings">Savings</option>
                  <option value="checking">Checking</option>
                </select>
              </div>
              <div className="flex gap-2">
                <button
                  type="button"
                  className="btn-secondary flex-1"
                  onClick={() => setIsDialogOpen(false)}
                  disabled={isCreating}
                >
                  Cancel
                </button>
                <button type="submit" className="btn-primary flex-1" disabled={isCreating}>
                  {isCreating ? 'Creating…' : 'Create'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </Layout>
  )
}
