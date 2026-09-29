import { useEffect, useRef, useState } from 'react'
import { ApiError, generateMarket, getMarket } from '../api/client'
import { MarketActions } from '../components/MarketActions'
import { MarketControls } from '../components/MarketControls'
import { MarketSection } from '../components/MarketSection'
import { ModeBadge } from '../components/ModeBadge'
import { RecentMarkets } from '../components/RecentMarkets'
import { copyText } from '../platform/browser/clipboard'
import { navigate } from '../platform/browser/router'
import {
  addRecentMarket,
  clearRecentMarkets,
  loadGeneratorSettings,
  loadRecentMarkets,
  removeRecentMarket,
  saveGeneratorSettings,
} from '../platform/browser/storage'
import type { GmChoiceBehavior, MarketMode, NightMarket } from '../types/api'
import type { RecentMarket } from '../types/history'
import { buildMarketPath, parseMarketSearch } from '../utils/marketUrl'

interface Props {
  locationSearch: string
}

const DEFAULT_ROUTE_MODE: MarketMode = 'expanded_2045'
const DEFAULT_ROUTE_GM_CHOICE: GmChoiceBehavior = 'random'

function errorMessage(err: unknown): string {
  return err instanceof ApiError ? err.message : 'The Night Market API could not be reached.'
}

