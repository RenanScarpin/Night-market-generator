import type {
  ApiErrorBody,
  GmChoiceBehavior,
  CategoryDetail,
  ItemDetail,
  ManufacturerSummary,
  MarketTagDetail,
  PaginatedItems,
  MarketGenerateRequest,
  MarketMode,
  NightMarket,
} from '../types/api'

const API_BASE = (import.meta.env.VITE_API_BASE_URL ?? '').replace(/\/$/, '')

export class ApiError extends Error {
  readonly status: number
  readonly body: unknown

  constructor(message: string, status: number, body: unknown) {
    super(message)
    this.name = 'ApiError'
    this.status = status
    this.body = body
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    ...init,
    headers: {
      Accept: 'application/json',
      ...(init?.body ? { 'Content-Type': 'application/json' } : {}),
      ...init?.headers,
    },
  })

  const body = await response.json().catch(() => null)
  if (!response.ok) {
    const error = body as ApiErrorBody | null
    const detail = typeof error?.detail === 'string' ? error.detail : null
    throw new ApiError(detail ?? `Request failed with status ${response.status}`, response.status, body)
  }

  return body as T
}

export function generateMarket(payload: MarketGenerateRequest): Promise<NightMarket> {
  return request<NightMarket>('/api/markets/generate', {
    method: 'POST',
    body: JSON.stringify(payload),
  })
}

export function getMarket(
  seed: number,
  mode: MarketMode,
  gmChoice: GmChoiceBehavior,
): Promise<NightMarket> {
  const params = new URLSearchParams({
    mode,
    gm_choice: gmChoice,
  })
  return request<NightMarket>(`/api/markets/${seed}?${params.toString()}`)
}

export function getItemDetail(itemId: number): Promise<ItemDetail> {
  return request<ItemDetail>(`/api/items/${itemId}`)
}


export interface ListItemsParams {
  q?: string
  category?: string
  tag?: string
  manufacturer?: string
  itemKind?: string
  minCostEb?: number
  maxCostEb?: number
  limit?: number
  offset?: number
}

export function listItems(params: ListItemsParams = {}): Promise<PaginatedItems> {
  const query = new URLSearchParams()
  if (params.q) query.set('q', params.q)
  if (params.category) query.set('category', params.category)
  if (params.tag) query.set('tag', params.tag)
  if (params.manufacturer) query.set('manufacturer', params.manufacturer)
  if (params.itemKind) query.set('item_kind', params.itemKind)
  if (params.minCostEb !== undefined) query.set('min_cost_eb', String(params.minCostEb))
  if (params.maxCostEb !== undefined) query.set('max_cost_eb', String(params.maxCostEb))
  if (params.limit !== undefined) query.set('limit', String(params.limit))
  if (params.offset !== undefined) query.set('offset', String(params.offset))
  const suffix = query.toString() ? `?${query.toString()}` : ''
  return request<PaginatedItems>(`/api/items${suffix}`)
}

export function getCategories(): Promise<CategoryDetail[]> {
  return request<CategoryDetail[]>('/api/categories')
}

export function getMarketTags(): Promise<MarketTagDetail[]> {
  return request<MarketTagDetail[]>('/api/tags')
}

export function getManufacturers(): Promise<ManufacturerSummary[]> {
  return request<ManufacturerSummary[]>('/api/manufacturers')
}
