import { useEffect, useState, type FormEvent } from 'react'
import {
  Bar,
  BarChart,
  CartesianGrid,
  Legend,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
  type TooltipContentProps,
  type TooltipValueType,
} from 'recharts'
import { accountsApi } from '../api/accounts'
import { analyticsApi } from '../api/analytics'
import { getErrorMessage } from '../api/errorMessage'
import type { Account, AnalyticsSummary, TransactionType } from '../api/types'
import Alert from '../components/Alert'
import Layout from '../components/Layout'
import { formatCents } from '../utils/money'

// Validated against the app's dark (zinc-900) chart surface with the dataviz skill's
// validator — see scripts/validate_palette.js. Single hue for the by-type chart (each
// bar is already identified by its axis label, so color doesn't need to carry identity
// there); a validated categorical pair for the two-series credits/debits chart.
const SINGLE_SERIES_HUE = '#d946ef' // matches the app's brand-500 accent
const CREDIT_COLOR = '#3987e5'
const DEBIT_COLOR = '#d95926'
const GRID_COLOR = '#2c2c2a'
const AXIS_COLOR = '#898781'

const TYPE_LABELS: Record<TransactionType, string> = {
  deposit: 'Deposit',
  withdraw: 'Withdraw',
  transfer_in: 'Transfer in',
  transfer_out: 'Transfer out',
  loan_disbursement: 'Loan disbursement',
}

function formatMonth(month: string): string {
  const [year, m] = month.split('-')
  const d = new Date(Number(year), Number(m) - 1, 1)
  return d.toLocaleDateString('en-US', { month: 'short', year: 'numeric' })
}

function ChartTooltip({ active, payload, label }: TooltipContentProps<TooltipValueType, string | number>) {
  if (!active || !payload || payload.length === 0) return null
  return (
    <div className="rounded-md border border-zinc-700 bg-zinc-900 px-3 py-2 text-xs shadow-lg">
      {label !== undefined && <p className="mb-1 font-medium text-zinc-300">{label}</p>}
      {payload.map((entry) => (
        <p key={entry.name} className="flex items-center gap-2">
          <span className="inline-block h-2 w-2 rounded-full" style={{ backgroundColor: entry.color }} />
          <span className="font-semibold text-zinc-100">{formatCents(Number(entry.value ?? 0))}</span>
          <span className="text-zinc-500">{entry.name}</span>
        </p>
      ))}
    </div>
  )
}

interface FilterFormState {
  accountId: string
  startDate: string
  endDate: string
}

const emptyFilters: FilterFormState = { accountId: '', startDate: '', endDate: '' }

