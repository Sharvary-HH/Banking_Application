import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { getErrorMessage } from '../api/errorMessage'
import { scheduledTransfersApi } from '../api/scheduledTransfers'
import type { ScheduledTransfer } from '../api/types'
import Alert from '../components/Alert'
import Layout from '../components/Layout'
import { formatCents, formatDate } from '../utils/money'

const FREQUENCY_LABELS: Record<string, string> = {
  once: 'Once',
  daily: 'Daily',
  weekly: 'Weekly',
  monthly: 'Monthly',
}

export default function ScheduledTransfers() {
  const [items, setItems] = useState<ScheduledTransfer[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [cancellingId, setCancellingId] = useState<string | null>(null)

  async function load() {
    setIsLoading(true)
    setError(null)
    try {
      const data = await scheduledTransfersApi.list()
      setItems(data)
    } catch (err) {
      setError(getErrorMessage(err, 'Could not load scheduled transfers.'))
    } finally {
      setIsLoading(false)
    }
  }

  useEffect(() => {
    void load()
  }, [])

  async function handleCancel(id: string) {
    setCancellingId(id)
    try {
      await scheduledTransfersApi.cancel(id)
      await load()
    } catch (err) {
      setError(getErrorMessage(err, 'Could not cancel scheduled transfer.'))
    } finally {
      setCancellingId(null)
    }
  }

  return (
    <Layout>
      <div className="mb-6 flex items-center justify-between">
        <h1 className="text-2xl font-bold text-zinc-100">Scheduled transfers</h1>
        <Link to="/dashboard" className="text-sm font-medium text-brand-400 hover:text-brand-300">
          Back to dashboard
        </Link>
      </div>

      <p className="mb-6 text-sm text-zinc-400">
        Recurring and one-off transfers you've scheduled from the "Schedule this transfer" toggle on any account's
        Transfer page.
      </p>

      {error && (
        <div className="mb-4">
          <Alert variant="error">{error}</Alert>
        </div>
      )}

      {isLoading ? (
        <p className="text-sm text-zinc-400">Loading…</p>
      ) : items.length === 0 ? (
        <div className="card text-center text-sm text-zinc-400">No scheduled transfers yet.</div>
      ) : (
        <div className="card overflow-x-auto">
          <table className="min-w-full divide-y divide-zinc-800 text-sm">
            <thead>
              <tr className="text-left text-xs uppercase tracking-wide text-zinc-500">
                <th className="py-2 pr-4">Amount</th>
                <th className="py-2 pr-4">Frequency</th>
                <th className="py-2 pr-4">Next run</th>
                <th className="py-2 pr-4">Last run</th>
                <th className="py-2 pr-4">Status</th>
                <th className="py-2 pr-4" />
              </tr>
            </thead>
            <tbody className="divide-y divide-zinc-800">
              {items.map((s) => (
                <tr key={s.id}>
                  <td className="py-2 pr-4 whitespace-nowrap text-zinc-300">{formatCents(s.amount_cents)}</td>
                  <td className="py-2 pr-4 whitespace-nowrap text-zinc-300">{FREQUENCY_LABELS[s.frequency]}</td>
                  <td className="py-2 pr-4 whitespace-nowrap text-zinc-300">
                    {s.is_active ? formatDate(s.next_run_at) : '—'}
                  </td>
                  <td className="py-2 pr-4 whitespace-nowrap text-zinc-500">
                    {s.last_run_at ? formatDate(s.last_run_at) : 'Never'}
                  </td>
                  <td className="py-2 pr-4 whitespace-nowrap">
                    {!s.is_active ? (
                      <span className="text-zinc-500">Cancelled</span>
                    ) : s.last_run_status === 'failed' ? (
                      <span className="text-red-400">Retrying (last run failed)</span>
                    ) : (
                      <span className="text-green-400">Active</span>
                    )}
                  </td>
                  <td className="py-2 pr-4 whitespace-nowrap">
                    {s.is_active && (
                      <button
                        type="button"
                        className="btn-secondary"
                        disabled={cancellingId === s.id}
                        onClick={() => void handleCancel(s.id)}
                      >
                        {cancellingId === s.id ? 'Cancelling…' : 'Cancel'}
                      </button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </Layout>
  )
}
