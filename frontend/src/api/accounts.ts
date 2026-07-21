import { apiClient } from './client'
import type { Account, AccountLookup, CreateAccountRequest } from './types'

export const accountsApi = {
  async list(): Promise<Account[]> {
    const { data } = await apiClient.get<Account[]>('/accounts')
    return data
  },

  async get(accountId: string): Promise<Account> {
    const { data } = await apiClient.get<Account>(`/accounts/${accountId}`)
    return data
  },

  async create(payload: CreateAccountRequest): Promise<Account> {
    const { data } = await apiClient.post<Account>('/accounts', payload)
    return data
  },

  async lookupByAccountNumber(accountNumber: string): Promise<AccountLookup> {
    const { data } = await apiClient.get<AccountLookup>('/accounts/lookup', {
      params: { account_number: accountNumber },
    })
    return data
  },
}
