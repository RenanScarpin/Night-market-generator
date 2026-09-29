import { useState } from 'react'
import type { ItemSummary } from '../types/api'
import { titleCase } from '../utils/format'
import { ItemDetails } from './ItemDetails'
import { PriceBadge } from './PriceBadge'

interface Props {
  item: ItemSummary
}

function priceText(item: ItemSummary): string | null {
  const price = item.prices[0]
  if (!price) return null
  if (price.source_price_text) return price.source_price_text
  if (price.cost_eb !== null) {
    return `${price.cost_eb.toLocaleString()}eb${price.price_category ? ` (${price.price_category})` : ''}`
  }
  return price.price_category ? `(${price.price_category})` : null
}

export function CatalogueCard({ item }: Props) {
  const [expanded, setExpanded] = useState(false)
  const price = priceText(item)
  const primaryCategory = item.categories.find((category) => category.is_primary) ?? item.categories[0]

  return (
    <article className={`catalogue-card ${expanded ? 'catalogue-card-expanded' : ''}`}>
      <div className="catalogue-card-topline">
        <span className="catalogue-kind">{titleCase(item.item_kind)}</span>
        <span className="catalogue-id">#{item.item_id}</span>
      </div>

      <div className="catalogue-card-heading">
        <div>
          <h3>{item.canonical_name}</h3>
          {item.manufacturers.length > 0 && (
            <p className="manufacturer-line">{item.manufacturers.join(' · ')}</p>
          )}
        </div>
        {price && <PriceBadge price={price} />}
      </div>

      <p className="catalogue-info">{item.info}</p>

      <div className="catalogue-taxonomy">
        {primaryCategory && <span>{primaryCategory.name}</span>}
        {item.categories
          .filter((category) => category !== primaryCategory)
          .slice(0, 2)
          .map((category) => (
            <span key={category.slug}>{category.name}</span>
          ))}
      </div>

      <div className="catalogue-card-footer">
        <button
          className="text-button"
          type="button"
          onClick={() => setExpanded((value) => !value)}
          aria-expanded={expanded}
        >
          {expanded ? 'Hide details' : 'Inspect item'}
        </button>
      </div>

      {expanded && <ItemDetails itemId={item.item_id} />}
    </article>
  )
}
