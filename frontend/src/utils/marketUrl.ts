import type { GmChoiceBehavior, MarketMode } from '../types/api'

export interface MarketRouteParams {
  seed: number
  mode: MarketMode
  gmChoice: GmChoiceBehavior
}

export interface ParsedMarketRoute {
  seed: number | null
  mode: MarketMode | null
  gmChoice: GmChoiceBehavior | null
  error: string | null
}

export function buildMarketPath(params: MarketRouteParams): string {
  const search = new URLSearchParams({
    seed: String(params.seed),
    mode: params.mode,
    gmChoice: params.gmChoice,
  })
  return `/market?${search.toString()}`
}

export function parseMarketSearch(search: string): ParsedMarketRoute {
  const params = new URLSearchParams(search)
  const rawSeed = params.get('seed')
  const rawMode = params.get('mode')
  const rawChoice = params.get('gmChoice')

  let seed: number | null = null
  if (rawSeed !== null && rawSeed !== '') {
    const numeric = Number(rawSeed)
    if (!Number.isSafeInteger(numeric) || numeric < 0) {
      return {
        seed: null,
        mode: null,
        gmChoice: null,
        error: 'The market URL contains an invalid seed.',
      }
    }
    seed = numeric
  }

  let mode: MarketMode | null = null
  if (rawMode !== null) {
    if (rawMode !== 'core_raw' && rawMode !== 'expanded_2045') {
      return {
        seed,
        mode: null,
        gmChoice: null,
        error: 'The market URL contains an unknown generation mode.',
      }
    }
    mode = rawMode
  }

  let gmChoice: GmChoiceBehavior | null = null
  if (rawChoice !== null) {
    if (rawChoice !== 'random' && rawChoice !== 'leave') {
      return {
        seed,
        mode,
        gmChoice: null,
        error: 'The market URL contains an unknown GM-choice behavior.',
      }
    }
    gmChoice = rawChoice
  }

  return { seed, mode, gmChoice, error: null }
}
