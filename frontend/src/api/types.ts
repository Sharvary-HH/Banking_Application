// Shared types matching the fixed backend API contract.
// All money amounts over the wire are integer cents.

export type Role = 'customer' | 'admin'

export interface User {
  id: string
  email: string
  role: Role
  totp_enabled: boolean
}

export interface RegisterRequest {
  email: string
  password: string
}

export interface RegisterResponse {
  id: string
  email: string
  role: Role
}

export interface LoginRequest {
  email: string
  password: string
}

export interface TokenResponse {
  access_token: string
  refresh_token: string
  token_type: 'bearer'
}

export interface TwoFaRequiredResponse {
  two_fa_required: true
  two_fa_token: string
}

export type LoginResponse = TokenResponse | TwoFaRequiredResponse

export interface Verify2FaRequest {
  two_fa_token: string
  code: string
}

export interface RefreshRequest {
  refresh_token: string
}

export interface Setup2FaResponse {
  secret: string
  qr_code_base64: string
  otpauth_url: string
}

export interface Enable2FaRequest {
  code: string
}

export interface Enable2FaResponse {
  enabled: true
}

export type AccountType = 'savings' | 'checking'

export interface Account {
  id: string
  account_number: string
  account_type: AccountType
  balance_cents: number
  created_at: string
}

export interface CreateAccountRequest {
  account_type: AccountType
}

export type TransactionType = 'deposit' | 'withdraw' | 'transfer_in' | 'transfer_out' | 'loan_disbursement'

export interface TransactionOut {
  id: string
  account_id: string
  related_account_id: string | null
  type: TransactionType
  amount_cents: number
  balance_after_cents: number
  reference_id: string | null
  description: string | null
  created_at: string
}

export interface DepositWithdrawRequest {
  amount_cents: number
  description?: string
}

export interface TransferRequest {
  from_account_id: string
  to_account_id: string
  amount_cents: number
  description?: string
}

export interface TransferResponse {
  debit: TransactionOut
  credit: TransactionOut
}

export interface TransactionListParams {
  type?: TransactionType
  start_date?: string
  end_date?: string
  min_amount_cents?: number
  max_amount_cents?: number
  page?: number
  page_size?: number
}

export interface TransactionListResponse {
  items: TransactionOut[]
  total: number
  page: number
  page_size: number
}

export interface ApiErrorBody {
  detail?: string | Record<string, unknown> | Array<unknown>
}

export interface AccountLookup {
  id: string
  account_number: string
  account_type: AccountType
}

export interface Beneficiary {
  id: string
  nickname: string
  account_id: string
  account_number: string
  created_at: string
}

export interface CreateBeneficiaryRequest {
  nickname: string
  account_id: string
}

export type TransferFrequency = 'once' | 'daily' | 'weekly' | 'monthly'

export interface ScheduledTransfer {
  id: string
  from_account_id: string
  to_account_id: string
  amount_cents: number
  description: string | null
  frequency: TransferFrequency
  next_run_at: string
  end_date: string | null
  is_active: boolean
  last_run_at: string | null
  last_run_status: 'success' | 'failed' | null
  created_at: string
}

export interface CreateScheduledTransferRequest {
  from_account_id: string
  to_account_id: string
  amount_cents: number
  description?: string
  frequency: TransferFrequency
  start_at?: string
  end_date?: string
}

export interface EmiCalculationRequest {
  principal_cents: number
  annual_interest_rate_bps: number
  term_months: number
}

export interface EmiCalculationResponse {
  emi_cents: number
  total_payment_cents: number
  total_interest_cents: number
}

export interface LoanApplyRequest extends EmiCalculationRequest {
  disbursement_account_id: string
}

export type LoanStatus = 'pending' | 'approved' | 'rejected'

export interface Loan {
  id: string
  disbursement_account_id: string
  principal_cents: number
  annual_interest_rate_bps: number
  term_months: number
  emi_cents: number
  status: LoanStatus
  decided_at: string | null
  created_at: string
}

export interface AdminLoan extends Loan {
  user_id: string
  applicant_email: string
}

export interface TypeBreakdown {
  type: TransactionType
  total_cents: number
  count: number
}

export interface MonthlyBreakdown {
  month: string // "YYYY-MM"
  credits_cents: number
  debits_cents: number
  net_cents: number
}

export interface AnalyticsSummary {
  start_date: string | null
  end_date: string | null
  total_credits_cents: number
  total_debits_cents: number
  net_cents: number
  by_type: TypeBreakdown[]
  by_month: MonthlyBreakdown[]
}

export interface AnalyticsSummaryParams {
  account_id?: string
  start_date?: string
  end_date?: string
}
