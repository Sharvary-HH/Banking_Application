import { useEffect, useState, type FormEvent } from 'react'
import { accountsApi } from '../api/accounts'
import { getErrorMessage } from '../api/errorMessage'
import { adminLoansApi, loansApi } from '../api/loans'
import type { Account, AdminLoan, EmiCalculationResponse, Loan, LoanStatus } from '../api/types'
import Alert from '../components/Alert'
import Layout from '../components/Layout'
import { useAuth } from '../context/AuthContext'
import { dollarsToCents, formatCents, formatDate } from '../utils/money'

const STATUS_STYLES: Record<LoanStatus, string> = {
  pending: 'text-yellow-400',
  approved: 'text-green-400',
  rejected: 'text-red-400',
}

export default function Loans() {
  const { user } = useAuth()
  const isAdmin = user?.role === 'admin'

  const [accounts, setAccounts] = useState<Account[]>([])
  const [principal, setPrincipal] = useState('')
  const [ratePercent, setRatePercent] = useState('')
  const [termMonths, setTermMonths] = useState('')
  const [disbursementAccountId, setDisbursementAccountId] = useState('')

  const [calcResult, setCalcResult] = useState<EmiCalculationResponse | null>(null)
  const [calcError, setCalcError] = useState<string | null>(null)
  const [isCalculating, setIsCalculating] = useState(false)

  const [applyError, setApplyError] = useState<string | null>(null)
  const [applySuccess, setApplySuccess] = useState<string | null>(null)
  const [isApplying, setIsApplying] = useState(false)

  const [myLoans, setMyLoans] = useState<Loan[]>([])
  const [isLoadingLoans, setIsLoadingLoans] = useState(true)

  const [pendingLoans, setPendingLoans] = useState<AdminLoan[]>([])
  const [adminError, setAdminError] = useState<string | null>(null)
  const [decidingId, setDecidingId] = useState<string | null>(null)

  function parsedInputs(): { principal_cents: number; annual_interest_rate_bps: number; term_months: number } | null {
    const principal_cents = dollarsToCents(principal)
    const rate = Number(ratePercent)
    const term_months = Number(termMonths)
    if (principal_cents === null || principal_cents <= 0) return null
    if (!Number.isFinite(rate) || rate < 0) return null
    if (!Number.isInteger(term_months) || term_months <= 0) return null
    return { principal_cents, annual_interest_rate_bps: Math.round(rate * 100), term_months }
  }

  async function loadMyLoans() {
    setIsLoadingLoans(true)
    try {
      setMyLoans(await loansApi.list())
    } catch {
      // Non-fatal — the calculator/apply form still works.
    } finally {
      setIsLoadingLoans(false)
    }
  }

  async function loadPendingLoans() {
    try {
      setPendingLoans(await adminLoansApi.listPending())
    } catch (err) {
      setAdminError(getErrorMessage(err, 'Could not load pending loan applications.'))
    }
  }

  useEffect(() => {
    void accountsApi.list().then(setAccounts).catch(() => undefined)
    void loadMyLoans()
    if (isAdmin) void loadPendingLoans()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isAdmin])

  async function handleCalculate(e: FormEvent) {
    e.preventDefault()
    setCalcError(null)
    const inputs = parsedInputs()
    if (!inputs) {
      setCalcError('Enter a valid principal, rate, and term.')
      return
    }
    setIsCalculating(true)
    try {
      setCalcResult(await loansApi.calculateEmi(inputs))
    } catch (err) {
      setCalcError(getErrorMessage(err, 'Could not calculate EMI.'))
    } finally {
      setIsCalculating(false)
    }
  }

  async function handleApply(e: FormEvent) {
    e.preventDefault()
    setApplyError(null)
    setApplySuccess(null)
    const inputs = parsedInputs()
    if (!inputs) {
      setApplyError('Enter a valid principal, rate, and term.')
      return
    }
    if (!disbursementAccountId) {
      setApplyError('Choose an account to receive the funds if approved.')
      return
    }
    setIsApplying(true)
    try {
      await loansApi.apply({ ...inputs, disbursement_account_id: disbursementAccountId })
      setApplySuccess('Loan application submitted — status: pending.')
      await loadMyLoans()
    } catch (err) {
      setApplyError(getErrorMessage(err, 'Could not submit loan application.'))
    } finally {
      setIsApplying(false)
    }
  }

  async function handleDecision(loanId: string, decision: 'approve' | 'reject') {
    setDecidingId(loanId)
    setAdminError(null)
    try {
      if (decision === 'approve') {
        await adminLoansApi.approve(loanId)
      } else {
        await adminLoansApi.reject(loanId)
      }
      await loadPendingLoans()
      await loadMyLoans()
    } catch (err) {
      setAdminError(getErrorMessage(err, 'Could not record decision.'))
    } finally {
      setDecidingId(null)
    }
  }

  return (
    <Layout>
      <h1 className="mb-6 text-2xl font-bold text-zinc-100">Loans</h1>

      <div className="card mb-6">
        <h2 className="mb-4 text-lg font-semibold text-zinc-100">EMI calculator &amp; application</h2>
        <form className="grid grid-cols-1 gap-4 sm:grid-cols-3">
          <div>
            <label htmlFor="principal" className="label">
              Principal (USD)
            </label>
            <input
              id="principal"
              type="text"
              inputMode="decimal"
              className="input"
              placeholder="10000.00"
              value={principal}
              onChange={(e) => setPrincipal(e.target.value)}
            />
          </div>
          <div>
            <label htmlFor="rate" className="label">
              Annual interest rate (%)
            </label>
            <input
              id="rate"
              type="text"
              inputMode="decimal"
              className="input"
              placeholder="12"
              value={ratePercent}
              onChange={(e) => setRatePercent(e.target.value)}
            />
          </div>
          <div>
            <label htmlFor="term" className="label">
              Term (months)
            </label>
            <input
              id="term"
              type="text"
              inputMode="numeric"
              className="input"
              placeholder="12"
              value={termMonths}
              onChange={(e) => setTermMonths(e.target.value)}
            />
          </div>
        </form>

        <div className="mt-4 flex flex-wrap gap-2">
          <button type="button" className="btn-secondary" disabled={isCalculating} onClick={handleCalculate}>
            {isCalculating ? 'Calculating…' : 'Calculate EMI'}
          </button>
        </div>

        {calcError && (
          <div className="mt-4">
            <Alert variant="error">{calcError}</Alert>
          </div>
        )}

        {calcResult && (
          <div className="mt-4 grid grid-cols-1 gap-4 rounded-md border border-zinc-800 bg-zinc-950 p-4 sm:grid-cols-3">
            <div>
              <p className="text-xs uppercase tracking-wide text-zinc-500">Monthly EMI</p>
              <p className="text-lg font-semibold text-zinc-100">{formatCents(calcResult.emi_cents)}</p>
            </div>
            <div>
              <p className="text-xs uppercase tracking-wide text-zinc-500">Total payment</p>
              <p className="text-lg font-semibold text-zinc-100">{formatCents(calcResult.total_payment_cents)}</p>
            </div>
            <div>
              <p className="text-xs uppercase tracking-wide text-zinc-500">Total interest</p>
              <p className="text-lg font-semibold text-zinc-100">{formatCents(calcResult.total_interest_cents)}</p>
            </div>
          </div>
        )}

        <form onSubmit={handleApply} className="mt-6 space-y-4 border-t border-zinc-800 pt-6">
          <div>
            <label htmlFor="disbursementAccount" className="label">
              Disburse funds to (if approved)
            </label>
            <select
              id="disbursementAccount"
              className="input"
              value={disbursementAccountId}
              onChange={(e) => setDisbursementAccountId(e.target.value)}
              disabled={accounts.length === 0}
            >
              <option value="">{accounts.length === 0 ? 'No accounts available' : 'Select an account…'}</option>
              {accounts.map((a) => (
                <option key={a.id} value={a.id}>
                  {a.account_type} · #{a.account_number}
                </option>
              ))}
            </select>
          </div>
          {applyError && <Alert variant="error">{applyError}</Alert>}
          {applySuccess && <Alert variant="success">{applySuccess}</Alert>}
          <button type="submit" disabled={isApplying} className="btn-primary w-full">
            {isApplying ? 'Submitting…' : 'Apply for this loan'}
          </button>
        </form>
      </div>

      <h2 className="mb-4 text-lg font-semibold text-zinc-100">My loans</h2>
      {isLoadingLoans ? (
        <p className="text-sm text-zinc-400">Loading…</p>
      ) : myLoans.length === 0 ? (
        <div className="card mb-6 text-center text-sm text-zinc-400">No loan applications yet.</div>
      ) : (
        <div className="card mb-6 overflow-x-auto">
          <table className="min-w-full divide-y divide-zinc-800 text-sm">
            <thead>
              <tr className="text-left text-xs uppercase tracking-wide text-zinc-500">
                <th className="py-2 pr-4">Principal</th>
                <th className="py-2 pr-4">Rate</th>
                <th className="py-2 pr-4">Term</th>
                <th className="py-2 pr-4">EMI</th>
                <th className="py-2 pr-4">Status</th>
                <th className="py-2 pr-4">Applied</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-zinc-800">
              {myLoans.map((loan) => (
                <tr key={loan.id}>
                  <td className="py-2 pr-4 whitespace-nowrap text-zinc-300">{formatCents(loan.principal_cents)}</td>
                  <td className="py-2 pr-4 whitespace-nowrap text-zinc-300">
                    {(loan.annual_interest_rate_bps / 100).toFixed(2)}%
                  </td>
                  <td className="py-2 pr-4 whitespace-nowrap text-zinc-300">{loan.term_months}mo</td>
                  <td className="py-2 pr-4 whitespace-nowrap text-zinc-300">{formatCents(loan.emi_cents)}</td>
                  <td className={`py-2 pr-4 whitespace-nowrap font-medium capitalize ${STATUS_STYLES[loan.status]}`}>
                    {loan.status}
                  </td>
                  <td className="py-2 pr-4 whitespace-nowrap text-zinc-500">{formatDate(loan.created_at)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {isAdmin && (
        <>
          <h2 className="mb-4 text-lg font-semibold text-zinc-100">Pending applications (admin)</h2>
          {adminError && (
            <div className="mb-4">
              <Alert variant="error">{adminError}</Alert>
            </div>
          )}
          {pendingLoans.length === 0 ? (
            <div className="card text-center text-sm text-zinc-400">No pending applications.</div>
          ) : (
            <div className="card overflow-x-auto">
              <table className="min-w-full divide-y divide-zinc-800 text-sm">
                <thead>
                  <tr className="text-left text-xs uppercase tracking-wide text-zinc-500">
                    <th className="py-2 pr-4">Applicant</th>
                    <th className="py-2 pr-4">Principal</th>
                    <th className="py-2 pr-4">Rate</th>
                    <th className="py-2 pr-4">Term</th>
                    <th className="py-2 pr-4">EMI</th>
                    <th className="py-2 pr-4" />
                  </tr>
                </thead>
                <tbody className="divide-y divide-zinc-800">
                  {pendingLoans.map((loan) => (
                    <tr key={loan.id}>
                      <td className="py-2 pr-4 whitespace-nowrap text-zinc-300">{loan.applicant_email}</td>
                      <td className="py-2 pr-4 whitespace-nowrap text-zinc-300">{formatCents(loan.principal_cents)}</td>
                      <td className="py-2 pr-4 whitespace-nowrap text-zinc-300">
                        {(loan.annual_interest_rate_bps / 100).toFixed(2)}%
                      </td>
                      <td className="py-2 pr-4 whitespace-nowrap text-zinc-300">{loan.term_months}mo</td>
                      <td className="py-2 pr-4 whitespace-nowrap text-zinc-300">{formatCents(loan.emi_cents)}</td>
                      <td className="py-2 pr-4 whitespace-nowrap">
                        <div className="flex gap-2">
                          <button
                            type="button"
                            className="btn-secondary"
                            disabled={decidingId === loan.id}
                            onClick={() => void handleDecision(loan.id, 'approve')}
                          >
                            Approve
                          </button>
                          <button
                            type="button"
                            className="btn-secondary"
                            disabled={decidingId === loan.id}
                            onClick={() => void handleDecision(loan.id, 'reject')}
                          >
                            Reject
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </>
      )}
    </Layout>
  )
}
