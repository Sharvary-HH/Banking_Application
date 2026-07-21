const currencyFormatter = new Intl.NumberFormat('en-US', {
  style: 'currency',
  currency: 'USD',
})

/** Formats integer cents (e.g. 150000) as a dollar string (e.g. "$1,500.00"). */
export function formatCents(cents: number): string {
  return currencyFormatter.format(cents / 100)
}

/**
 * Parses a user-entered dollar amount string (e.g. "12.5") into integer cents.
 * Returns null if the input isn't a valid non-negative amount.
 */
export function dollarsToCents(value: string): number | null {
  const trimmed = value.trim()
  if (trimmed === '') return null
  if (!/^\d+(\.\d{1,2})?$/.test(trimmed)) return null
  const [wholePart, fractionPart = ''] = trimmed.split('.')
  const cents = Number(wholePart) * 100 + Number(fractionPart.padEnd(2, '0'))
  return Number.isFinite(cents) ? cents : null
}

export function formatDate(iso: string): string {
  const d = new Date(iso)
  if (Number.isNaN(d.getTime())) return iso
  return d.toLocaleString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  })
}
