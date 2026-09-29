import type { ChangeEvent, FormEvent } from 'react'
import type { GmChoiceBehavior, MarketMode } from '../types/api'

interface Props {
  mode: MarketMode
  seed: string
  gmChoice: GmChoiceBehavior
  loading: boolean
  onModeChange: (mode: MarketMode) => void
  onSeedChange: (seed: string) => void
  onGmChoiceChange: (choice: GmChoiceBehavior) => void
  onSubmit: () => void
}

export function MarketControls({
  mode,
  seed,
  gmChoice,
  loading,
  onModeChange,
  onSeedChange,
  onGmChoiceChange,
  onSubmit,
}: Props) {
  function handleSubmit(event: FormEvent) {
    event.preventDefault()
    onSubmit()
  }

  return (
    <form className="control-panel" onSubmit={handleSubmit}>
      <div className="control-panel-heading">
        <span className="eyebrow">MARKET CONFIGURATION</span>
        <h1>Generate a Night Market</h1>
        <p>
          Roll the Core table exactly, or resolve those same rolls against the full canon-2045 catalogue.
        </p>
      </div>

      <div className="control-grid">
        <label className="field">
          <span>Mode</span>
          <select
            value={mode}
            onChange={(event: ChangeEvent<HTMLSelectElement>) => onModeChange(event.target.value as MarketMode)}
          >
            <option value="expanded_2045">Expanded 2045</option>
            <option value="core_raw">Core RAW</option>
          </select>
          <small>
            {mode === 'expanded_2045'
              ? 'Concrete canon items are resolved from RAW stock slots.'
              : 'Shows the Core Rulebook table results without expanded item resolution.'}
          </small>
        </label>

        <label className="field">
          <span>Seed</span>
          <div className="seed-row">
            <input
              inputMode="numeric"
              pattern="[0-9]*"
              placeholder="Random"
              value={seed}
              onChange={(event: ChangeEvent<HTMLInputElement>) => onSeedChange(event.target.value.replace(/[^0-9]/g, ''))}
            />
            <button className="secondary-button" type="button" onClick={() => onSeedChange('')}>
              Random
            </button>
          </div>
          <small>Leave blank for a new random market. Reuse a seed to reproduce it.</small>
        </label>

        <label className={`field ${mode === 'core_raw' ? 'field-disabled' : ''}`}>
          <span>GM-choice slots</span>
          <select
            value={gmChoice}
            disabled={mode === 'core_raw'}
            onChange={(event: ChangeEvent<HTMLSelectElement>) => onGmChoiceChange(event.target.value as GmChoiceBehavior)}
          >
            <option value="random">Resolve randomly</option>
            <option value="leave">Leave unresolved</option>
          </select>
          <small>
            {mode === 'core_raw'
              ? 'Not applicable in RAW display mode.'
              : 'Interactive GM selection will be added in the next GUI iteration.'}
          </small>
        </label>
      </div>

      <button className="generate-button" type="submit" disabled={loading}>
        <span>{loading ? 'GENERATING…' : 'GENERATE MARKET'}</span>
        <span aria-hidden="true">→</span>
      </button>
    </form>
  )
}
