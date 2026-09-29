import { useEffect, useState } from 'react'
import { ApiError, getItemDetail } from '../api/client'
import type { ItemDetail } from '../types/api'
import { titleCase } from '../utils/format'
import { MechanicsView } from './MechanicsView'
import { PriceBadge } from './PriceBadge'

interface Props {
  itemId: number
}

export function ItemDetails({ itemId }: Props) {
  const [detail, setDetail] = useState<ItemDetail | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    let active = true
    setLoading(true)
    setError(null)

    getItemDetail(itemId)
      .then((data) => {
        if (active) setDetail(data)
      })
      .catch((err: unknown) => {
        if (!active) return
        setError(err instanceof ApiError ? err.message : 'Could not load item details.')
      })
      .finally(() => {
        if (active) setLoading(false)
      })

    return () => {
      active = false
    }
  }, [itemId])

  if (loading) return <div className="detail-state">Loading source mechanics…</div>
  if (error) return <div className="detail-state error-text">{error}</div>
  if (!detail) return null

  const relationships = detail.relationships

  return (
    <div className="item-details-panel">
      <div className="detail-section">
        <h4>Mechanics</h4>
        {detail.mechanics ? (
          <MechanicsView value={detail.mechanics} />
        ) : (
          <p className="muted">No structured mechanics recorded.</p>
        )}
      </div>

      {detail.prices.length > 1 && (
        <div className="detail-section">
          <h4>Price variants</h4>
          <div className="price-row">
            {detail.prices.map((price) => (
              <PriceBadge
                key={price.item_price_id}
                price={price.source_price_text ?? `${price.cost_eb ?? '—'}eb`}
              />
            ))}
          </div>
        </div>
      )}

      {relationships.length > 0 && (
        <div className="detail-section">
          <h4>Relationships</h4>
          <ul className="relationship-list">
            {relationships.map((relationship) => (
              <li key={`${relationship.relation_type}-${relationship.target_item_id}`}>
                <span className="relationship-type">{titleCase(relationship.relation_type)}</span>
                <strong>{relationship.target_name}</strong>
                {relationship.notes && <span className="muted"> — {relationship.notes}</span>}
              </li>
            ))}
          </ul>
        </div>
      )}

      <div className="detail-section detail-meta-grid">
        <div>
          <h4>Categories</h4>
          <p>{detail.categories.map((category) => category.name).join(' · ') || '—'}</p>
        </div>
      </div>
    </div>
  )
}