export function GeneratorPage({ locationSearch }: Props) {
  const initialSettings = useRef(loadGeneratorSettings()).current
  const [mode, setMode] = useState<MarketMode>(initialSettings.mode)
  const [seed, setSeed] = useState('')
  const [gmChoice, setGmChoice] = useState<GmChoiceBehavior>(initialSettings.gmChoice)
  const [market, setMarket] = useState<NightMarket | null>(null)
  const [recentMarkets, setRecentMarkets] = useState<RecentMarket[]>(() => loadRecentMarkets())
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [copied, setCopied] = useState(false)
  const requestSerial = useRef(0)
  const lastLoadedRoute = useRef<string | null>(null)
  const copiedTimer = useRef<number | null>(null)

  useEffect(() => {
    saveGeneratorSettings({ mode, gmChoice })
  }, [mode, gmChoice])

  useEffect(() => {
    return () => {
      if (copiedTimer.current !== null) {
        window.clearTimeout(copiedTimer.current)
      }
    }
  }, [])

  useEffect(() => {
    const parsed = parseMarketSearch(locationSearch)

    if (parsed.error) {
      requestSerial.current += 1
      lastLoadedRoute.current = null
      setError(parsed.error)
      setMarket(null)
      return
    }

    if (parsed.seed === null) {
      requestSerial.current += 1
      lastLoadedRoute.current = null
      setMarket(null)
      setSeed('')
      if (parsed.mode) setMode(parsed.mode)
      if (parsed.gmChoice) setGmChoice(parsed.gmChoice)
      setError(null)
      return
    }

    const routeMode = parsed.mode ?? DEFAULT_ROUTE_MODE
    const routeChoice = parsed.gmChoice ?? DEFAULT_ROUTE_GM_CHOICE
    const routeKey = `${routeMode}:${parsed.seed}:${routeChoice}`

    setMode(routeMode)
    setSeed(String(parsed.seed))
    setGmChoice(routeChoice)

    if (lastLoadedRoute.current === routeKey) {
      return
    }
    lastLoadedRoute.current = routeKey

    void loadMarketFromSeed(parsed.seed, routeMode, routeChoice, true)
    // The load function is intentionally driven only by the URL state.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [locationSearch])

  function recordMarket(result: NightMarket) {
    const recent: RecentMarket = {
      seed: result.seed,
      mode: result.mode,
      gmChoice: result.gm_choice_behavior,
      categoryNames: result.sections.map((section) => section.category_name),
      generatedAt: new Date().toISOString(),
    }
    setRecentMarkets(addRecentMarket(recent))
  }

  function applyMarket(result: NightMarket, updateUrl: boolean, replaceUrl = false) {
    setMarket(result)
    setMode(result.mode)
    setSeed(String(result.seed))
    setGmChoice(result.gm_choice_behavior)
    setError(null)
    lastLoadedRoute.current = `${result.mode}:${result.seed}:${result.gm_choice_behavior}`
    recordMarket(result)

    if (updateUrl) {
      navigate(
        buildMarketPath({
          seed: result.seed,
          mode: result.mode,
          gmChoice: result.gm_choice_behavior,
        }),
        { replace: replaceUrl },
      )
    }
  }

  async function loadMarketFromSeed(
    numericSeed: number,
    requestedMode: MarketMode,
    requestedChoice: GmChoiceBehavior,
    canonicalizeUrl = false,
  ) {
    const serial = ++requestSerial.current
    setLoading(true)
    setError(null)

    try {
      const result = await getMarket(numericSeed, requestedMode, requestedChoice)
      if (serial !== requestSerial.current) return
      applyMarket(result, canonicalizeUrl, true)
    } catch (err: unknown) {
      if (serial !== requestSerial.current) return
      lastLoadedRoute.current = null
      setError(errorMessage(err))
      setMarket(null)
    } finally {
      if (serial === requestSerial.current) setLoading(false)
    }
  }

  async function generate(payloadSeed: number | null, replaceUrl = false) {
    const serial = ++requestSerial.current
    setLoading(true)
    setError(null)

    try {
      const result = await generateMarket({
        mode,
        seed: payloadSeed,
        gm_choice: gmChoice,
      })
      if (serial !== requestSerial.current) return
      applyMarket(result, true, replaceUrl)
    } catch (err: unknown) {
      if (serial !== requestSerial.current) return
      setError(errorMessage(err))
    } finally {
      if (serial === requestSerial.current) setLoading(false)
    }
  }

  async function handleGenerate() {
    const numericSeed = seed.trim() ? Number(seed) : null
    if (numericSeed !== null && (!Number.isSafeInteger(numericSeed) || numericSeed < 0)) {
      setError('Seed must be a non-negative safe integer.')
      return
    }
    await generate(numericSeed)
  }

  async function handleRegenerate() {
    if (!market) return
    await loadMarketFromSeed(market.seed, market.mode, market.gm_choice_behavior)
  }

  async function handleNewRandom() {
    setSeed('')
    await generate(null)
  }

  async function handleCopyLink() {
    if (!market) return

    const path = buildMarketPath({
      seed: market.seed,
      mode: market.mode,
      gmChoice: market.gm_choice_behavior,
    })

    try {
      await copyText(new URL(path, window.location.origin).toString())
      setCopied(true)
      if (copiedTimer.current !== null) window.clearTimeout(copiedTimer.current)
      copiedTimer.current = window.setTimeout(() => setCopied(false), 1800)
    } catch {
      setError('Could not copy the market link to the clipboard.')
    }
  }

  function handleRemoveRecent(recent: RecentMarket) {
    setRecentMarkets(removeRecentMarket(recent))
  }

  function handleClearRecents() {
    setRecentMarkets(clearRecentMarkets())
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

      <RecentMarkets
        markets={recentMarkets}
        onRemove={handleRemoveRecent}
        onClear={handleClearRecents}
      />

      {error && (
        <div className="error-banner" role="alert">
          <strong>Could not load market.</strong>
          <span>{error}</span>
          <span className="error-hint">Is FastAPI running on port 8000?</span>
        </div>
      )}

      {!market && loading && (
        <section className="empty-market loading-market" aria-live="polite">
          <div className="empty-crosshair loading-crosshair" aria-hidden="true">↻</div>
          <h2>Contacting the Fixer…</h2>
          <p>Reconstructing the market from its seed.</p>
        </section>
      )}

      {!market && !loading && !error && (
        <section className="empty-market">
          <div className="empty-crosshair" aria-hidden="true">+</div>
          <h2>No market generated yet.</h2>
          <p>Choose a mode above and put something on the shelves.</p>
        </section>
      )}

      {market && (
        <section className={`market-output ${loading ? 'market-output-loading' : ''}`} aria-live="polite">
          <header className="market-output-header">
            <div>
              <div className="market-id-line">
                <span>NIGHT MARKET</span>
                <strong>#{market.seed}</strong>
              </div>
              <h2>{market.sections.map((section) => section.category_name).join(' / ')}</h2>
            </div>
            <div className="market-header-side">
              <div className="market-meta">
                <ModeBadge mode={market.mode} />
                <span className="version-chip">GEN {market.generator_version}</span>
              </div>
              <MarketActions
                loading={loading}
                copied={copied}
                onRegenerate={handleRegenerate}
                onNewRandom={handleNewRandom}
                onCopyLink={handleCopyLink}
              />
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
