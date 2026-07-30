import { useEffect, useState, type FormEvent } from 'react'
import { Link, useParams } from 'react-router-dom'
import { accountsApi } from '../api/accounts'
import { beneficiariesApi } from '../api/beneficiaries'
import { getErrorMessage } from '../api/errorMessage'
import { scheduledTransfersApi } from '../api/scheduledTransfers'
import { transactionsApi } from '../api/transactions'
import type { Account, Beneficiary, TransactionOut, TransferFrequency, TransferResponse } from '../api/types'
import Alert from '../components/Alert'
import Layout from '../components/Layout'
import { dollarsToCents, formatCents } from '../utils/money'

type Tab = 'deposit' | 'withdraw' | 'transfer'

const FREQUENCIES: { key: TransferFrequency; label: string }[] = [
  { key: 'once', label: 'Once' },
  { key: 'daily', label: 'Daily' },
  { key: 'weekly', label: 'Weekly' },
  { key: 'monthly', label: 'Monthly' },
]

export default function AccountTransfer() {
  const { id } = useParams<{ id: string }>()
  const accountId = id as string

  const [tab, setTab] = useState<Tab>('deposit')
  const [account, setAccount] = useState<Account | null>(null)
  const [otherAccounts, setOtherAccounts] = useState<Account[]>([])
  const [beneficiaries, setBeneficiaries] = useState<Beneficiary[]>([])

  // Deposit / withdraw shared state
  const [amount, setAmount] = useState('')
  const [description, setDescription] = useState('')

  // Transfer-specific state
  const [targetAccountId, setTargetAccountId] = useState('')
  const [manualTargetAccountId, setManualTargetAccountId] = useState('')

  // Scheduling state (only used when isScheduled is on, within the transfer tab)
  const [isScheduled, setIsScheduled] = useState(false)
  const [frequency, setFrequency] = useState<TransferFrequency>('once')
  const [startDate, setStartDate] = useState('')
  const [endDate, setEndDate] = useState('')

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
    async function loadBeneficiaries() {
      try {
        setBeneficiaries(await beneficiariesApi.list())
      } catch {
        // Non-fatal: the manual account-id fallback still works.
      }
    }
    void loadAccounts()
    void loadBeneficiaries()
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
    setIsScheduled(false)
    setFrequency('once')
    setStartDate('')
    setEndDate('')
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
      if (isScheduled) {
        await scheduledTransfersApi.create({
          from_account_id: accountId,
          to_account_id: destination,
          amount_cents: cents,
          description: description || undefined,
          frequency,
          start_at: startDate ? new Date(startDate).toISOString() : undefined,
          end_date: endDate ? new Date(endDate).toISOString() : undefined,
        })
        setSuccessMessage(
          `Scheduled a ${frequency} transfer of ${formatCents(cents)}. See it on the Scheduled Transfers page.`,
        )
      } else {
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
      }
      setAmount('')
      setDescription('')
      setTargetAccountId('')
      setManualTargetAccountId('')
      setStartDate('')
      setEndDate('')
    } catch (err) {
      setError(getErrorMessage(err, isScheduled ? 'Could not schedule transfer.' : 'Transfer failed.'))
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
            <h1 className="text-2xl font-bold text-zinc-100">Manage funds</h1>
            {account && (
              <p className="text-sm text-zinc-400">
                Account #{account.account_number} · {formatCents(account.balance_cents)}
              </p>
            )}
          </div>
          <Link to="/dashboard" className="text-sm font-medium text-brand-400 hover:text-brand-300">
            Back to dashboard
          </Link>
        </div>

        <div className="card">
          <div className="mb-6 flex gap-1 rounded-md bg-zinc-800 p-1">
            {tabs.map((t) => (
              <button
                key={t.key}
                type="button"
                onClick={() => switchTab(t.key)}
                className={`flex-1 rounded-md px-3 py-1.5 text-sm font-medium transition-colors ${
                  tab === t.key ? 'bg-zinc-950 text-brand-400 shadow-sm' : 'text-zinc-400 hover:text-zinc-200'
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
                  disabled={otherAccounts.length === 0 && beneficiaries.length === 0}
                >
                  <option value="">
                    {otherAccounts.length === 0 && beneficiaries.length === 0
                      ? 'No saved accounts or beneficiaries'
                      : 'Select an account…'}
                  </option>
                  {otherAccounts.length > 0 && (
                    <optgroup label="Your other accounts">
                      {otherAccounts.map((a) => (
                        <option key={a.id} value={a.id}>
                          {a.account_type} · #{a.account_number}
                        </option>
                      ))}
                    </optgroup>
                  )}
                  {beneficiaries.length > 0 && (
                    <optgroup label="Beneficiaries">
                      {beneficiaries.map((b) => (
                        <option key={b.id} value={b.account_id}>
                          {b.nickname} · #{b.account_number}
                        </option>
                      ))}
                    </optgroup>
                  )}
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

              <div className="flex items-center gap-2">
                <input
                  id="isScheduled"
                  type="checkbox"
                  checked={isScheduled}
                  onChange={(e) => setIsScheduled(e.target.checked)}
                  className="h-4 w-4 rounded border-zinc-700 bg-zinc-900 text-brand-600 focus:ring-brand-500"
                />
                <label htmlFor="isScheduled" className="text-sm text-zinc-300">
                  Schedule this transfer instead of sending it now
                </label>
              </div>

              {isScheduled && (
                <div className="space-y-4 rounded-md border border-zinc-800 bg-zinc-950 p-3">
                  <div>
                    <label htmlFor="frequency" className="label">
                      Frequency
                    </label>
                    <select
                      id="frequency"
                      className="input"
                      value={frequency}
                      onChange={(e) => setFrequency(e.target.value as TransferFrequency)}
                    >
                      {FREQUENCIES.map((f) => (
                        <option key={f.key} value={f.key}>
                          {f.label}
                        </option>
                      ))}
                    </select>
                  </div>
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <label htmlFor="startDate" className="label">
                        Start (optional, defaults to now)
                      </label>
                      <input
                        id="startDate"
                        type="datetime-local"
                        className="input"
                        value={startDate}
                        onChange={(e) => setStartDate(e.target.value)}
                      />
                    </div>
                    {frequency !== 'once' && (
                      <div>
                        <label htmlFor="endDate" className="label">
                          End (optional)
                        </label>
                        <input
                          id="endDate"
                          type="date"
                          className="input"
                          value={endDate}
                          onChange={(e) => setEndDate(e.target.value)}
                        />
                      </div>
                    )}
                  </div>
                </div>
              )}

              <button type="submit" disabled={isSubmitting} className="btn-primary w-full">
                {isSubmitting ? (isScheduled ? 'Scheduling…' : 'Transferring…') : isScheduled ? 'Schedule transfer' : 'Transfer'}
              </button>
            </form>
          )}

          {lastResult && (
            <div className="mt-6 rounded-md border border-zinc-800 bg-zinc-950 p-3 text-xs text-zinc-400">
              <p className="mb-1 font-medium text-zinc-300">Transaction reference</p>
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
        <span className="pointer-events-none absolute inset-y-0 left-3 flex items-center text-zinc-500">$</span>
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
