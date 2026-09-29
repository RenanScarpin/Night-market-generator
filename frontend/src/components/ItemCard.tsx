import { useState } from 'react'
import type { MarketItem, StockSlot } from '../types/api'
import { compactSource } from '../utils/format'
import { ItemDetails } from './ItemDetails'
import { PriceBadge } from './PriceBadge'

interface Props {
  slot: StockSlot
}

function SupplementalItem({ item }: { item: MarketItem }) {
  return (
    <div className="supplemental-item">
      <span className="supplemental-plus">+</span>
      <div>
        <strong>{item.name}</strong>
        <div className="supplemental-meta">
          {item.prices[0] ?? 'Price not listed'} · Required foundational cyberware
        </div>
      </div>
    </div>
  )
}

export function ItemCard({ slot }: Props) {
  const [expanded, setExpanded] = useState(false)
  const item = slot.selected_item

  if (!item) {
    const unresolvedGmChoice = slot.resolution_mode === 'gm_choice'
    return (
      <article className={`market-card raw-card ${unresolvedGmChoice ? 'gm-card' : ''}`}>
        <div className="card-topline">
          <span className="mini-badge">{unresolvedGmChoice ? 'GM CHOICE' : 'RAW'}</span>
          <span className="roll-chip">d100 {slot.d100_roll}</span>
        </div>
        <h3>{slot.raw_result}</h3>
        {slot.raw_cost && <PriceBadge price={slot.raw_cost} />}
        <p className="card-note">
          {unresolvedGmChoice
            ? 'This slot was intentionally left for the GM to resolve.'
            : 'Generic Core RAW stock result.'}
        </p>
      </article>
    )
  }

  return (
    <article className="market-card item-card">
      <div className="card-topline">
        <span className="mini-badge expanded-badge">EXPANDED</span>
        <span className="roll-chip">d100 {slot.d100_roll}</span>
      </div>

      <div className="item-heading-row">
        <div>
          <h3>{item.name}</h3>
          {item.manufacturers.length > 0 && (
            <p className="manufacturer-line">{item.manufacturers.join(' · ')}</p>
          )}
        </div>
        {item.prices[0] && <PriceBadge price={item.prices[0]} />}
      </div>

      <p className="item-info">{item.info}</p>

      <div className="raw-origin">
        <span>Rolled from</span>
        <strong>{slot.raw_result}</strong>
      </div>

      {slot.supplemental_items.length > 0 && (
        <div className="supplemental-block">
          <div className="supplemental-label">Also available by RAW prerequisite rule</div>
          {slot.supplemental_items.map((extra) => (
            <SupplementalItem key={extra.item_id} item={extra} />
          ))}
        </div>
      )}

      <div className="card-footer">
        <span className="source-line">
          {compactSource(item.primary_source, item.primary_page) ?? 'Source unavailable'}
        </span>
        <button
          className="text-button"
          type="button"
          onClick={() => setExpanded((current) => !current)}
          aria-expanded={expanded}
        >
          {expanded ? 'Hide details' : 'Show mechanics'}
        </button>
      </div>

      {expanded && <ItemDetails itemId={item.item_id} />}
    </article>
  )
}
