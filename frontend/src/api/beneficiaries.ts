import { apiClient } from './client'
import type { Beneficiary, CreateBeneficiaryRequest } from './types'

export const beneficiariesApi = {
  async list(): Promise<Beneficiary[]> {
    const { data } = await apiClient.get<Beneficiary[]>('/beneficiaries')
    return data
  },

  async create(payload: CreateBeneficiaryRequest): Promise<Beneficiary> {
    const { data } = await apiClient.post<Beneficiary>('/beneficiaries', payload)
    return data
  },

  async remove(beneficiaryId: string): Promise<void> {
    await apiClient.delete(`/beneficiaries/${beneficiaryId}`)
  },
}
