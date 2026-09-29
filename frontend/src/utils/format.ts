export function titleCase(value: string): string {
  return value
    .replace(/[._-]+/g, ' ')
    .replace(/\b\w/g, (letter) => letter.toUpperCase())
}

export function priceCategoryFromText(price: string): string | null {
  const match = price.match(/\(([^)]+)\)\s*$/)
  return match?.[1] ?? null
}

export function priceAmountFromText(price: string): string {
  return price.replace(/\s*\([^)]+\)\s*$/, '')
}

export function compactSource(code: string | null, page: number | null): string | null {
  if (!code) return null
  return page ? `${code} p. ${page}` : code
}
