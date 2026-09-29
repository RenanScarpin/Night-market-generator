import type { GmChoiceBehavior, MarketMode } from '../../types/api'
import type { RecentMarket } from '../../types/history'

const SETTINGS_KEY = 'nightmarket.generator-settings.v1'
const RECENTS_KEY = 'nightmarket.recent-markets.v1'
const MAX_RECENT_MARKETS = 12

export interface StoredGeneratorSettings {
  mode: MarketMode
  gmChoice: GmChoiceBehavior
}

const DEFAULT_SETTINGS: StoredGeneratorSettings = {
  mode: 'expanded_2045',
  gmChoice: 'random',
}

function canUseStorage(): boolean {
  return typeof window !== 'undefined' && typeof window.localStorage !== 'undefined'
}

export function loadGeneratorSettings(): StoredGeneratorSettings {
  if (!canUseStorage()) return DEFAULT_SETTINGS

  try {
    const raw = window.localStorage.getItem(SETTINGS_KEY)
    if (!raw) return DEFAULT_SETTINGS

    const parsed = JSON.parse(raw) as Partial<StoredGeneratorSettings>
    return {
      mode: parsed.mode === 'core_raw' ? 'core_raw' : 'expanded_2045',
      gmChoice: parsed.gmChoice === 'leave' ? 'leave' : 'random',
    }
  } catch {
    return DEFAULT_SETTINGS
  }
}

export function saveGeneratorSettings(settings: StoredGeneratorSettings) {
  if (!canUseStorage()) return
  window.localStorage.setItem(SETTINGS_KEY, JSON.stringify(settings))
}

export function loadRecentMarkets(): RecentMarket[] {
  if (!canUseStorage()) return []

  try {
    const raw = window.localStorage.getItem(RECENTS_KEY)
    if (!raw) return []

    const parsed = JSON.parse(raw)
    if (!Array.isArray(parsed)) return []

    return parsed
      .filter((entry): entry is RecentMarket => {
        return (
          typeof entry === 'object' &&
          entry !== null &&
          Number.isSafeInteger(entry.seed) &&
          entry.seed >= 0 &&
          (entry.mode === 'core_raw' || entry.mode === 'expanded_2045') &&
          (entry.gmChoice === 'random' || entry.gmChoice === 'leave') &&
          Array.isArray(entry.categoryNames) &&
          entry.categoryNames.every((name: unknown) => typeof name === 'string') &&
          typeof entry.generatedAt === 'string'
        )
      })
      .slice(0, MAX_RECENT_MARKETS)
  } catch {
    return []
  }
}

function persistRecentMarkets(markets: RecentMarket[]) {
  if (!canUseStorage()) return
  window.localStorage.setItem(RECENTS_KEY, JSON.stringify(markets.slice(0, MAX_RECENT_MARKETS)))
}

export function addRecentMarket(market: RecentMarket): RecentMarket[] {
  const current = loadRecentMarkets()
  const key = recentMarketKey(market)
  const next = [
    market,
    ...current.filter((entry) => recentMarketKey(entry) !== key),
  ].slice(0, MAX_RECENT_MARKETS)

  persistRecentMarkets(next)
  return next
}

export function removeRecentMarket(target: RecentMarket): RecentMarket[] {
  const key = recentMarketKey(target)
  const next = loadRecentMarkets().filter((entry) => recentMarketKey(entry) !== key)
  persistRecentMarkets(next)
  return next
}

export function clearRecentMarkets(): RecentMarket[] {
  persistRecentMarkets([])
  return []
}

export function recentMarketKey(market: Pick<RecentMarket, 'seed' | 'mode' | 'gmChoice'>): string {
  return `${market.mode}:${market.seed}:${market.gmChoice}`
}
