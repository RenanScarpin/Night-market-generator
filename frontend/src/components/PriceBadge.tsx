import { priceAmountFromText, priceCategoryFromText } from '../utils/format'

interface Props {
  price: string
}

export function PriceBadge({ price }: Props) {
  const category = priceCategoryFromText(price)
  return (
    <span className="price-badge">
      <strong>{priceAmountFromText(price)}</strong>
      {category && <span>{category}</span>}
    </span>
  )
}
