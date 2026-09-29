import type { NightMarket, StockSlot } from '../types/api'

function itemText(slot: StockSlot): string {
  if (slot.selected_item) {
    const item = slot.selected_item
    return `${item.name}\n${item.prices.join(' / ') || 'Price unavailable'}\n${item.info || ''}`
  }
  return `${slot.raw_result}\n${slot.raw_cost ?? ''}`
}

export function marketToText(market: NightMarket): string {
  const lines: string[] = []
  lines.push('CYBERPUNK RED NIGHT MARKET')
  lines.push(`Seed: ${market.seed}`)
  lines.push(`Mode: ${market.mode === 'expanded_2045' ? 'Expanded 2045' : 'Core RAW'}`)
  lines.push('')

  for (const section of market.sections) {
    lines.push('='.repeat(40))
    lines.push(section.category_name.toUpperCase())
    lines.push('')
    for (const slot of section.slots) {
      lines.push('• ' + itemText(slot))
      lines.push('')
    }
  }
  return lines.join('\n')
}

export function marketToMarkdown(market: NightMarket): string {
  const lines = [
    '# Cyberpunk RED Night Market',
    '',
    `**Seed:** ${market.seed}`,
    `**Mode:** ${market.mode === 'expanded_2045' ? 'Expanded 2045' : 'Core RAW'}`,
    '',
  ]

  for (const section of market.sections) {
    lines.push(`## ${section.category_name}`)
    lines.push('')
    for (const slot of section.slots) {
      if (slot.selected_item) {
        lines.push(`### ${slot.selected_item.name}`)
        lines.push('')
        lines.push(slot.selected_item.info || '')
      } else {
        lines.push(`### ${slot.raw_result}`)
      }
      if (slot.raw_cost) lines.push(`\nCost: ${slot.raw_cost}`)
      lines.push('')
    }
  }

  return lines.join('\n')
}

export function downloadFile(filename: string, content: string, mime: string) {
  const blob = new Blob([content], { type: mime })
  const url = URL.createObjectURL(blob)
  const anchor = document.createElement('a')
  anchor.href = url
  anchor.download = filename
  anchor.click()
  URL.revokeObjectURL(url)
}
