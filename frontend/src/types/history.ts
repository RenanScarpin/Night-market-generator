import type { GmChoiceBehavior, MarketMode } from './api'

export interface RecentMarket {
  seed: number
  mode: MarketMode
  gmChoice: GmChoiceBehavior
  categoryNames: string[]
  generatedAt: string
}
