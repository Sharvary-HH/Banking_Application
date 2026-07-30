import { apiClient } from './client'
import type { CreateScheduledTransferRequest, ScheduledTransfer } from './types'

export const scheduledTransfersApi = {
  async list(): Promise<ScheduledTransfer[]> {
    const { data } = await apiClient.get<ScheduledTransfer[]>('/scheduled-transfers')
    return data
  },

  async create(payload: CreateScheduledTransferRequest): Promise<ScheduledTransfer> {
    const { data } = await apiClient.post<ScheduledTransfer>('/scheduled-transfers', payload)
    return data
  },

  async cancel(scheduledTransferId: string): Promise<ScheduledTransfer> {
    const { data } = await apiClient.post<ScheduledTransfer>(`/scheduled-transfers/${scheduledTransferId}/cancel`)
    return data
  },
}
