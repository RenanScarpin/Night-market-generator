interface Props {
  loading: boolean
  copied: boolean
  onRegenerate: () => void
  onNewRandom: () => void
  onCopyLink: () => void
}

export function MarketActions({
  loading,
  copied,
  onRegenerate,
  onNewRandom,
  onCopyLink,
}: Props) {
  return (
    <div className="market-actions" aria-label="Market actions">
      <button className="action-button" type="button" disabled={loading} onClick={onRegenerate}>
        ↻ <span>Regenerate</span>
      </button>
      <button className="action-button" type="button" disabled={loading} onClick={onNewRandom}>
        ⚄ <span>New random</span>
      </button>
      <button className="action-button" type="button" onClick={onCopyLink}>
        ⧉ <span>{copied ? 'Link copied' : 'Copy link'}</span>
      </button>
    </div>
  )
}
