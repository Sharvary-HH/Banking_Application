import { apiClient } from './client'
import type { AnalyticsSummary, AnalyticsSummaryParams } from './types'

export const analyticsApi = {
  async getSummary(params: AnalyticsSummaryParams): Promise<AnalyticsSummary> {
    const { data } = await apiClient.get<AnalyticsSummary>('/analytics/summary', { params })
    return data
  },
}
