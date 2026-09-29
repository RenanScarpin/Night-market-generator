export interface CatalogueFilters {
  q: string
  category: string
  tag: string
  manufacturer: string
  minCost: string
  maxCost: string
  page: number
}

export const EMPTY_CATALOGUE_FILTERS: CatalogueFilters = {
  q: '',
  category: '',
  tag: '',
  manufacturer: '',
  minCost: '',
  maxCost: '',
  page: 1,
}

export function parseCatalogueSearch(search: string): CatalogueFilters {
  const params = new URLSearchParams(search)
  const rawPage = Number(params.get('page') ?? '1')
  return {
    q: params.get('q') ?? '',
    category: params.get('category') ?? '',
    tag: params.get('tag') ?? '',
    manufacturer: params.get('manufacturer') ?? '',
    minCost: params.get('minCost') ?? '',
    maxCost: params.get('maxCost') ?? '',
    page: Number.isInteger(rawPage) && rawPage > 0 ? rawPage : 1,
  }
}

export function buildCataloguePath(filters: CatalogueFilters): string {
  const params = new URLSearchParams()
  if (filters.q.trim()) params.set('q', filters.q.trim())
  if (filters.category) params.set('category', filters.category)
  if (filters.tag) params.set('tag', filters.tag)
  if (filters.manufacturer) params.set('manufacturer', filters.manufacturer)
  if (filters.minCost.trim()) params.set('minCost', filters.minCost.trim())
  if (filters.maxCost.trim()) params.set('maxCost', filters.maxCost.trim())
  if (filters.page > 1) params.set('page', String(filters.page))
  const query = params.toString()
  return query ? `/catalogue?${query}` : '/catalogue'
}
