import type { MarketMode } from '../types/api'

interface Props {
  mode: MarketMode
}

export function ModeBadge({ mode }: Props) {
  const expanded = mode === 'expanded_2045'
  return (
    <span className={`mode-badge ${expanded ? 'mode-expanded' : 'mode-raw'}`}>
      {expanded ? 'EXPANDED 2045' : 'CORE RAW'}
    </span>
  )
}
