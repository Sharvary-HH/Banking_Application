import { useEffect, useState, type FormEvent } from 'react'
import { Link, useParams } from 'react-router-dom'
import { getErrorMessage } from '../api/errorMessage'
import { transactionsApi } from '../api/transactions'
import type { TransactionListParams, TransactionOut, TransactionType } from '../api/types'
import Alert from '../components/Alert'
import Layout from '../components/Layout'
import { dollarsToCents, formatCents, formatDate } from '../utils/money'

const PAGE_SIZE = 20

const TYPE_LABELS: Record<TransactionType, string> = {
  deposit: 'Deposit',
  withdraw: 'Withdraw',
  transfer_in: 'Transfer in',
  transfer_out: 'Transfer out',
}

const CREDIT_TYPES: TransactionType[] = ['deposit', 'transfer_in']

interface FilterFormState {
  type: TransactionType | ''
  startDate: string
  endDate: string
  minAmount: string
  maxAmount: string
}

const emptyFilters: FilterFormState = {
  type: '',
  startDate: '',
  endDate: '',
  minAmount: '',
  maxAmount: '',
}

export default function AccountHistory() {
  const { id } = useParams<{ id: string }>()
  const accountId = id as string

  const [filters, setFilters] = useState<FilterFormState>(emptyFilters)
  const [appliedFilters, setAppliedFilters] = useState<FilterFormState>(emptyFilters)
  const [page, setPage] = useState(1)

  const [items, setItems] = useState<TransactionOut[]>([])
  const [total, setTotal] = useState(0)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    async function load() {
      setIsLoading(true)
      setError(null)
      try {
        const params: TransactionListParams = {
          page,
          page_size: PAGE_SIZE,
        }
        if (appliedFilters.type) params.type = appliedFilters.type
        if (appliedFilters.startDate) params.start_date = appliedFilters.startDate
        if (appliedFilters.endDate) params.end_date = appliedFilters.endDate
        if (appliedFilters.minAmount) {
          const cents = dollarsToCents(appliedFilters.minAmount)
          if (cents !== null) params.min_amount_cents = cents
        }
        if (appliedFilters.maxAmount) {
          const cents = dollarsToCents(appliedFilters.maxAmount)
          if (cents !== null) params.max_amount_cents = cents
        }

        const res = await transactionsApi.list(accountId, params)
        setItems(res.items)
        setTotal(res.total)
      } catch (err) {
        setError(getErrorMessage(err, 'Could not load transaction history.'))
      } finally {
        setIsLoading(false)
      }
    }
    void load()
  }, [accountId, appliedFilters, page])

  function handleApplyFilters(e: FormEvent) {
    e.preventDefault()
    setPage(1)
    setAppliedFilters(filters)
  }

  function handleResetFilters() {
    setFilters(emptyFilters)
    setAppliedFilters(emptyFilters)
    setPage(1)
  }

  const totalPages = Math.max(1, Math.ceil(total / PAGE_SIZE))

  return (
    <Layout>
      <div className="mb-6 flex items-center justify-between">
        <h1 className="text-2xl font-bold text-slate-900">Transaction history</h1>
        <Link to="/dashboard" className="text-sm font-medium text-brand-600 hover:text-brand-700">
          Back to dashboard
        </Link>
      </div>

      <div className="card mb-6">
        <form onSubmit={handleApplyFilters} className="grid grid-cols-1 gap-4 sm:grid-cols-3 lg:grid-cols-5">
          <div>
            <label htmlFor="type" className="label">
              Type
            </label>
            <select
              id="type"
              className="input"
              value={filters.type}
              onChange={(e) => setFilters((f) => ({ ...f, type: e.target.value as TransactionType | '' }))}
            >
              <option value="">All</option>
              {Object.entries(TYPE_LABELS).map(([value, label]) => (
                <option key={value} value={value}>
                  {label}
                </option>
              ))}
            </select>
          </div>
          <div>
            <label htmlFor="startDate" className="label">
              Start date
            </label>
            <input
              id="startDate"
              type="date"
              className="input"
              value={filters.startDate}
              onChange={(e) => setFilters((f) => ({ ...f, startDate: e.target.value }))}
            />
          </div>
          <div>
            <label htmlFor="endDate" className="label">
              End date
            </label>
            <input
              id="endDate"
              type="date"
              className="input"
              value={filters.endDate}
              onChange={(e) => setFilters((f) => ({ ...f, endDate: e.target.value }))}
            />
          </div>
          <div>
            <label htmlFor="minAmount" className="label">
              Min amount ($)
            </label>
            <input
              id="minAmount"
              type="text"
              inputMode="decimal"
              className="input"
              placeholder="0.00"
              value={filters.minAmount}
              onChange={(e) => setFilters((f) => ({ ...f, minAmount: e.target.value }))}
            />
          </div>
          <div>
            <label htmlFor="maxAmount" className="label">
              Max amount ($)
            </label>
            <input
              id="maxAmount"
              type="text"
              inputMode="decimal"
              className="input"
              placeholder="0.00"
              value={filters.maxAmount}
              onChange={(e) => setFilters((f) => ({ ...f, maxAmount: e.target.value }))}
            />
          </div>
          <div className="flex items-end gap-2 sm:col-span-3 lg:col-span-5">
            <button type="submit" className="btn-primary">
              Apply filters
            </button>
            <button type="button" className="btn-secondary" onClick={handleResetFilters}>
              Reset
            </button>
          </div>
        </form>
      </div>

      {error && (
        <div className="mb-4">
          <Alert variant="error">{error}</Alert>
        </div>
      )}

      <div className="card overflow-x-auto">
        {isLoading ? (
          <p className="text-sm text-slate-500">Loading transactions…</p>
        ) : items.length === 0 ? (
          <p className="text-sm text-slate-500">No transactions found.</p>
        ) : (
          <table className="min-w-full divide-y divide-slate-200 text-sm">
            <thead>
              <tr className="text-left text-xs uppercase tracking-wide text-slate-500">
                <th className="py-2 pr-4">Date</th>
                <th className="py-2 pr-4">Type</th>
                <th className="py-2 pr-4">Amount</th>
                <th className="py-2 pr-4">Balance after</th>
                <th className="py-2 pr-4">Description</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {items.map((tx) => {
                const isCredit = CREDIT_TYPES.includes(tx.type)
                return (
                  <tr key={tx.id}>
                    <td className="py-2 pr-4 whitespace-nowrap text-slate-600">{formatDate(tx.created_at)}</td>
                    <td className="py-2 pr-4 whitespace-nowrap text-slate-600">{TYPE_LABELS[tx.type]}</td>
                    <td
                      className={`py-2 pr-4 whitespace-nowrap font-medium ${
                        isCredit ? 'text-green-600' : 'text-red-600'
                      }`}
                    >
                      {isCredit ? '+' : '-'}
                      {formatCents(tx.amount_cents)}
                    </td>
                    <td className="py-2 pr-4 whitespace-nowrap text-slate-600">
                      {formatCents(tx.balance_after_cents)}
                    </td>
                    <td className="py-2 pr-4 text-slate-500">{tx.description ?? '—'}</td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        )}
      </div>

      {total > 0 && (
        <div className="mt-4 flex items-center justify-between text-sm text-slate-500">
          <span>
            Page {page} of {totalPages} · {total} total
          </span>
          <div className="flex gap-2">
            <button
              type="button"
              className="btn-secondary"
              disabled={page <= 1}
              onClick={() => setPage((p) => Math.max(1, p - 1))}
            >
              Prev
            </button>
            <button
              type="button"
              className="btn-secondary"
              disabled={page >= totalPages}
              onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
            >
              Next
            </button>
          </div>
        </div>
      )}
    </Layout>
  )
}
