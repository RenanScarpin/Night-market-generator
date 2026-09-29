import { useState } from 'react'
import { ApiError, generateMarket } from '../api/client'
import { MarketControls } from '../components/MarketControls'
import { MarketSection } from '../components/MarketSection'
import { ModeBadge } from '../components/ModeBadge'
import type { GmChoiceBehavior, MarketMode, NightMarket } from '../types/api'

export function GeneratorPage() {
  const [mode, setMode] = useState<MarketMode>('expanded_2045')
  const [seed, setSeed] = useState('')
  const [gmChoice, setGmChoice] = useState<GmChoiceBehavior>('random')
  const [market, setMarket] = useState<NightMarket | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  async function handleGenerate() {
    setLoading(true)
    setError(null)

    try {
      const numericSeed = seed.trim() ? Number(seed) : null
      if (numericSeed !== null && (!Number.isSafeInteger(numericSeed) || numericSeed < 0)) {
        setError('Seed must be a non-negative safe integer.')
        return
      }
      const result = await generateMarket({
        mode,
        seed: numericSeed,
        gm_choice: gmChoice,
      })
      setMarket(result)
      setSeed(String(result.seed))
    } catch (err: unknown) {
      setError(err instanceof ApiError ? err.message : 'The Night Market API could not be reached.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <main className="page-shell">
      <MarketControls
        mode={mode}
        seed={seed}
        gmChoice={gmChoice}
        loading={loading}
        onModeChange={setMode}
        onSeedChange={setSeed}
        onGmChoiceChange={setGmChoice}
        onSubmit={handleGenerate}
      />

      {error && (
        <div className="error-banner" role="alert">
          <strong>Could not generate market.</strong>
          <span>{error}</span>
          <span className="error-hint">Is FastAPI running on port 8000?</span>
        </div>
      )}

      {!market && !loading && !error && (
        <section className="empty-market">
          <div className="empty-crosshair" aria-hidden="true">+</div>
          <h2>No market generated yet.</h2>
          <p>Choose a mode above and put something on the shelves.</p>
        </section>
      )}

      {market && (
        <section className="market-output" aria-live="polite">
          <header className="market-output-header">
            <div>
              <div className="market-id-line">
                <span>NIGHT MARKET</span>
                <strong>#{market.seed}</strong>
              </div>
              <h2>{market.sections.map((section) => section.category_name).join(' / ')}</h2>
            </div>
            <div className="market-meta">
              <ModeBadge mode={market.mode} />
              <span className="version-chip">GEN {market.generator_version}</span>
            </div>
          </header>

          {market.mode === 'expanded_2045' && (
            <div className="mode-explainer">
              <strong>Expanded mode:</strong> the Core Night Market rolls are preserved, then compatible
              canon-2045 items are selected from the unified catalogue.
            </div>
          )}

          {market.mode === 'core_raw' && (
            <div className="mode-explainer raw-explainer">
              <strong>Core RAW mode:</strong> entries below reproduce the Night Market table results without
              resolving them into supplement-specific items.
            </div>
          )}

          <div className="market-sections">
            {market.sections.map((section) => (
              <MarketSection key={section.category_code} section={section} />
            ))}
          </div>
        </section>
      )}
    </main>
  )
}
