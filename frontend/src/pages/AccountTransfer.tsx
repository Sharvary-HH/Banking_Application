import { useEffect, useState, type FormEvent } from 'react'
import { Link, useParams } from 'react-router-dom'
import { accountsApi } from '../api/accounts'
import { getErrorMessage } from '../api/errorMessage'
import { transactionsApi } from '../api/transactions'
import type { Account, TransactionOut, TransferResponse } from '../api/types'
import Alert from '../components/Alert'
import Layout from '../components/Layout'
import { dollarsToCents, formatCents } from '../utils/money'

type Tab = 'deposit' | 'withdraw' | 'transfer'

export default function AccountTransfer() {
  const { id } = useParams<{ id: string }>()
  const accountId = id as string

  const [tab, setTab] = useState<Tab>('deposit')
  const [account, setAccount] = useState<Account | null>(null)
  const [otherAccounts, setOtherAccounts] = useState<Account[]>([])

  // Deposit / withdraw shared state
  const [amount, setAmount] = useState('')
  const [description, setDescription] = useState('')

  // Transfer-specific state
  const [targetAccountId, setTargetAccountId] = useState('')
  const [manualTargetAccountId, setManualTargetAccountId] = useState('')

  const [isSubmitting, setIsSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [successMessage, setSuccessMessage] = useState<string | null>(null)
  const [lastResult, setLastResult] = useState<TransactionOut | TransferResponse | null>(null)

  useEffect(() => {
    async function loadAccounts() {
      try {
        const all = await accountsApi.list()
        setAccount(all.find((a) => a.id === accountId) ?? null)
        setOtherAccounts(all.filter((a) => a.id !== accountId))
      } catch {
        // Non-fatal: the forms still work without this context.
      }
    }
    void loadAccounts()
  }, [accountId])

  function resetFeedback() {
    setError(null)
    setSuccessMessage(null)
    setLastResult(null)
  }

  function switchTab(next: Tab) {
    setTab(next)
    resetFeedback()
    setAmount('')
    setDescription('')
    setTargetAccountId('')
    setManualTargetAccountId('')
  }

  async function handleDeposit(e: FormEvent) {
    e.preventDefault()
    resetFeedback()
    const cents = dollarsToCents(amount)
    if (cents === null || cents <= 0) {
      setError('Enter a valid amount greater than 0.')
      return
    }
    setIsSubmitting(true)
    try {
      const result = await transactionsApi.deposit(accountId, {
        amount_cents: cents,
        description: description || undefined,
      })
      setLastResult(result)
      setSuccessMessage(`Deposited ${formatCents(cents)}. New balance: ${formatCents(result.balance_after_cents)}.`)
      setAmount('')
      setDescription('')
    } catch (err) {
      setError(getErrorMessage(err, 'Deposit failed.'))
    } finally {
      setIsSubmitting(false)
    }
  }

  async function handleWithdraw(e: FormEvent) {
    e.preventDefault()
    resetFeedback()
    const cents = dollarsToCents(amount)
    if (cents === null || cents <= 0) {
      setError('Enter a valid amount greater than 0.')
      return
    }
    setIsSubmitting(true)
    try {
      const result = await transactionsApi.withdraw(accountId, {
        amount_cents: cents,
        description: description || undefined,
      })
      setLastResult(result)
      setSuccessMessage(`Withdrew ${formatCents(cents)}. New balance: ${formatCents(result.balance_after_cents)}.`)
      setAmount('')
      setDescription('')
    } catch (err) {
      setError(getErrorMessage(err, 'Withdrawal failed.'))
    } finally {
      setIsSubmitting(false)
    }
  }

  async function handleTransfer(e: FormEvent) {
    e.preventDefault()
    resetFeedback()
    const cents = dollarsToCents(amount)
    if (cents === null || cents <= 0) {
      setError('Enter a valid amount greater than 0.')
      return
    }
    const destination = manualTargetAccountId.trim() || targetAccountId
    if (!destination) {
      setError('Choose a destination account or enter an account id.')
      return
    }
    setIsSubmitting(true)
    try {
      const result = await transactionsApi.transfer({
        from_account_id: accountId,
        to_account_id: destination,
        amount_cents: cents,
        description: description || undefined,
      })
      setLastResult(result)
      setSuccessMessage(
        `Transferred ${formatCents(cents)} to account ${destination}. New balance: ${formatCents(
          result.debit.balance_after_cents,
        )}.`,
      )
      setAmount('')
      setDescription('')
      setTargetAccountId('')
      setManualTargetAccountId('')
    } catch (err) {
      setError(getErrorMessage(err, 'Transfer failed.'))
    } finally {
      setIsSubmitting(false)
    }
  }

  const tabs: { key: Tab; label: string }[] = [
    { key: 'deposit', label: 'Deposit' },
    { key: 'withdraw', label: 'Withdraw' },
    { key: 'transfer', label: 'Transfer' },
  ]

  return (
    <Layout>
      <div className="mx-auto max-w-lg">
        <div className="mb-6 flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-slate-900">Manage funds</h1>
            {account && (
              <p className="text-sm text-slate-500">
                Account #{account.account_number} · {formatCents(account.balance_cents)}
              </p>
            )}
          </div>
          <Link to="/dashboard" className="text-sm font-medium text-brand-600 hover:text-brand-700">
            Back to dashboard
          </Link>
        </div>

        <div className="card">
          <div className="mb-6 flex gap-1 rounded-md bg-slate-100 p-1">
            {tabs.map((t) => (
              <button
                key={t.key}
                type="button"
                onClick={() => switchTab(t.key)}
                className={`flex-1 rounded-md px-3 py-1.5 text-sm font-medium transition-colors ${
                  tab === t.key ? 'bg-white text-brand-700 shadow-sm' : 'text-slate-500 hover:text-slate-700'
                }`}
              >
                {t.label}
              </button>
            ))}
          </div>

          {error && (
            <div className="mb-4">
              <Alert variant="error">{error}</Alert>
            </div>
          )}
          {successMessage && (
            <div className="mb-4">
              <Alert variant="success">{successMessage}</Alert>
            </div>
          )}

          {tab === 'deposit' && (
            <form onSubmit={handleDeposit} className="space-y-4">
              <AmountField amount={amount} setAmount={setAmount} />
              <DescriptionField description={description} setDescription={setDescription} />
              <button type="submit" disabled={isSubmitting} className="btn-primary w-full">
                {isSubmitting ? 'Depositing…' : 'Deposit'}
              </button>
            </form>
          )}

          {tab === 'withdraw' && (
            <form onSubmit={handleWithdraw} className="space-y-4">
              <AmountField amount={amount} setAmount={setAmount} />
              <DescriptionField description={description} setDescription={setDescription} />
              <button type="submit" disabled={isSubmitting} className="btn-primary w-full">
                {isSubmitting ? 'Withdrawing…' : 'Withdraw'}
              </button>
            </form>
          )}

          {tab === 'transfer' && (
            <form onSubmit={handleTransfer} className="space-y-4">
              <AmountField amount={amount} setAmount={setAmount} />
              <div>
                <label htmlFor="targetAccount" className="label">
                  Destination account
                </label>
                <select
                  id="targetAccount"
                  className="input"
                  value={targetAccountId}
                  onChange={(e) => {
                    setTargetAccountId(e.target.value)
                    setManualTargetAccountId('')
                  }}
                  disabled={otherAccounts.length === 0}
                >
                  <option value="">
                    {otherAccounts.length === 0 ? 'No other accounts available' : 'Select an account…'}
                  </option>
                  {otherAccounts.map((a) => (
                    <option key={a.id} value={a.id}>
                      {a.account_type} · #{a.account_number}
                    </option>
                  ))}
                </select>
              </div>
              <div>
                <label htmlFor="manualTargetAccount" className="label">
                  Or enter an account id directly
                </label>
                <input
                  id="manualTargetAccount"
                  type="text"
                  className="input"
                  placeholder="e.g. an external recipient's account id"
                  value={manualTargetAccountId}
                  onChange={(e) => {
                    setManualTargetAccountId(e.target.value)
                    if (e.target.value) setTargetAccountId('')
                  }}
                />
              </div>
              <DescriptionField description={description} setDescription={setDescription} />
              <button type="submit" disabled={isSubmitting} className="btn-primary w-full">
                {isSubmitting ? 'Transferring…' : 'Transfer'}
              </button>
            </form>
          )}

          {lastResult && (
            <div className="mt-6 rounded-md border border-slate-200 bg-slate-50 p-3 text-xs text-slate-500">
              <p className="mb-1 font-medium text-slate-600">Transaction reference</p>
              {'reference_id' in lastResult ? (
                <p>{lastResult.reference_id ?? lastResult.id}</p>
              ) : (
                <p>{lastResult.debit.reference_id ?? lastResult.debit.id}</p>
              )}
            </div>
          )}
        </div>
      </div>
    </Layout>
  )
}

function AmountField({
  amount,
  setAmount,
}: {
  amount: string
  setAmount: (v: string) => void
}) {
  return (
    <div>
      <label htmlFor="amount" className="label">
        Amount (USD)
      </label>
      <div className="relative">
        <span className="pointer-events-none absolute inset-y-0 left-3 flex items-center text-slate-400">$</span>
        <input
          id="amount"
          type="text"
          inputMode="decimal"
          required
          className="input pl-6"
          placeholder="0.00"
          value={amount}
          onChange={(e) => setAmount(e.target.value)}
        />
      </div>
    </div>
  )
}

function DescriptionField({
  description,
  setDescription,
}: {
  description: string
  setDescription: (v: string) => void
}) {
  return (
    <div>
      <label htmlFor="description" className="label">
        Description (optional)
      </label>
      <input
        id="description"
        type="text"
        className="input"
        value={description}
        onChange={(e) => setDescription(e.target.value)}
      />
    </div>
  )
}
