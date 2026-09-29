import type { RecentMarket } from '../types/history'
import { buildMarketPath } from '../utils/marketUrl'
import { BrowserLink } from '../platform/browser/router'

interface Props {
  markets: RecentMarket[]
  onRemove: (market: RecentMarket) => void
  onClear: () => void
}

function formatWhen(value: string): string {
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return 'Recently'

  return new Intl.DateTimeFormat(undefined, {
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  }).format(date)
}

export function RecentMarkets({ markets, onRemove, onClear }: Props) {
  if (markets.length === 0) return null

  return (
    <section className="recent-markets" aria-labelledby="recent-markets-heading">
      <header className="recent-heading">
        <div>
          <span className="eyebrow">LOCAL HISTORY</span>
          <h2 id="recent-markets-heading">Recent Markets</h2>
          <p>Saved in this browser. Opening one regenerates it from the deterministic seed.</p>
        </div>
        <button className="text-button danger-text-button" type="button" onClick={onClear}>
          Clear history
        </button>
      </header>

      <div className="recent-list">
        {markets.map((market) => (
          <article
            className="recent-row"
            key={`${market.mode}:${market.seed}:${market.gmChoice}`}
          >
            <BrowserLink
              className="recent-open"
              to={buildMarketPath({
                seed: market.seed,
                mode: market.mode,
                gmChoice: market.gmChoice,
              })}
            >
              <div className="recent-seed">#{market.seed}</div>
              <div className="recent-description">
                <strong>{market.categoryNames.join(' / ') || 'Night Market'}</strong>
                <span>
                  {market.mode === 'expanded_2045' ? 'Expanded 2045' : 'Core RAW'}
                  {' · '}
                  {formatWhen(market.generatedAt)}
                </span>
              </div>
              <span className="recent-arrow" aria-hidden="true">→</span>
            </BrowserLink>

            <button
              className="icon-button"
              type="button"
              aria-label={`Remove Night Market ${market.seed} from recent markets`}
              title="Remove from history"
              onClick={() => onRemove(market)}
            >
              ×
            </button>
          </article>
        ))}
      </div>
    </section>
  )
}
