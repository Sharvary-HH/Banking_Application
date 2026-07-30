import axios from 'axios'
import type { ApiErrorBody } from './types'

/**
 * Extracts a human-readable error message from an unknown error, honoring
 * the backend's FastAPI default error shape: { detail: string | object }.
 */
export function getErrorMessage(err: unknown, fallback = 'Something went wrong. Please try again.'): string {
  if (axios.isAxiosError<ApiErrorBody>(err)) {
    const detail = err.response?.data?.detail
    if (typeof detail === 'string') {
      return detail
    }
    if (detail !== undefined && detail !== null) {
      try {
        return JSON.stringify(detail)
      } catch {
        return fallback
      }
    }
    if (err.message) {
      return err.message
    }
  }
  if (err instanceof Error) {
    return err.message
  }
  return fallback
}