export default function Analytics() {
  const [accounts, setAccounts] = useState<Account[]>([])
  const [filters, setFilters] = useState<FilterFormState>(emptyFilters)
  const [appliedFilters, setAppliedFilters] = useState<FilterFormState>(emptyFilters)

  const [summary, setSummary] = useState<AnalyticsSummary | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    void accountsApi.list().then(setAccounts).catch(() => undefined)
  }, [])

  useEffect(() => {
    async function load() {
      setIsLoading(true)
      setError(null)
      try {
        const data = await analyticsApi.getSummary({
          account_id: appliedFilters.accountId || undefined,
          start_date: appliedFilters.startDate ? new Date(appliedFilters.startDate).toISOString() : undefined,
          end_date: appliedFilters.endDate ? new Date(appliedFilters.endDate).toISOString() : undefined,
        })
        setSummary(data)
      } catch (err) {
        setError(getErrorMessage(err, 'Could not load analytics.'))
      } finally {
        setIsLoading(false)
      }
    }
    void load()
  }, [appliedFilters])

  function handleApplyFilters(e: FormEvent) {
    e.preventDefault()
    setAppliedFilters(filters)
  }

  function handleResetFilters() {
    setFilters(emptyFilters)
    setAppliedFilters(emptyFilters)
  }

  const byTypeData = summary
    ? [...summary.by_type]
        .sort((a, b) => b.total_cents - a.total_cents)
        .map((t) => ({ ...t, label: TYPE_LABELS[t.type] ?? t.type }))
    : []

  const byMonthData = summary
    ? summary.by_month.map((m) => ({ ...m, label: formatMonth(m.month) }))
    : []

  return (
    <Layout>
      <h1 className="mb-6 text-2xl font-bold text-zinc-100">Spending analytics</h1>

      {/* One filter row, above everything it scopes — every chart/stat below re-renders against this same slice. */}
      <div className="card mb-6">
        <form onSubmit={handleApplyFilters} className="grid grid-cols-1 gap-4 sm:grid-cols-4 sm:items-end">
          <div>
            <label htmlFor="accountId" className="label">
              Account
            </label>
            <select
              id="accountId"
              className="input"
              value={filters.accountId}
              onChange={(e) => setFilters((f) => ({ ...f, accountId: e.target.value }))}
            >
              <option value="">All accounts</option>
              {accounts.map((a) => (
                <option key={a.id} value={a.id}>
                  {a.account_type} · #{a.account_number}
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
          <div className="flex gap-2">
            <button type="submit" className="btn-primary">
              Apply
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

      {isLoading && !summary ? (
        <p className="text-sm text-zinc-400">Loading…</p>
      ) : summary ? (
        <div className={isLoading ? 'opacity-60 transition-opacity' : 'transition-opacity'}>
          <div className="mb-6 grid grid-cols-1 gap-4 sm:grid-cols-3">
            <div className="card">
              <p className="text-xs uppercase tracking-wide text-zinc-500">Total credits</p>
              <p className="mt-1 text-2xl font-bold text-zinc-100">{formatCents(summary.total_credits_cents)}</p>
            </div>
            <div className="card">
              <p className="text-xs uppercase tracking-wide text-zinc-500">Total debits</p>
              <p className="mt-1 text-2xl font-bold text-zinc-100">{formatCents(summary.total_debits_cents)}</p>
            </div>
            <div className="card">
              <p className="text-xs uppercase tracking-wide text-zinc-500">Net</p>
              <p className={`mt-1 text-2xl font-bold ${summary.net_cents >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                {formatCents(summary.net_cents)}
              </p>
            </div>
          </div>

          <div className="card mb-6">
            <h2 className="mb-4 text-lg font-semibold text-zinc-100">By transaction type</h2>
            {byTypeData.length === 0 ? (
              <p className="text-sm text-zinc-400">No transactions in this range.</p>
            ) : (
              <>
                <ResponsiveContainer width="100%" height={Math.max(160, byTypeData.length * 44 + 40)}>
                  <BarChart data={byTypeData} layout="vertical" margin={{ left: 8, right: 24 }}>
                    <CartesianGrid horizontal={false} stroke={GRID_COLOR} strokeDasharray="0" />
                    <XAxis
                      type="number"
                      tickFormatter={(v: number) => formatCents(v)}
                      stroke={AXIS_COLOR}
                      tick={{ fill: AXIS_COLOR, fontSize: 12 }}
                    />
                    <YAxis
                      type="category"
                      dataKey="label"
                      width={140}
                      stroke={AXIS_COLOR}
                      tick={{ fill: AXIS_COLOR, fontSize: 12 }}
                    />
                    <Tooltip content={ChartTooltip} cursor={{ fill: 'rgba(255,255,255,0.04)' }} />
                    <Bar dataKey="total_cents" name="Total" fill={SINGLE_SERIES_HUE} radius={[0, 4, 4, 0]} maxBarSize={24} />
                  </BarChart>
                </ResponsiveContainer>

                <div className="mt-4 overflow-x-auto">
                  <table className="min-w-full divide-y divide-zinc-800 text-sm">
                    <thead>
                      <tr className="text-left text-xs uppercase tracking-wide text-zinc-500">
                        <th className="py-2 pr-4">Type</th>
                        <th className="py-2 pr-4">Total</th>
                        <th className="py-2 pr-4">Count</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-zinc-800">
                      {byTypeData.map((t) => (
                        <tr key={t.type}>
                          <td className="py-2 pr-4 text-zinc-300">{t.label}</td>
                          <td className="py-2 pr-4 text-zinc-300">{formatCents(t.total_cents)}</td>
                          <td className="py-2 pr-4 text-zinc-500">{t.count}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </>
            )}
          </div>

          <div className="card">
            <h2 className="mb-4 text-lg font-semibold text-zinc-100">Credits vs. debits by month</h2>
            {byMonthData.length === 0 ? (
              <p className="text-sm text-zinc-400">No transactions in this range.</p>
            ) : (
              <>
                <ResponsiveContainer width="100%" height={280}>
                  <BarChart data={byMonthData} margin={{ top: 8 }} barGap={2}>
                    <CartesianGrid vertical={false} stroke={GRID_COLOR} strokeDasharray="0" />
                    <XAxis dataKey="label" stroke={AXIS_COLOR} tick={{ fill: AXIS_COLOR, fontSize: 12 }} />
                    <YAxis
                      tickFormatter={(v: number) => formatCents(v)}
                      stroke={AXIS_COLOR}
                      tick={{ fill: AXIS_COLOR, fontSize: 12 }}
                    />
                    <Tooltip content={ChartTooltip} cursor={{ fill: 'rgba(255,255,255,0.04)' }} />
                    <Legend wrapperStyle={{ fontSize: 12, color: AXIS_COLOR }} />
                    <Bar dataKey="credits_cents" name="Credits" fill={CREDIT_COLOR} radius={[4, 4, 0, 0]} maxBarSize={24} />
                    <Bar dataKey="debits_cents" name="Debits" fill={DEBIT_COLOR} radius={[4, 4, 0, 0]} maxBarSize={24} />
                  </BarChart>
                </ResponsiveContainer>

                <div className="mt-4 overflow-x-auto">
                  <table className="min-w-full divide-y divide-zinc-800 text-sm">
                    <thead>
                      <tr className="text-left text-xs uppercase tracking-wide text-zinc-500">
                        <th className="py-2 pr-4">Month</th>
                        <th className="py-2 pr-4">Credits</th>
                        <th className="py-2 pr-4">Debits</th>
                        <th className="py-2 pr-4">Net</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-zinc-800">
                      {byMonthData.map((m) => (
                        <tr key={m.month}>
                          <td className="py-2 pr-4 text-zinc-300">{m.label}</td>
                          <td className="py-2 pr-4 text-zinc-300">{formatCents(m.credits_cents)}</td>
                          <td className="py-2 pr-4 text-zinc-300">{formatCents(m.debits_cents)}</td>
                          <td className={`py-2 pr-4 ${m.net_cents >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                            {formatCents(m.net_cents)}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </>
            )}
          </div>
        </div>
      ) : null}
    </Layout>
  )
}
