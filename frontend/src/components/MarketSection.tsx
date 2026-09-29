import type { MarketSection as MarketSectionType } from '../types/api'
import { ItemCard } from './ItemCard'

interface Props {
  section: MarketSectionType
}

export function MarketSection({ section }: Props) {
  return (
    <section className="market-section">
      <header className="section-header">
        <div>
          <div className="section-kicker">CATEGORY ROLL {section.category_roll}</div>
          <h2>{section.category_name}</h2>
          <p>{section.description}</p>
        </div>
        <div className="stock-count">
          <strong>{section.stock_count_roll}</strong>
          <span>{section.stock_count_roll === 1 ? 'stock type' : 'stock types'}</span>
        </div>
      </header>

      <div className="cards-grid">
        {section.slots.map((slot) => (
          <ItemCard key={slot.stock_roll_id} slot={slot} />
        ))}
      </div>
    </section>
  )
}
