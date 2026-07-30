import { apiClient } from './client'
import type { AdminLoan, EmiCalculationRequest, EmiCalculationResponse, Loan, LoanApplyRequest } from './types'

export const loansApi = {
  async calculateEmi(payload: EmiCalculationRequest): Promise<EmiCalculationResponse> {
    const { data } = await apiClient.post<EmiCalculationResponse>('/loans/calculate-emi', payload)
    return data
  },

  async apply(payload: LoanApplyRequest): Promise<Loan> {
    const { data } = await apiClient.post<Loan>('/loans', payload)
    return data
  },

  async list(): Promise<Loan[]> {
    const { data } = await apiClient.get<Loan[]>('/loans')
    return data
  },
}

export const adminLoansApi = {
  async listPending(): Promise<AdminLoan[]> {
    const { data } = await apiClient.get<AdminLoan[]>('/admin/loans', { params: { status: 'pending' } })
    return data
  },

  async approve(loanId: string): Promise<Loan> {
    const { data } = await apiClient.post<Loan>(`/admin/loans/${loanId}/approve`)
    return data
  },

  async reject(loanId: string): Promise<Loan> {
    const { data } = await apiClient.post<Loan>(`/admin/loans/${loanId}/reject`)
    return data
  },
}
