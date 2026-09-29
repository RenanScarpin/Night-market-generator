import { useState } from 'react'
import type { NightMarket } from '../types/api'
import { copyText } from '../platform/browser/clipboard'
import { downloadFile, marketToMarkdown, marketToText } from '../utils/marketExport'

export function ExportActions({ market }: { market: NightMarket }) {
  const [copied, setCopied] = useState(false)

  async function copyMarket() {
    await copyText(marketToText(market))
    setCopied(true)
    window.setTimeout(() => setCopied(false), 1500)
  }

  return <div className="export-actions">
    <button className="action-button" onClick={copyMarket}>⧉ {copied ? 'Copied' : 'Copy Market'}</button>
    <button className="action-button" onClick={() => downloadFile(`night-market-${market.seed}.md`, marketToMarkdown(market), 'text/markdown')}>↓ Markdown</button>
    <button className="action-button" onClick={() => window.print()}>🖨 Print</button>
  </div>
}
