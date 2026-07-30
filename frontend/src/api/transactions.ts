import { apiClient } from './client'
import type {
  DepositWithdrawRequest,
  TransactionListParams,
  TransactionListResponse,
  TransactionOut,
  TransferRequest,
  TransferResponse,
} from './types'

export const transactionsApi = {
  async deposit(accountId: string, payload: DepositWithdrawRequest): Promise<TransactionOut> {
    const { data } = await apiClient.post<TransactionOut>(`/accounts/${accountId}/deposit`, payload)
    return data
  },

  async withdraw(accountId: string, payload: DepositWithdrawRequest): Promise<TransactionOut> {
    const { data } = await apiClient.post<TransactionOut>(`/accounts/${accountId}/withdraw`, payload)
    return data
  },

  async transfer(payload: TransferRequest): Promise<TransferResponse> {
    const { data } = await apiClient.post<TransferResponse>('/transfers', payload)
    return data
  },

  async list(accountId: string, params: TransactionListParams): Promise<TransactionListResponse> {
    const { data } = await apiClient.get<TransactionListResponse>(`/accounts/${accountId}/transactions`, {
      params,
    })
    return data
  },
}
